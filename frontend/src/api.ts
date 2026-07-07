// Cliente da API Inclua Beauty AI.
const BASE = "/api/v1";

export type Token = string;

let token: Token | null = localStorage.getItem("ib_token");

export function setToken(t: Token | null) {
  token = t;
  if (t) localStorage.setItem("ib_token", t);
  else localStorage.removeItem("ib_token");
}

export function getToken() {
  return token;
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { ...(opts.headers as any) };
  if (!(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(BASE + path, { ...opts, headers });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error((detail as any).detail || `Erro ${res.status}`);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

export interface Score {
  score_total: number;
  maturity_level: string;
  gate: string;
  dimensions: { dimension: string; weight: number; score: number }[];
}
export interface Recommendation {
  component: string | null;
  barrier: string;
  impact: string | null;
  option_min: string | null;
  option_mid: string | null;
  option_premium: string | null;
  priority: string | null;
  standard_ref: string | null;
  standard_status: string | null;
  norm_evidence: string | null;
}
export interface ChecklistItem {
  dimension: string;
  item: string;
  status: string;
  evidence: string | null;
  priority: string | null;
}
export interface Usage {
  total_analyses: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_cost_per_analysis_usd: number;
  avg_latency_ms: number;
  by_agent: { agent: string; calls: number; tokens: number; cost_usd: number }[];
}

export const api = {
  login: (email: string, password: string) =>
    req<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  signup: (organization_name: string, name: string, email: string, password: string) =>
    req<{ access_token: string }>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ organization_name, name, email, password }),
    }),
  me: () => req<{ name: string; email: string; role: string }>("/me"),
  projects: () => req<any[]>("/projects"),
  createProject: (name: string, objective?: string) =>
    req<any>("/projects", { method: "POST", body: JSON.stringify({ name, objective }) }),
  createProduct: (p: any) =>
    req<any>("/products", { method: "POST", body: JSON.stringify(p) }),
  uploadImage: (productId: string, file: File, imageType: string) => {
    const fd = new FormData();
    fd.append("file", file);
    return req<any>(`/products/${productId}/images?image_type=${imageType}`, {
      method: "POST",
      body: fd,
    });
  },
  runAnalysis: (product_id: string, profiles: string[]) =>
    req<any>("/analysis-runs", {
      method: "POST",
      body: JSON.stringify({ product_id, profiles }),
    }),
  getRun: (id: string) => req<any>(`/analysis-runs/${id}`),
  score: (id: string) => req<Score>(`/analysis-runs/${id}/score`),
  checklist: (id: string) => req<ChecklistItem[]>(`/analysis-runs/${id}/checklist`),
  recommendations: (id: string) => req<Recommendation[]>(`/analysis-runs/${id}/recommendations`),
  trace: (id: string) => req<any[]>(`/analysis-runs/${id}/trace`),
  usage: () => req<Usage>("/admin/usage"),
  searchStandards: (q: string) =>
    req<{ matches: any[] }>(`/standards/search?q=${encodeURIComponent(q)}`),
};
