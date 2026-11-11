export type Status = "on_track" | "at_risk" | "off_track" | "no_data";

export interface Period {
  period: string;
  plan: number;
  fact: number | null;
  deviation: number | null;
  completion_pct: number | null;
  status: Status;
}
export interface KpiTracking {
  kpi_id: number;
  name: string;
  unit: string;
  higher_is_better: boolean;
  status: Status;
  periods: Period[];
}
export interface Tracking {
  strategy_id: number;
  ok_threshold: number;
  risk_threshold: number;
  kpis: KpiTracking[];
}
export interface Strategy {
  id: number;
  name: string;
  description: string;
}
export interface ImportSummary {
  kpis_created: number;
  measurements_created: number;
  measurements_updated: number;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api${path}`, init);
  if (!r.ok) {
    let msg = `Ошибка ${r.status}`;
    try {
      const detail = (await r.json()).detail;
      msg = Array.isArray(detail)
        ? detail.map((e: unknown) => (typeof e === "string" ? e : (e as { msg: string }).msg)).join("\n")
        : String(detail ?? msg);
    } catch {
      /* тело ответа не JSON */
    }
    throw new Error(msg);
  }
  return r.json() as Promise<T>;
}

export const listStrategies = () => req<Strategy[]>("/strategies");

export const createStrategy = (name: string) =>
  req<Strategy>("/strategies", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });

export const getTracking = (id: number) => req<Tracking>(`/strategies/${id}/tracking`);

export const uploadFile = (id: number, file: File) => {
  const body = new FormData();
  body.append("file", file);
  return req<ImportSummary>(`/strategies/${id}/import`, { method: "POST", body });
};
