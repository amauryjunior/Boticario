import type { ChecklistItem, Recommendation, Score } from "../api";

const GATE_CLASS: Record<string, string> = {
  vermelho: "bad", amarelo: "warn", verde: "ok", azul: "info",
};
const STATUS_CLASS: Record<string, string> = {
  atende: "ok", parcial: "warn", a_validar: "info", nao_atende: "bad", nao_aplicavel: "info",
};
const STATUS_LABEL: Record<string, string> = {
  atende: "Atende", parcial: "Atende parcialmente", a_validar: "A validar",
  nao_atende: "Não atende", nao_aplicavel: "Não aplicável",
};

export function ScoreCard({ score }: { score: Score }) {
  return (
    <section className="card" aria-labelledby="score-h">
      <h2 id="score-h">Score de acessibilidade</h2>
      <div className="row" style={{ alignItems: "center", gap: "1.5rem" }}>
        <div>
          <span className="score-num">{score.score_total}</span>
          <span className="muted"> / 100</span>
          <div>
            <strong>{score.maturity_level}</strong>{" "}
            <span className={`badge ${GATE_CLASS[score.gate] || "info"}`}>
              Gate {score.gate}
            </span>
          </div>
        </div>
      </div>
      <table style={{ marginTop: "1rem" }}>
        <caption className="visually-hidden">Pontuação por dimensão</caption>
        <thead>
          <tr><th scope="col">Dimensão</th><th scope="col">Peso</th><th scope="col">Score</th></tr>
        </thead>
        <tbody>
          {score.dimensions.map((d) => (
            <tr key={d.dimension}>
              <th scope="row" style={{ fontWeight: 400 }}>{d.dimension}</th>
              <td>{d.weight}</td>
              <td>
                <div className="row" style={{ alignItems: "center", gap: "0.5rem" }}>
                  <div className="meter" style={{ width: 90 }} aria-hidden="true">
                    <span style={{ width: `${d.score}%` }} />
                  </div>
                  <span>{d.score}</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export function ChecklistCard({ items }: { items: ChecklistItem[] }) {
  return (
    <section className="card" aria-labelledby="check-h">
      <h2 id="check-h">Checklist de acessibilidade</h2>
      <table>
        <thead>
          <tr>
            <th scope="col">Dimensão</th><th scope="col">Item</th>
            <th scope="col">Status</th><th scope="col">Evidência</th>
          </tr>
        </thead>
        <tbody>
          {items.map((c, i) => (
            <tr key={i}>
              <td>{c.dimension}</td>
              <td>{c.item}</td>
              <td>
                <span className={`badge ${STATUS_CLASS[c.status] || "info"}`}>
                  {STATUS_LABEL[c.status] || c.status}
                </span>
              </td>
              <td className="muted">{c.evidence}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export function RecommendationsCard({ recs }: { recs: Recommendation[] }) {
  return (
    <section className="card" aria-labelledby="rec-h">
      <h2 id="rec-h">Recomendações priorizadas</h2>
      {recs.length === 0 && <p className="muted">Nenhuma barreira relevante identificada.</p>}
      {recs.map((r, i) => (
        <article key={i} style={{ borderTop: i ? "1px solid var(--border)" : "none", paddingTop: "0.8rem", marginTop: "0.8rem" }}>
          <h3 style={{ marginBottom: "0.3rem" }}>
            {r.barrier}{" "}
            {r.priority && (
              <span className={`badge ${r.priority === "alta" ? "bad" : "warn"}`}>
                prioridade {r.priority}
              </span>
            )}
          </h3>
          {r.component && <p className="muted" style={{ margin: "0.2rem 0" }}>Componente: {r.component}</p>}
          <ul className="rec-options">
            {r.option_min && <li><strong>Mínima:</strong> {r.option_min}</li>}
            {r.option_mid && <li><strong>Intermediária:</strong> {r.option_mid}</li>}
            {r.option_premium && <li><strong>Premium:</strong> {r.option_premium}</li>}
          </ul>
          {r.standard_ref && (
            <p style={{ margin: "0.4rem 0 0" }}>
              <span className="badge info">Norma</span> {r.standard_ref}
              {r.standard_status && <span className="muted"> — status: {r.standard_status}</span>}
            </p>
          )}
          {r.norm_evidence && (
            <p className="muted" style={{ marginTop: "0.3rem", fontSize: "0.9rem" }}>
              Evidência (RAG): {r.norm_evidence}
            </p>
          )}
        </article>
      ))}
    </section>
  );
}
