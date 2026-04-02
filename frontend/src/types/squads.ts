export interface AgentIdentity {
  squadAgentId: string;
  displayName: string;
  color: string;
  spriteKey: string;
  icon: string;
}

export interface PipelineStep {
  id: string;
  name: string;
  type: "agent" | "checkpoint";
  agent?: string;
  tasks: string[];
  dependsOn?: string;
}

export type PipelineStepStatus =
  | "pending"
  | "active"
  | "completed"
  | "waiting_approval"
  | "approved"
  | "retry"
  | "error";

export type SquadStatus = "pending" | "running" | "paused" | "completed" | "error";

export interface SquadSummary {
  code: string;
  name: string;
  description: string;
  icon: string;
  agentCount: number;
  stepCount: number;
}

export interface CheckpointState {
  stepId: string;
  stepName: string;
  content: string;
  awaitingApproval: boolean;
  approved?: boolean;
  feedback?: string;
}

export interface PipelineState {
  squadCode: string;
  sessionId: string;
  totalSteps: number;
  currentStepIndex: number;
  status: SquadStatus;
  stepStates: Record<string, PipelineStepStatus>;
  outputs: Record<string, string>;
  checkpoint?: CheckpointState;
}

export interface SquadQueueItem {
  id: string;
  squadCode: string;
  squadName: string;
  position: number;
  userInput?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "agent" | "system" | "checkpoint";
  agentName?: string;
  agentIcon?: string;
  agentColor?: string;
  text: string;
  timestamp: number;
  checkpointStepId?: string;
  isApproved?: boolean;
}
