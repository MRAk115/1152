import { useEffect, useRef, useState, type FormEvent } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type ChatResponse = {
  content: string;
  provider: string;
  fallback_used: boolean;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("Connecting…");
  const [provider, setProvider] = useState("");
  const [speakReplies, setSpeakReplies] = useState(false);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [transcribing, setTranscribing] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void fetch(`${API_BASE}/api/health`)
      .then(async (response) => {
        if (!response.ok) throw new Error("Backend health check failed.");
        const result: { status: string; provider: string } = await response.json();
        setStatus(result.status === "ok" ? "Online" : "Unavailable");
        setProvider(result.provider);
      })
      .catch(() => setStatus("Offline"));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;

    const nextMessages: Message[] = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setError("");
    setBusy(true);
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "The chat request failed.");
      const reply = result as ChatResponse;
      setProvider(reply.provider);
      setMessages([...nextMessages, { role: "assistant", content: reply.content }]);
      if (speakReplies && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(new SpeechSynthesisUtterance(reply.content));
      }
      if (reply.fallback_used) setError(`Primary provider unavailable; replied via ${reply.provider}.`);
    } catch (requestError) {
      setMessages(nextMessages);
      setError(requestError instanceof Error ? requestError.message : "The chat request failed.");
    } finally {
      setBusy(false);
    }
  }

  async function transcribeAudio() {
    if (!audioFile || transcribing) return;
    setError("");
    setTranscribing(true);
    try {
      const form = new FormData();
      form.append("audio", audioFile);
      const response = await fetch(`${API_BASE}/api/transcribe`, { method: "POST", body: form });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Audio transcription failed.");
      if (!result.text) throw new Error("No speech was detected in the audio.");
      setInput((value) => [value.trim(), result.text].filter(Boolean).join(" "));
      setAudioFile(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Audio transcription failed.");
    } finally {
      setTranscribing(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Jarvis home">
          <span className="brand-mark">J</span>
          <span>JARVIS</span>
        </a>
        <div className="connection">
          <span className={`status-dot ${status === "Online" ? "online" : ""}`} />
          <span>{status}</span>
          {provider && <span className="provider-tag">{provider}</span>}
        </div>
      </header>

      <section className="conversation" aria-live="polite">
        {messages.length === 0 ? (
          <div className="welcome">
            <div className="orb"><span /></div>
            <p className="eyebrow">YOUR LOCAL-FIRST ASSISTANT</p>
            <h1>How can I help?</h1>
            <p className="welcome-copy">Ask a question, or add an audio file to transcribe.</p>
          </div>
        ) : (
          <div className="messages">
            {messages.map((message, index) => (
              <article className={`message ${message.role}`} key={`${index}-${message.role}`}>
                <span className="message-label">{message.role === "user" ? "YOU" : "JARVIS"}</span>
                <p>{message.content}</p>
              </article>
            ))}
            {busy && <div className="typing" role="status">Jarvis is thinking…</div>}
            <div ref={endRef} />
          </div>
        )}
      </section>

      <section className="composer-wrap">
        {error && <p className="error" role="alert">{error}</p>}
        <form className="composer" onSubmit={sendMessage}>
          <textarea
            aria-label="Message Jarvis"
            placeholder="Message Jarvis…"
            rows={2}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
          />
          <div className="composer-tools">
            <div className="tools-left">
              <label className="file-button">
                <input
                  type="file"
                  accept="audio/*,.wav,.mp3,.m4a,.webm"
                  onChange={(event) => setAudioFile(event.target.files?.[0] ?? null)}
                />
                <span aria-hidden="true">＋</span> {audioFile ? audioFile.name : "Add audio"}
              </label>
              {audioFile && (
                <button className="subtle-button" type="button" onClick={() => void transcribeAudio()} disabled={transcribing}>
                  {transcribing ? "Transcribing…" : "Transcribe"}
                </button>
              )}
              <label className="voice-toggle">
                <input type="checkbox" checked={speakReplies} onChange={(event) => setSpeakReplies(event.target.checked)} />
                Speak replies
              </label>
            </div>
            <button className="send-button" type="submit" disabled={busy || !input.trim()} aria-label="Send message">
              <span aria-hidden="true">↑</span>
            </button>
          </div>
        </form>
        <p className="privacy-note">Local by default. Audio is processed by your configured speech provider.</p>
      </section>
    </main>
  );
}
