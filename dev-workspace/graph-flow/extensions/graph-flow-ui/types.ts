export type AnswerType = "single_select" | "multi_select" | "confirm" | "text";

export interface InputRequest {
  id: string;
  kind: "input" | "approval";
  answer_type: AnswerType;
  prompt: string;
  rationale?: string;
  options?: string[];
  scope: "preflight" | "node";
  node: string | null;
}

export interface CockpitNode {
  id: string;
  status: string;
  workstream?: string;
  kind?: string;
  objective?: string;
  assigned_role?: string;
  priority?: string;
  paths?: string[];
  resources?: string[];
  verification_commands?: string[];
  outcomes?: string[];
  failure_outcomes?: string[];
  transitions?: Record<string, string>;
  prompt?: string;
  depends_on?: Array<{ node: string; outcome: string }>;
  depends_on_any?: Array<{ node: string; outcome: string }>;
  attempts?: number;
  task_id?: string | null;
  acceptance_criteria?: string[];
  evidence?: Record<string, unknown> | null;
  artifacts?: Record<string, unknown> | null;
}

export interface CockpitWorkstream {
  id: string;
  title?: string;
  objective?: string;
  status?: string;
  node_counts?: Record<string, number>;
}

export interface PendingApproval {
  scope: "graph" | "node";
  node: string | null;
  prompt: string;
  objective: string | null;
  allowed_outcomes: string[];
  kind: "approval";
  evidence_required: true;
}

export interface CockpitRequirements {
  goal?: string;
  success_criteria?: string[];
  scope?: { included?: string[]; excluded?: string[] };
  constraints?: string[];
  verification?: string[];
  approval_boundaries?: string[];
  assumptions?: string[];
}

export interface CockpitLimits {
  max_attempts_per_node?: number;
  max_transitions?: number;
}

export interface CockpitSnapshot {
  cockpit_version: number;
  run_id: string;
  status: string;
  phase?: string;
  updated_at: string;
  goal: string | null;
  plan_revision: number;
  max_concurrency?: number;
  limits?: CockpitLimits;
  progress: { completed: number; skipped: number; total: number; ratio: number } | null;
  node_counts: Record<string, number> | null;
  active_handles: Array<{ node: string; task_id: string }>;
  open_request: InputRequest | null;
  pending_approval?: PendingApproval | null;
  requirements?: CockpitRequirements | null;
  reason: string | null;
  state_path?: string;
  workstreams?: CockpitWorkstream[];
  nodes?: CockpitNode[];
  recent_events?: Array<{ seq: number; at: string; event: string; node?: string }>;
}

export interface CommandResult {
  code: number;
  stdout: string;
  stderr: string;
}

export interface CommandRunner {
  execute(command: string, args: string[]): Promise<CommandResult>;
}

export interface DialogUI {
  select(title: string, options: string[]): Promise<string | string[] | undefined>;
  confirm(title: string, message: string): Promise<boolean>;
  input(title: string, placeholder?: string): Promise<string | undefined>;
}
