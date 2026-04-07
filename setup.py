#!/usr/bin/env python3
"""SocialForge Auto-Installer — roda em Windows, Mac e Linux.

Uso:
    python setup.py          # Instala tudo
    python setup.py --check  # Só verifica pré-requisitos
    python setup.py --start  # Inicia backend + frontend
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
HOOKS = ROOT / "hooks"

IS_WINDOWS = platform.system() == "Windows"

GREEN = "" if IS_WINDOWS else "\033[92m"
RED = "" if IS_WINDOWS else "\033[91m"
YELLOW = "" if IS_WINDOWS else "\033[93m"
BOLD = "" if IS_WINDOWS else "\033[1m"
RESET = "" if IS_WINDOWS else "\033[0m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}✗{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}!{RESET} {msg}")


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command, printing it first."""
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def check_command(name: str, version_flag: str = "--version") -> str | None:
    """Check if a command exists and return its version."""
    path = shutil.which(name)
    if not path:
        return None
    try:
        result = run([path, version_flag], check=False)
        output = result.stdout.strip() or result.stderr.strip()
        return output.split("\n")[0]
    except Exception:
        return "installed"


# ── Phase 1: Check prerequisites ──────────────────────────────────

def check_prerequisites() -> bool:
    print(f"\n{BOLD}=== Verificando pré-requisitos ==={RESET}\n")
    all_ok = True

    # Python 3.13+
    py_ver = check_command("python3") or check_command("python")
    if py_ver:
        ok(f"Python: {py_ver}")
    else:
        fail("Python não encontrado")
        all_ok = False

    # Node.js 20+
    node_ver = check_command("node")
    if node_ver:
        ok(f"Node.js: {node_ver}")
    else:
        fail("Node.js não encontrado (precisa 20+)")
        all_ok = False

    # uv
    uv_ver = check_command("uv")
    if uv_ver:
        ok(f"uv: {uv_ver}")
    else:
        fail("uv não encontrado — instale com: curl -LsSf https://astral.sh/uv/install.sh | sh")
        all_ok = False

    # Git
    git_ver = check_command("git")
    if git_ver:
        ok(f"Git: {git_ver}")
    else:
        fail("Git não encontrado")
        all_ok = False

    # npm or bun
    bun_ver = check_command("bun")
    npm_ver = check_command("npm")
    if bun_ver:
        ok(f"Bun: {bun_ver}")
    elif npm_ver:
        ok(f"npm: {npm_ver}")
    else:
        fail("npm ou bun não encontrado")
        all_ok = False

    # tmux (optional)
    tmux_ver = check_command("tmux", "-V")
    if tmux_ver:
        ok(f"tmux: {tmux_ver} (opcional)")
    else:
        warn("tmux não encontrado (opcional — use terminais separados)")

    # Claude Code
    claude_ver = check_command("claude")
    if claude_ver:
        ok(f"Claude Code: {claude_ver}")
    else:
        warn("Claude Code CLI não encontrado no PATH (ok se usar Desktop)")

    return all_ok


# ── Phase 2: Install dependencies ─────────────────────────────────

def install_python_313() -> bool:
    """Ensure Python 3.13 is available via uv."""
    print(f"\n{BOLD}=== Instalando Python 3.13 (via uv) ==={RESET}\n")
    try:
        result = run(["uv", "python", "install", "3.13"], check=False)
        if result.returncode == 0:
            ok("Python 3.13 instalado/disponível")
            return True
        else:
            warn(f"Aviso: {result.stderr.strip()}")
            return True  # May already be installed
    except Exception as e:
        fail(f"Erro ao instalar Python 3.13: {e}")
        return False


def install_backend() -> bool:
    print(f"\n{BOLD}=== Instalando backend ==={RESET}\n")
    try:
        result = run(["uv", "sync", "-p", "3.13"], cwd=BACKEND, check=False)
        if result.returncode == 0:
            ok("Dependências do backend instaladas")
            return True
        else:
            fail(f"Erro no backend: {result.stderr.strip()[:200]}")
            return False
    except Exception as e:
        fail(f"Erro: {e}")
        return False


def install_frontend() -> bool:
    print(f"\n{BOLD}=== Instalando frontend ==={RESET}\n")
    pkg = "bun" if shutil.which("bun") else "npm"
    try:
        result = run([pkg, "install"], cwd=FRONTEND, check=False)
        if result.returncode == 0:
            ok(f"Dependências do frontend instaladas ({pkg})")
            return True
        else:
            fail(f"Erro no frontend: {result.stderr.strip()[:200]}")
            return False
    except Exception as e:
        fail(f"Erro: {e}")
        return False


def install_hooks() -> bool:
    print(f"\n{BOLD}=== Instalando hooks ==={RESET}\n")
    try:
        # Install hooks Python package
        result = run(["uv", "sync", "-p", "3.13"], cwd=HOOKS, check=False)
        if result.returncode != 0:
            warn(f"uv sync hooks: {result.stderr.strip()[:200]}")

        # Run install script
        if IS_WINDOWS:
            # On Windows, use the manage_hooks.py directly
            manage_script = HOOKS / "manage_hooks.py"
            if manage_script.exists():
                # Install the tool first
                run(["uv", "tool", "install", "--force", "-p", "3.13", "."], cwd=HOOKS, check=False)
                result = run(
                    ["uv", "run", "-p", "3.13", str(manage_script), "install",
                     "--hook-cmd", "claude-office-hook"],
                    cwd=HOOKS, check=False
                )
                if result.returncode == 0:
                    ok("Hooks instalados")
                    return True
                else:
                    warn(f"Hooks: {result.stderr.strip()[:200]}")
                    return False
        else:
            install_sh = HOOKS / "install.sh"
            if install_sh.exists():
                os.chmod(install_sh, 0o755)
                result = run(["bash", str(install_sh)], cwd=HOOKS, check=False)
                if result.returncode == 0:
                    ok("Hooks instalados")
                    return True
                else:
                    warn(f"Hooks: {result.stderr.strip()[:200]}")
                    return False

        warn("Script de instalação de hooks não encontrado")
        return False
    except Exception as e:
        fail(f"Erro: {e}")
        return False


def create_env() -> bool:
    """Create .env file for backend."""
    env_path = BACKEND / ".env"
    if not env_path.exists():
        env_path.write_text("SUMMARY_ENABLED=false\n", encoding="utf-8")
        ok(".env criado (SUMMARY_ENABLED=false)")
    else:
        ok(".env já existe")
    return True


def build_static() -> bool:
    """Build frontend and copy to backend/static."""
    print(f"\n{BOLD}=== Build estático do frontend ==={RESET}\n")
    pkg = "bun" if shutil.which("bun") else "npm"
    try:
        # Build
        result = run([pkg, "run", "build"], cwd=FRONTEND, check=False)
        if result.returncode != 0:
            fail(f"Build falhou: {result.stderr.strip()[:200]}")
            return False

        # Copy output to backend/static
        out_dir = FRONTEND / "out"
        static_dir = BACKEND / "static"

        if static_dir.exists():
            shutil.rmtree(static_dir)

        if out_dir.exists():
            shutil.copytree(out_dir, static_dir)
            ok("Frontend compilado e copiado para backend/static")
            return True
        else:
            fail("Diretório 'out' não encontrado após build")
            return False
    except Exception as e:
        fail(f"Erro: {e}")
        return False


# ── Phase 3: Start servers ─────────────────────────────────────────

def start_servers() -> None:
    print(f"\n{BOLD}=== Iniciando servidores ==={RESET}\n")

    has_tmux = shutil.which("tmux")
    if has_tmux and not IS_WINDOWS:
        print("Usando tmux...")
        subprocess.run(
            ["tmux", "kill-session", "-t", "socialforge"],
            capture_output=True, check=False
        )
        subprocess.run([
            "tmux", "new-session", "-d", "-s", "socialforge", "-n", "backend",
        ], check=False)
        subprocess.run([
            "tmux", "send-keys", "-t", "socialforge:backend",
            f"cd {BACKEND} && uv run -p 3.13 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
            "Enter"
        ], check=False)
        subprocess.run([
            "tmux", "new-window", "-t", "socialforge", "-n", "frontend",
        ], check=False)
        subprocess.run([
            "tmux", "send-keys", "-t", "socialforge:frontend",
            f"cd {FRONTEND} && npm run dev", "Enter"
        ], check=False)
        ok("Servidores iniciados em tmux session 'socialforge'")
        print(f"\n  Backend:  http://localhost:8000")
        print(f"  Frontend: http://localhost:3333")
        print(f"\n  Anexar: tmux attach -t socialforge")
    else:
        print("Sem tmux — inicie manualmente em 2 terminais:\n")
        print(f"  Terminal 1: cd {BACKEND} && uv run -p 3.13 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print(f"  Terminal 2: cd {FRONTEND} && npm run dev")
        print(f"\n  Ou acesse só via backend: http://localhost:8000 (com build estático)")


# ── Main ───────────────────────────────────────────────────────────

def main() -> None:
    print(f"""
{BOLD}╔══════════════════════════════════════════╗
║        SOCIALFORGE — AUTO INSTALLER       ║
║   100% Local · Sem API Key · 11 Agentes   ║
╚══════════════════════════════════════════╝{RESET}
""")

    if "--check" in sys.argv:
        check_prerequisites()
        return

    if "--start" in sys.argv:
        start_servers()
        return

    # Full install
    if not check_prerequisites():
        print(f"\n{RED}Instale os pré-requisitos faltantes e rode novamente.{RESET}")
        sys.exit(1)

    results = {}
    results["python_313"] = install_python_313()
    results["backend"] = install_backend()
    results["frontend"] = install_frontend()
    results["env"] = create_env()
    results["hooks"] = install_hooks()
    results["static"] = build_static()

    # Report
    print(f"""
{BOLD}============================================
  SOCIALFORGE — RELATÓRIO DE INSTALAÇÃO
============================================{RESET}

  {"✅" if results["python_313"] else "❌"} Python 3.13
  {"✅" if results["backend"] else "❌"} Backend (FastAPI)
  {"✅" if results["frontend"] else "❌"} Frontend (Next.js + PixiJS)
  {"✅" if results["env"] else "❌"} .env configurado
  {"✅" if results["hooks"] else "❌"} Hooks do Claude Code
  {"✅" if results["static"] else "❌"} Build estático

{BOLD}============================================{RESET}
""")

    all_ok = all(results.values())
    if all_ok:
        print(f"{GREEN}Instalação completa!{RESET}\n")
        print("Para iniciar:")
        print(f"  python setup.py --start")
        print(f"  # ou: make dev-tmux")
        print(f"\nDepois abra http://localhost:8000 no navegador.")
        print(f"No Claude Code Desktop, peça qualquer coisa sobre social media!")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"{RED}Algumas etapas falharam: {', '.join(failed)}{RESET}")
        print("Verifique os erros acima e rode novamente.")


if __name__ == "__main__":
    main()
