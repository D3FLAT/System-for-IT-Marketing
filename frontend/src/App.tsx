import { useCallback, useEffect, useState } from "react";
import { createStrategy, getTracking, listStrategies, uploadFile } from "./api";
import type { KpiTracking, Status, Strategy, Tracking } from "./api";

const STATUS: Record<Status, { label: string; cls: string }> = {
  on_track: { label: "В норме", cls: "bg-emerald-100 text-emerald-800" },
  at_risk: { label: "Риск", cls: "bg-amber-100 text-amber-800" },
  off_track: { label: "Отставание", cls: "bg-red-100 text-red-800" },
  no_data: { label: "Нет данных", cls: "bg-slate-100 text-slate-600" },
};

const fmt = (n: number | null | undefined) =>
  n === null || n === undefined ? "—" : n.toLocaleString("ru-RU", { maximumFractionDigits: 2 });

function Badge({ s }: { s: Status }) {
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS[s].cls}`}>{STATUS[s].label}</span>;
}

function Chart({ kpi }: { kpi: KpiTracking }) {
  const W = 600, H = 220, L = 44, R = 10, T = 10, B = 28;
  const max = Math.max(1e-9, ...kpi.periods.flatMap((p) => [p.plan, p.fact ?? 0]));
  const group = (W - L - R) / Math.max(1, kpi.periods.length);
  const bw = Math.min(28, group / 3);
  const y = (v: number) => T + (H - T - B) * (1 - Math.max(0, v) / max);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`План и факт: ${kpi.name}`}>
      <line x1={L} y1={y(0)} x2={W - R} y2={y(0)} stroke="#cbd5e1" />
      <text x={L - 6} y={y(0) + 4} textAnchor="end" fontSize="11" fill="#64748b">0</text>
      <text x={L - 6} y={y(max) + 4} textAnchor="end" fontSize="11" fill="#64748b">{fmt(max)}</text>
      {kpi.periods.map((p, i) => {
        const cx = L + i * group + group / 2;
        return (
          <g key={p.period}>
            <rect x={cx - bw - 1} y={y(p.plan)} width={bw} height={y(0) - y(p.plan)} fill="#cbd5e1" />
            {p.fact !== null && (
              <rect x={cx + 1} y={y(p.fact)} width={bw} height={y(0) - y(p.fact)} fill="#4f46e5" />
            )}
            <text x={cx} y={H - 10} textAnchor="middle" fontSize="11" fill="#475569">{p.period}</text>
          </g>
        );
      })}
    </svg>
  );
}

export default function App() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [sid, setSid] = useState<number | null>(null);
  const [tracking, setTracking] = useState<Tracking | null>(null);
  const [kpiId, setKpiId] = useState<number | null>(null);
  const [newName, setNewName] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const fail = (e: unknown) => setMsg({ ok: false, text: e instanceof Error ? e.message : String(e) });

  const loadTracking = useCallback(async (id: number) => {
    try {
      const t = await getTracking(id);
      setTracking(t);
      setKpiId((cur) => (t.kpis.some((k) => k.kpi_id === cur) ? cur : (t.kpis[0]?.kpi_id ?? null)));
    } catch (e) {
      fail(e);
    }
  }, []);

  useEffect(() => {
    listStrategies()
      .then((list) => {
        setStrategies(list);
        if (list.length) setSid(list[0].id);
      })
      .catch(fail);
  }, []);

  useEffect(() => {
    if (sid !== null) void loadTracking(sid);
    else setTracking(null);
  }, [sid, loadTracking]);

  const onCreate = async () => {
    if (!newName.trim()) return;
    try {
      const s = await createStrategy(newName.trim());
      setStrategies((l) => [...l, s]);
      setSid(s.id);
      setNewName("");
      setMsg(null);
    } catch (e) {
      fail(e);
    }
  };

  const onFile = async (file?: File) => {
    if (!file || sid === null) return;
    try {
      const r = await uploadFile(sid, file);
      setMsg({
        ok: true,
        text: `Загружено: новых показателей ${r.kpis_created}, добавлено измерений ${r.measurements_created}, обновлено ${r.measurements_updated}`,
      });
      await loadTracking(sid);
    } catch (e) {
      fail(e);
    }
  };

  const kpis = tracking?.kpis ?? [];
  const selected = kpis.find((k) => k.kpi_id === kpiId) ?? null;
  const count = (s: Status) => kpis.filter((k) => k.status === s).length;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Отслеживание эффективности стратегии</h1>
          <p className="text-sm text-slate-500">План и факт по показателям, отклонения и статусы</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            value={sid ?? ""}
            onChange={(e) => setSid(Number(e.target.value))}
            aria-label="Стратегия"
          >
            {strategies.length === 0 && <option value="">Нет стратегий</option>}
            {strategies.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <input
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Новая стратегия"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void onCreate()}
          />
          <button className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm hover:bg-slate-100" onClick={() => void onCreate()}>
            Создать
          </button>
          <label className={`rounded-md bg-indigo-600 px-3 py-2 text-sm text-white ${sid === null ? "opacity-50" : "cursor-pointer hover:bg-indigo-700"}`}>
            Загрузить файл
            <input
              type="file"
              accept=".csv,.xlsx"
              className="hidden"
              disabled={sid === null}
              onChange={(e) => {
                void onFile(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
          </label>
        </div>
      </header>

      {msg && (
        <div className={`whitespace-pre-line rounded-md p-3 text-sm ${msg.ok ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"}`} role="status">
          {msg.text}
        </div>
      )}

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {(["on_track", "at_risk", "off_track", "no_data"] as Status[]).map((s) => (
          <div key={s} className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="text-3xl font-semibold">{count(s)}</div>
            <div className="mt-1"><Badge s={s} /></div>
          </div>
        ))}
      </section>

      <section className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="p-3 font-medium">Показатель</th>
              <th className="p-3 font-medium">Статус</th>
              <th className="p-3 text-right font-medium">План</th>
              <th className="p-3 text-right font-medium">Факт</th>
              <th className="p-3 text-right font-medium">Выполнение</th>
              <th className="p-3 text-right font-medium">Отклонение</th>
            </tr>
          </thead>
          <tbody>
            {kpis.length === 0 && (
              <tr>
                <td colSpan={6} className="p-6 text-center text-slate-500">
                  Данных пока нет. Выберите стратегию и загрузите файл с планом и фактом (CSV или XLSX).
                </td>
              </tr>
            )}
            {kpis.map((k) => {
              const last = [...k.periods].reverse().find((p) => p.fact !== null);
              return (
                <tr
                  key={k.kpi_id}
                  onClick={() => setKpiId(k.kpi_id)}
                  className={`cursor-pointer border-t border-slate-100 hover:bg-slate-50 ${k.kpi_id === kpiId ? "bg-indigo-50" : ""}`}
                >
                  <td className="p-3 font-medium">
                    {k.name}
                    {k.unit && <span className="ml-1 text-slate-400">({k.unit})</span>}
                  </td>
                  <td className="p-3"><Badge s={k.status} /></td>
                  <td className="p-3 text-right">{fmt(last?.plan)}</td>
                  <td className="p-3 text-right">{fmt(last?.fact)}</td>
                  <td className="p-3 text-right">{last?.completion_pct != null ? `${fmt(last.completion_pct)}%` : "—"}</td>
                  <td className="p-3 text-right">{fmt(last?.deviation)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      {selected && (
        <section className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="font-medium">
              {selected.name}: план и факт по периодам
              <span className="ml-2 text-xs text-slate-400">
                {selected.higher_is_better ? "больше — лучше" : "меньше — лучше"}
              </span>
            </h2>
            <div className="flex gap-3 text-xs text-slate-500">
              <span><span className="mr-1 inline-block h-2 w-3 bg-slate-300" />План</span>
              <span><span className="mr-1 inline-block h-2 w-3 bg-indigo-600" />Факт</span>
            </div>
          </div>
          <Chart kpi={selected} />
        </section>
      )}
    </div>
  );
}
