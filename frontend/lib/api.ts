import type { AgentResponse, ProposedAction } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function runInvestigation(message: string, sessionId?: string) {
  return request<AgentResponse>("/chat", { method: "POST", body: JSON.stringify({ message, session_id: sessionId }) });
}

export function decideApproval(workflowId: string, decision: "approve" | "reject" | "modify", modifiedAction?: ProposedAction) {
  return request<AgentResponse>(`/approval/${workflowId}`, {
    method: "POST",
    body: JSON.stringify({ decision, reviewer: "operations-manager", comment: "Reviewed in operations console", modified_action: modifiedAction }),
  });
}