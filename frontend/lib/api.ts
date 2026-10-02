import type { AgentResponse, ProposedAction } from "@/types/api";

function getApiBase() {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) return configured.replace(/\/$/, "");
  if (typeof window !== "undefined" && ["localhost", "127.0.0.1"].includes(window.location.hostname)) {
    return "http://localhost:8001";
  }
  throw new Error("The backend API is not configured for this deployment. Set NEXT_PUBLIC_API_URL to a public FastAPI URL.");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBase()}/api${path}`, {
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