import { useEffect, useState } from "react";
import { api, type Usage } from "../api";

export function UsagePanel({ refreshKey }: { refreshKey: number }) {
  const [usage, setUsage] = useState<Usage | null>(null);

  useEffect(() => {
    api.usage().then(setUsage).catch(() => setUsage(null));
  }, [refreshKey]);

  if (!usage) return null;
  return (
    <section className="card" aria-labelledby="usage-h">
      <h2 id="usage-h">Uso e custo de IA</h2>
      <div className="grid-2">
        <div>
          <p style={{ margin: "0.2rem 0" }}><strong>{usage.total_analyses}</strong> análises</p>
          <p style={{ margin: "0.2rem 0" }}><strong>{usage.total_tokens.toLocaleString("pt-BR")}</strong> tokens</p>
        </div>
        <div>
          <p style={{ margin: "0.2rem 0" }}>Custo total: <strong>US$ {usage.total_cost_usd.toFixed(4)}</strong></p>
          <p style={{ margin: "0.2rem 0" }}>Custo médio/análise: <strong>US$ {usage.avg_cost_per_analysis_usd.toFixed(4)}</strong></p>
          <p style={{ margin: "0.2rem 0" }}>Latência média: <strong>{usage.avg_latency_ms} ms</strong></p>
        </div>
      </div>
      {usage.by_agent.length > 0 && (
        <table style={{ marginTop: "0.8rem" }}>
          <thead>
            <tr><th scope="col">Agente</th><th scope="col">Chamadas</th><th scope="col">Tokens</th><th scope="col">Custo (US$)</th></tr>
          </thead>
          <tbody>
            {usage.by_agent.map((a) => (
              <tr key={a.agent}>
                <th scope="row" style={{ fontWeight: 400 }}>{a.agent}</th>
                <td>{a.calls}</td>
                <td>{a.tokens.toLocaleString("pt-BR")}</td>
                <td>{a.cost_usd.toFixed(6)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
