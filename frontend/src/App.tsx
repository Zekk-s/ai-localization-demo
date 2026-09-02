import { useState } from "react";
import type { FormEvent } from "react";

type Locale = { code: string; name: string; formality_default: string };

const LOCALES_URL = "/v1/locales";
const TRANSLATE_URL = "/v1/translate";

export default function App() {
  const [locales, setLocales] = useState<Locale[]>([]);
  const [text, setText] = useState("Hello, world.");
  const [source, setSource] = useState("en");
  const [target, setTarget] = useState("tr");
  const [formality, setFormality] = useState("neutral");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);

  useState(() => {
    void fetch(LOCALES_URL)
      .then((r) => r.json())
      .then((d: { locales: Locale[] }) => setLocales(d.locales ?? []));
  });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setOutput("");
    try {
      const r = await fetch(TRANSLATE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, source, target, formality, glossary: {} }),
      });
      if (!r.ok) {
        setOutput(`error ${r.status}`);
        return;
      }
      const data = await r.json();
      setOutput(data.text ?? "");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <h1>ai-localization-demo</h1>
      <p className="muted">Provider-agnostic AI translation · {locales.length} locales</p>
      <form onSubmit={onSubmit}>
        <label>
          Source
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            {locales.map((l) => (
              <option key={l.code} value={l.code}>
                {l.code} · {l.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Target
          <select value={target} onChange={(e) => setTarget(e.target.value)}>
            {locales.map((l) => (
              <option key={l.code} value={l.code}>
                {l.code} · {l.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Formality
          <select value={formality} onChange={(e) => setFormality(e.target.value)}>
            <option value="formal">formal</option>
            <option value="neutral">neutral</option>
            <option value="casual">casual</option>
          </select>
        </label>
        <label>
          Text
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4} />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Translating…" : "Translate"}
        </button>
      </form>
      <section className="output">
        <h2>Output</h2>
        <pre>{output}</pre>
      </section>
    </main>
  );
}