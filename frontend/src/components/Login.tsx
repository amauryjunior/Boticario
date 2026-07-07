import { useState } from "react";
import { api, setToken } from "../api";

export function Login({ onLogin }: { onLogin: () => void }) {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("demo@incluabeauty.ai");
  const [password, setPassword] = useState("demo1234");
  const [org, setOrg] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res =
        mode === "login"
          ? await api.login(email, password)
          : await api.signup(org, name, email, password);
      setToken(res.access_token);
      onLogin();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <section className="card" style={{ maxWidth: 460, margin: "3rem auto" }} aria-labelledby="login-h">
        <h1 id="login-h">Inclua Beauty AI</h1>
        <p className="muted">Acessibilidade de embalagens de beleza.</p>

        <div className="row" role="tablist" aria-label="Modo de acesso" style={{ marginBottom: "0.5rem" }}>
          <button className={mode === "login" ? "" : "secondary"} aria-pressed={mode === "login"}
            onClick={() => setMode("login")} type="button">Entrar</button>
          <button className={mode === "signup" ? "" : "secondary"} aria-pressed={mode === "signup"}
            onClick={() => setMode("signup")} type="button">Criar conta</button>
        </div>

        <form onSubmit={submit}>
          {mode === "signup" && (
            <>
              <label htmlFor="org">Organização</label>
              <input id="org" value={org} onChange={(e) => setOrg(e.target.value)} required />
              <label htmlFor="name">Seu nome</label>
              <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
            </>
          )}
          <label htmlFor="email">E-mail</label>
          <input id="email" type="email" autoComplete="email" value={email}
            onChange={(e) => setEmail(e.target.value)} required />
          <label htmlFor="password">Senha</label>
          <input id="password" type="password" autoComplete="current-password" value={password}
            onChange={(e) => setPassword(e.target.value)} required />

          {error && <p className="error" role="alert" style={{ marginTop: "0.7rem" }}>{error}</p>}

          <div style={{ marginTop: "1rem" }}>
            <button type="submit" disabled={busy}>
              {busy ? "Aguarde…" : mode === "login" ? "Entrar" : "Criar conta"}
            </button>
          </div>
        </form>
        <p className="muted" style={{ marginTop: "1rem", fontSize: "0.9rem" }}>
          Conta de demonstração já preenchida.
        </p>
      </section>
    </main>
  );
}
