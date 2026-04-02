"""Chat router that maps user messages to the appropriate squad using keyword matching."""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# Keyword mapping: squad_code -> list of keywords (lowercase, no accents)
_SQUAD_KEYWORDS: dict[str, list[str]] = {
    "fabrica-de-conteudo": [
        "conteudo",
        "calendario",
        "editorial",
        "copy",
        "stories",
        "reels",
        "carrossel",
        "carrosseis",
        "legenda",
        "post",
        "posts",
        "roteiro",
        "gancho",
        "fabrica",
    ],
    "diagnostico-perfil": [
        "metrica",
        "metricas",
        "diagnostico",
        "concorrente",
        "concorrentes",
        "perfil",
        "analise",
        "analisar",
        "instagram",
        "tiktok",
        "engajamento",
        "relatorio",
    ],
    "maquina-clientes": [
        "preco",
        "precificar",
        "precificacao",
        "cobrar",
        "proposta",
        "contrato",
        "clausula",
        "juridico",
        "onboarding",
        "boas vindas",
        "boas-vindas",
        "manual",
        "cliente",
        "clientes",
        "maquina",
    ],
}


def _normalize(text: str) -> str:
    """Lowercase and strip accents from text for comparison."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


class ChatRouter:
    """Routes user messages to the appropriate squad using keyword matching with optional Claude API fallback."""

    def __init__(self, available_squads: list[dict]) -> None:  # type: ignore[type-arg]
        """Initialize with list of available squad dicts (code, name, description)."""
        self.available_squads = available_squads
        self._squad_codes = {squad["code"] for squad in available_squads}

    def match_by_keywords(self, message: str) -> str | None:
        """Fast local matching by keywords.

        First checks for a direct squad code match in the message.
        Then scores the message against each squad's keywords and returns
        the squad code with the highest score, or None if no keywords match.
        """
        normalized = _normalize(message)

        # Direct squad code match
        for code in self._squad_codes:
            if code in normalized:
                return code

        # Keyword scoring
        scores: dict[str, int] = {}
        for squad_code, keywords in _SQUAD_KEYWORDS.items():
            if squad_code not in self._squad_codes:
                continue
            score = 0
            for kw in keywords:
                # Multi-word keywords need phrase match; single words use word boundary check
                if " " in kw or "-" in kw:
                    if kw in normalized:
                        score += 1
                else:
                    # Word boundary check to avoid "post" matching in "proposta"
                    if re.search(r'\b' + re.escape(kw) + r'\b', normalized):
                        score += 1
            if score > 0:
                scores[squad_code] = score

        if not scores:
            return None

        return max(scores, key=lambda k: scores[k])

    async def route(self, message: str, api_key: str | None = None) -> dict:  # type: ignore[type-arg]
        """Route a message to the appropriate squad.

        Tries keyword matching first. Falls back to Claude API if api_key is provided
        and keyword matching is inconclusive (returns None).

        Returns a dict with:
          - squad_code: str | None
          - confidence: "high" | "medium" | "low"
          - explanation: str
        """
        squad_code = self.match_by_keywords(message)

        if squad_code is not None:
            return {
                "squad_code": squad_code,
                "confidence": "high",
                "explanation": f"Matched squad '{squad_code}' via keyword scoring.",
            }

        # Try Claude API fallback for ambiguous messages
        if api_key:
            try:
                result = await self._route_via_claude(message, api_key)
                return result
            except Exception as e:
                logger.warning(f"Claude API routing failed, returning no match: {e}")

        return {
            "squad_code": None,
            "confidence": "low",
            "explanation": "No keyword match found and no API fallback available.",
        }

    async def _route_via_claude(self, message: str, api_key: str) -> dict:  # type: ignore[type-arg]
        """Use Claude to detect the squad for ambiguous messages.

        Sends a system prompt listing all available squads and asks the model
        to respond with just the squad code or "none".
        """
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=api_key)

        squads_description = "\n".join(
            f"- {s['code']}: {s.get('name', '')} — {s.get('description', '')}"
            for s in self.available_squads
        )

        system_prompt = (
            "You are a message router. Given a user message, identify which squad should handle it.\n"
            f"Available squads:\n{squads_description}\n\n"
            "Reply with ONLY the squad code (e.g. 'fabrica-de-conteudo') or 'none' if no squad matches. "
            "Do not include any other text."
        )

        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            system=system_prompt,
            messages=[{"role": "user", "content": message}],
        )

        content = response.content
        detected: str | None = None
        if content and len(content) > 0:
            first_block = content[0]
            if hasattr(first_block, "text"):
                raw = str(first_block.text).strip().lower()
                if raw != "none" and raw in self._squad_codes:
                    detected = raw

        if detected:
            return {
                "squad_code": detected,
                "confidence": "medium",
                "explanation": f"Matched squad '{detected}' via Claude API.",
            }

        return {
            "squad_code": None,
            "confidence": "low",
            "explanation": "Claude API could not determine a matching squad.",
        }
