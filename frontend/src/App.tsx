import { useEffect, useState } from "react";
import { api, getToken, setToken, type ChecklistItem, type Recommendation, type Score } from "./api";
import { Login } from "./components/Login";
import { ChecklistCard, RecommendationsCard, ScoreCard } from "./components/Results";
import { UsagePanel } from "./components/UsagePanel";
import { COMPONENTS, PROFILES } from "./profiles";

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  if (!authed) return <Login onLogin={() => setAuthed(true)} />;
  return <Dashboard onLogout={() => { setToken(null); setAuthed(false); }} />;
}

function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [me, setMe] = useState<{ name: string; email: string } | null>(null);
  const [name, setName] = useState("Perfume Aurora 100ml");
  const [category, setCategory] = useState("perfumes");
  const [cap, setCap] = useState("rosca");
  const [components, setComponents] = useState<string[]>(["frasco", "tampa", "rotulo"]);
  const [profiles, setProfiles] = useState<string[]>(["baixa_visao", "artrite"]);
  const [image, setImage] = useState<File | null>(null);

  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [score, setScore] = useState<Score | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [usageKey, setUsageKey] = useState(0);

  useEffect(() => { api.me().then(setMe).catch(() => onLogout()); }, []);

  function toggle(list: string[], set: (v: string[]) => void, id: string) {
    set(list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);
  }

  async function runAnalysis(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setScore(null);
    setChecklist([]);
    setRecs([]);
    try {
      setStatus("Criando projeto e produto…");
      const project = await api.createProject("Análise via painel");
      const product = await api.createProduct({
        project_id: project.id, name, category, cap_type: cap,
        components: components.map((c) => ({ component_type: c })),
      });
      if (image) {
        setStatus("Enviando imagem…");
        await api.uploadImage(product.id, image, "embalagem");
      }
      setStatus("Executando análise de acessibilidade (agentes)…");
      let run = await api.runAnalysis(product.id, profiles);
      // suporta modo assíncrono: aguarda conclusão
      for (let i = 0; run.status !== "done" && i < 60; i++) {
        await new Promise((r) => setTimeout(r, 500));
        run = await api.getRun(run.id);
      }
      setStatus("Carregando resultados…");
      const [s, c, r] = await Promise.all([
        api.score(run.id), api.checklist(run.id), api.recommendations(run.id),
      ]);
      setScore(s);
      setChecklist(c);
      setRecs(r);
      setStatus("Análise concluída.");
      setUsageKey((k) => k + 1);
    } catch (err) {
      setError((err as Error).message);
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <a href="#main" className="skip-link">Pular para o conteúdo</a>
      <header className="app">
        <div className="brand">
          <span aria-hidden="true" style={{ fontSize: "1.4rem" }}>💜</span>
          <h1>Inclua Beauty AI</h1>
        </div>
        <div className="row" style={{ alignItems: "center" }}>
          {me && <span className="muted">{me.name}</span>}
          <button className="secondary" onClick={onLogout}>Sair</button>
        </div>
      </header>

      <main id="main">
        <section className="card" aria-labelledby="form-h">
          <h2 id="form-h">Nova análise de embalagem</h2>
          <form onSubmit={runAnalysis}>
            <div className="grid-2">
              <div>
                <label htmlFor="pname">Nome do produto</label>
                <input id="pname" value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div>
                <label htmlFor="cat">Categoria</label>
                <select id="cat" value={category} onChange={(e) => setCategory(e.target.value)}>
                  {["perfumes", "maquiagem", "skincare", "cabelos", "corpo",
                    "infantil", "masculino", "60+", "pet", "acessorios"].map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            <label htmlFor="cap">Tipo de tampa</label>
            <select id="cap" value={cap} onChange={(e) => setCap(e.target.value)}>
              {["rosca", "flip_top", "press_to_open", "asas", "magnetica", "spray", "pump"].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            <fieldset>
              <legend>Componentes da embalagem</legend>
              <div className="checkbox-grid">
                {COMPONENTS.map((c) => (
                  <label key={c}>
                    <input type="checkbox" checked={components.includes(c)}
                      onChange={() => toggle(components, setComponents, c)} />
                    {c}
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend>Perfis de necessidade a analisar</legend>
              <div className="checkbox-grid">
                {PROFILES.map((p) => (
                  <label key={p.id}>
                    <input type="checkbox" checked={profiles.includes(p.id)}
                      onChange={() => toggle(profiles, setProfiles, p.id)} />
                    {p.label}
                  </label>
                ))}
              </div>
            </fieldset>

            <label htmlFor="img">Imagem da embalagem (opcional — ingestão multimodal)</label>
            <input id="img" type="file" accept="image/*"
              onChange={(e) => setImage(e.target.files?.[0] ?? null)} />

            <div style={{ marginTop: "1rem" }}>
              <button type="submit" disabled={busy || profiles.length === 0}>
                {busy ? "Analisando…" : "Executar análise"}
              </button>
            </div>
          </form>

          <p role="status" aria-live="polite" className="muted" style={{ marginTop: "0.8rem" }}>
            {status}
          </p>
          {error && <p className="error" role="alert">{error}</p>}
        </section>

        {score && (
          <div aria-live="polite">
            <ScoreCard score={score} />
            <RecommendationsCard recs={recs} />
            <ChecklistCard items={checklist} />
          </div>
        )}

        <UsagePanel refreshKey={usageKey} />
      </main>
    </>
  );
}
