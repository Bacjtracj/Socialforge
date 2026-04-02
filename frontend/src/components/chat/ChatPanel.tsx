"use client";

import { useEffect, useRef, useCallback } from "react";
import { useChatStore } from "@/stores/chatStore";
import { useSquadStore } from "@/stores/squadStore";
import type { SquadSummary } from "@/types/squads";
import { ChatInput } from "./ChatInput";
import { ChatMessage } from "./ChatMessage";
import { CheckpointMessage } from "./CheckpointMessage";
import { QueueIndicator } from "./QueueIndicator";
import { SquadCard } from "./SquadCard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

// ============================================================================
// HELPERS
// ============================================================================

function makeId() {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function ChatPanel() {
  const { messages, isLoading, addMessage, setLoading } = useChatStore();
  const { squads, pipelineState, queue, setSquads, setQueue } = useSquadStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasFetched = useRef(false);

  // Load squads on mount
  useEffect(() => {
    if (hasFetched.current) return;
    hasFetched.current = true;

    fetch(`${API_BASE}/api/v1/squads`)
      .then((res) => res.json())
      .then((data: SquadSummary[]) => setSquads(data))
      .catch(() => {
        // Silently ignore fetch errors (backend may not be running)
      });
  }, [setSquads]);

  // Auto-scroll when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Send a message to the chat endpoint
  const handleSend = useCallback(
    async (text: string) => {
      addMessage({ id: makeId(), role: "user", text, timestamp: Date.now() });
      setLoading(true);

      try {
        const res = await fetch(`${API_BASE}/api/v1/squads/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
        });
        const data = await res.json();

        // Show explanation from router
        if (data.explanation) {
          addMessage({
            id: makeId(),
            role: "agent",
            text: data.explanation,
            agentName: "SocialForge",
            agentIcon: "🤖",
            agentColor: "#E94560",
            timestamp: Date.now(),
          });
        }

        // Notify if auto-started
        if (data.auto_started && data.squad_code) {
          addMessage({
            id: makeId(),
            role: "system",
            text: `Squad iniciado! Acompanhe o progresso no escritório.`,
            timestamp: Date.now(),
          });
        } else if (data.squad_code && !data.auto_started) {
          // Squad identified but not auto-started (no active yet or medium confidence)
          addMessage({
            id: makeId(),
            role: "system",
            text: `Squad identificado: ${data.squad_code}. Clique no card acima para iniciar.`,
            timestamp: Date.now(),
          });
        }
      } catch {
        addMessage({
          id: makeId(),
          role: "system",
          text: "Erro ao conectar com o servidor.",
          timestamp: Date.now(),
        });
      } finally {
        setLoading(false);
      }
    },
    [addMessage, setLoading, setQueue],
  );

  // Handle squad card click — pre-fill a message
  const handleSquadClick = useCallback(
    async (code: string) => {
      const squad = squads.find((s) => s.code === code);
      if (!squad) return;

      addMessage({
        id: makeId(),
        role: "user",
        text: `Iniciar: ${squad.name}`,
        timestamp: Date.now(),
      });
      setLoading(true);

      try {
        const res = await fetch(`${API_BASE}/api/v1/squads/start`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ squad_code: code }),
        });
        const data = await res.json();
        addMessage({
          id: makeId(),
          role: "agent",
          text: data.status === "started"
            ? `Squad ${data.squad_name} iniciado! Os agentes estão entrando no escritório...`
            : `Squad ${data.squad_name} adicionado à fila (posição ${data.queue_position}).`,
          agentName: "SocialForge",
          agentIcon: "🤖",
          agentColor: "#E94560",
          timestamp: Date.now(),
        });
      } catch {
        addMessage({
          id: makeId(),
          role: "system",
          text: "Erro ao iniciar squad.",
          timestamp: Date.now(),
        });
      } finally {
        setLoading(false);
      }
    },
    [squads, addMessage, setLoading],
  );

  // Checkpoint handlers
  const handleApprove = useCallback(
    (checkpointStepId: string) => {
      fetch(`${API_BASE}/api/v1/squads/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approved: true }),
      }).catch(() => {});
      addMessage({
        id: makeId(),
        role: "system",
        text: "✅ Aprovado! Continuando pipeline...",
        timestamp: Date.now(),
      });
    },
    [addMessage],
  );

  const handleAdjust = useCallback(
    (checkpointStepId: string, feedback: string) => {
      fetch(`${API_BASE}/api/v1/squads/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approved: false, feedback }),
      }).catch(() => {});
      addMessage({
        id: makeId(),
        role: "user",
        text: `Ajuste solicitado: ${feedback}`,
        timestamp: Date.now(),
      });
    },
    [addMessage],
  );

  const handleQueueRemove = useCallback(
    (id: string) => {
      const updated = queue.filter((item) => item.id !== id);
      setQueue(updated);
      fetch(`${API_BASE}/api/v1/squads/queue/${id}`, { method: "DELETE" }).catch(() => {});
    },
    [queue, setQueue],
  );

  // ---- Pipeline progress ----
  const showProgress =
    pipelineState !== null &&
    (pipelineState.status === "running" || pipelineState.status === "paused");
  const progressPct = showProgress
    ? Math.round((pipelineState!.currentStepIndex / Math.max(pipelineState!.totalSteps, 1)) * 100)
    : 0;

  const isInitialScreen = messages.length === 0;

  return (
    <div className="flex flex-col h-full bg-zinc-900 overflow-hidden">

      {/* Progress bar */}
      {showProgress && (
        <div className="flex-shrink-0 px-4 py-2 border-b border-zinc-800 bg-zinc-900">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-zinc-400 font-medium">
              Pipeline em andamento
            </span>
            <span className="text-xs text-zinc-500">
              {pipelineState!.currentStepIndex} / {pipelineState!.totalSteps} etapas
            </span>
          </div>
          <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-rose-600 rounded-full transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      )}

      {/* Messages / Initial screen */}
      <div className="flex-1 min-h-0 overflow-y-auto py-4">
        {isInitialScreen ? (
          <div className="flex flex-col items-center px-4 pt-6 pb-2">
            <div className="text-3xl mb-3">🏢</div>
            <h2 className="text-zinc-100 font-semibold text-lg mb-1">Claude Office</h2>
            <p className="text-zinc-400 text-sm text-center mb-6 max-w-xs">
              Bem-vindo! Escolha uma squad abaixo ou descreva o que você precisa.
            </p>

            {squads.length > 0 && (
              <div className="w-full max-w-md flex flex-col gap-2">
                {squads.map((squad) => (
                  <SquadCard key={squad.code} squad={squad} onClick={handleSquadClick} />
                ))}
              </div>
            )}

            {squads.length === 0 && (
              <p className="text-zinc-600 text-xs">Carregando squads...</p>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            {messages.map((msg) => {
              if (msg.role === "checkpoint") {
                return (
                  <CheckpointMessage
                    key={msg.id}
                    stepName={msg.agentName ?? "Checkpoint"}
                    content={msg.text}
                    onApprove={() => handleApprove(msg.checkpointStepId ?? "")}
                    onAdjust={(feedback) =>
                      handleAdjust(msg.checkpointStepId ?? "", feedback)
                    }
                    isResolved={msg.isApproved}
                  />
                );
              }

              return (
                <ChatMessage
                  key={msg.id}
                  role={msg.role as "user" | "agent" | "system"}
                  text={msg.text}
                  agentName={msg.agentName}
                  agentIcon={msg.agentIcon}
                  agentColor={msg.agentColor}
                />
              );
            })}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex items-center gap-3 px-4 py-1">
                <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center flex-shrink-0">
                  <span className="text-sm animate-pulse">🤖</span>
                </div>
                <div className="bg-zinc-800 border border-zinc-700 rounded-2xl rounded-tl-sm px-4 py-2.5">
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce [animation-delay:0ms]" />
                    <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce [animation-delay:150ms]" />
                    <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Queue indicator */}
      <QueueIndicator items={queue} onRemove={handleQueueRemove} />

      {/* Chat input */}
      <ChatInput
        onSend={handleSend}
        disabled={isLoading}
        placeholder={isInitialScreen ? "Descreva o que você precisa..." : "Digite uma mensagem..."}
      />
    </div>
  );
}
