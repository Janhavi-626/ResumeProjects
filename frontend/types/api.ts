export type PolicySource = {
  document_id: string;
  title: string;
  source: string;
  category: string;
  section: string;
  version: string;
  effective_date: string;
  excerpt: string;
  citation: string;
};

export type ProposedAction = {
  action_type: string;
  description: string;
  requires_approval: boolean;
  expected_impact: string;
  parameters: Record<string, unknown>;
};

export type AgentResponse = {
  workflow_id: string;
  session_id: string;
  status: string;
  intent: string;
  classification: string;
  confidence: number;
  evidence: string[];
  policy_sources: PolicySource[];
  recommended_action: ProposedAction | null;
  approval_required: boolean;
  completed_actions: { success: boolean; action_id?: string; action_type?: string; status?: string }[];
  pending_actions: ProposedAction[];
  final_response: string;
  workflow_state: { current_stage: string; agent_status: string[]; tool_results: unknown[]; errors: string[]; validation_result: Record<string, unknown> };
};