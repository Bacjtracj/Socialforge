"use client";

type MessageRole = "user" | "agent" | "system";

interface ChatMessageProps {
  role: MessageRole;
  text: string;
  agentName?: string;
  agentIcon?: string;
  agentColor?: string;
}

export function ChatMessage({ role, text, agentName, agentIcon, agentColor }: ChatMessageProps) {
  if (role === "user") {
    return (
      <div className="flex justify-end px-4 py-1">
        <div className="max-w-[75%] bg-rose-700 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed">
          {text}
        </div>
      </div>
    );
  }

  const isSystem = role === "system";
  const avatarColor = agentColor ?? (isSystem ? "#6b7280" : "#3b82f6");
  const avatarIcon = agentIcon ?? (isSystem ? "⚙️" : "🤖");
  const displayName = agentName ?? (isSystem ? "System" : "Agent");

  return (
    <div className="flex items-start gap-3 px-4 py-1">
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm"
        style={{ backgroundColor: avatarColor + "33", border: `1px solid ${avatarColor}55` }}
      >
        <span>{avatarIcon}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xs font-medium mb-1" style={{ color: avatarColor }}>
          {displayName}
        </div>
        <div className="bg-zinc-800 border border-zinc-700 text-zinc-100 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm leading-relaxed">
          {text}
        </div>
      </div>
    </div>
  );
}
