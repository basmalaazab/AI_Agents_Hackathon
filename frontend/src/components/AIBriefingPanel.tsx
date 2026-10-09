import React, { useState, useRef, useEffect } from "react";
import { Brain, Send, RefreshCw, Sparkles, ChevronRight, AlertCircle, WifiOff, Upload } from "lucide-react";
import { askAIAgent, fetchPromptSuggestions } from "../services/agentApi";
import type { ChatMessage, PromptSuggestion } from "../types/agent";
import { MarkdownContent } from "./MarkdownContent";

interface AIBriefingPanelProps {
  aiData: any;
  dateRange: string;
  sourceName?: string;
  onOpenFullModal: () => void;
  onOpenDataSources?: () => void;
  apiOffline: boolean;
}

/** Renders a compact AI briefing with a visible ask-question field, data-backed context, and suggested questions. */
export const AIBriefingPanel: React.FC<AIBriefingPanelProps> = ({
  aiData,
  dateRange,
  sourceName,
  onOpenFullModal,
  onOpenDataSources,
  apiOffline,
}) => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<ChatMessage | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<PromptSuggestion[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch context-aware suggested questions
  useEffect(() => {
    if (!apiOffline) {
      fetchPromptSuggestions(dateRange, sourceName)
        .then(setSuggestions)
        .catch(() => setSuggestions([]));
    }
  }, [dateRange, sourceName, apiOffline]);

  const handleAsk = async (q?: string) => {
    const text = (q || question).trim();
    if (!text || isSending || apiOffline) return;
    setIsSending(true);
    setSendError(null);
    setAnswer(null);
    try {
      const res = await askAIAgent(text, dateRange, sourceName, [], false);
      setAnswer({
        id: `ans-${Date.now()}`,
        role: "assistant",
        content: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        intent: res.intent,
        model_used: res.model_used,
        suggested_followups: res.suggested_followups,
      });
      setQuestion("");
    } catch (err: any) {
      setSendError(err.message || "Could not reach the analytics service.");
    } finally {
      setIsSending(false);
    }
  };

  // Build a brief business context from aiData
  const rev = aiData?.headline_kpis?.revenue?.current;
  const orders = aiData?.headline_kpis?.orders?.current;
  const hasBriefData = rev !== undefined && orders !== undefined;
  const needsData = !hasBriefData || (Number(rev) === 0 && Number(orders) === 0);

  const defaultSuggestions: PromptSuggestion[] = [
    { category: "revenue", prompt: "What drove revenue this period?", icon: "" },
    { category: "risk",    prompt: "Which products are underperforming?", icon: "" },
    { category: "growth",  prompt: "How can I grow repeat purchases?", icon: "" },
    { category: "churn",   prompt: "Which customers are at risk of churning?", icon: "" },
  ];
  const pills = suggestions.length > 0 ? suggestions.slice(0, 5) : defaultSuggestions;

  return (
    <div className="glass-card ai-briefing-panel" role="region" aria-label="AI Business Analyst">
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px", marginBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            aria-hidden="true"
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #246b4d, #24845a)",
              boxShadow: "0 2px 8px rgba(36, 107, 77, 0.25)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Brain size={20} color="#fff" />
          </div>
          <div>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>AI Business Analyst</h2>
            <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", margin: "2px 0 0" }}>
              Ask about sales, customers, products, or trends in the data you have imported.
            </p>
          </div>
        </div>

        <button
          className="btn btn-secondary"
          onClick={onOpenFullModal}
          style={{ fontSize: "0.8rem", padding: "7px 14px" }}
          aria-label="Open full AI Analyst with recommendations and diagnostics"
          title="Open full AI Analyst"
        >
          <Sparkles size={15} color="var(--accent-indigo)" />
          Open analyst workspace
          <ChevronRight size={15} />
        </button>
      </div>

      {/* Business context snapshot — only when data is available */}
      {hasBriefData && !apiOffline && (
        <div
          style={{
            display: "flex",
            gap: "20px",
            flexWrap: "wrap",
            padding: "12px 16px",
            borderRadius: "10px",
            background: "var(--card-subtle-bg)",
            border: "1px solid var(--card-subtle-border)",
            marginBottom: "16px",
            fontSize: "0.82rem",
          }}
        >
          <span>
            <span style={{ color: "var(--text-muted)" }}>Revenue (USD): </span>
            <strong>{typeof rev === "number" ? rev.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "–"}</strong>
          </span>
          <span>
            <span style={{ color: "var(--text-muted)" }}>Orders: </span>
            <strong>{typeof orders === "number" ? orders.toLocaleString() : "–"}</strong>
          </span>
          <span style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginLeft: "auto" }}>
            Period: <strong style={{ color: "var(--text-primary)" }}>{dateRange === "30d" ? "Last 30 days" : dateRange === "7d" ? "Last 7 days" : dateRange === "all" ? "All time" : dateRange}</strong>
            {sourceName ? ` · Source: ${sourceName}` : " · All sources"}
          </span>
        </div>
      )}

      {/* Offline notice */}
      {apiOffline && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 14px",
            borderRadius: "10px",
            background: "var(--card-subtle-bg)",
            border: "1px solid var(--card-border)",
            fontSize: "0.83rem",
            color: "var(--text-secondary)",
            marginBottom: "16px",
          }}
          role="status"
        >
          <WifiOff size={15} />
          Analytics service is not reachable. Connect the backend to use the AI Analyst.
        </div>
      )}

      {!apiOffline && needsData && (
        <div className="analyst-empty-state" role="status">
          <div className="analyst-empty-copy">
            <strong>Start with your business data</strong>
            <span>Upload a sales, customer, or product CSV, then come back for tailored insights.</span>
          </div>
          {onOpenDataSources && <button className="btn btn-primary" onClick={onOpenDataSources}><Upload size={15} /> Add data</button>}
        </div>
      )}

      {/* Question input */}
      <div className="ai-question-bar">
        <input
          ref={inputRef}
          type="text"
          className="ai-question-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          placeholder="e.g. Why did revenue drop last week? Which product should I push?"
          disabled={isSending || apiOffline || needsData}
          aria-label="Ask the AI Analyst a question about your business"
        />
        <button
          className="btn btn-primary"
          onClick={() => handleAsk()}
          disabled={isSending || !question.trim() || apiOffline || needsData}
          aria-label="Send question to AI Analyst"
          style={{ flexShrink: 0, background: "var(--accent-indigo)", color: "var(--accent-on-primary)", border: "none" }}
        >
          {isSending ? <RefreshCw size={16} className="animate-spin" aria-hidden="true" /> : <Send size={16} aria-hidden="true" />}
          {isSending ? "Analyzing…" : "Ask"}
        </button>
      </div>

      {/* Suggested questions */}
      {!answer && !isSending && !needsData && (
        <div className="ai-suggestion-pills" role="list" aria-label="Suggested questions">
          {pills.map((s, i) => (
            <button
              key={i}
              className="ai-pill"
              role="listitem"
              onClick={() => { setQuestion(s.prompt); handleAsk(s.prompt); }}
              disabled={isSending || apiOffline}
              title={s.prompt}
            >
              {s.prompt}
            </button>
          ))}
        </div>
      )}

      {/* Answer */}
      {sendError && (
        <div
          style={{
            marginTop: "12px",
            display: "flex",
            alignItems: "flex-start",
            gap: "8px",
            padding: "12px 16px",
            borderRadius: "10px",
            background: "var(--badge-red-bg)",
            border: "1px solid var(--accent-border-danger)",
            fontSize: "0.85rem",
            color: "var(--text-primary)",
          }}
          role="alert"
        >
          <AlertCircle size={16} color="var(--accent-rose)" style={{ flexShrink: 0, marginTop: "2px" }} />
          <div>
            <strong>Could not get an answer.</strong> {sendError}
          </div>
        </div>
      )}

      {answer && (
        <div
          style={{
            marginTop: "14px",
            padding: "16px 18px",
            borderRadius: "12px",
            background: "var(--chat-assistant-bg)",
            border: "1px solid var(--chat-assistant-border)",
            fontSize: "0.88rem",
            color: "var(--chat-assistant-text)",
            lineHeight: 1.6,
          }}
          role="region"
          aria-label="AI answer"
        >
          <MarkdownContent content={answer.content} />

          {/* Source/metadata footer */}
          <div style={{ marginTop: "10px", paddingTop: "8px", borderTop: "1px solid var(--card-border)", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
            <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
              {answer.timestamp}
              {answer.intent ? ` · ${answer.intent.replaceAll("_", " ")}` : ""}
            </span>
            <button
              className="btn btn-secondary"
              onClick={onOpenFullModal}
              style={{ fontSize: "0.75rem", padding: "4px 10px" }}
              aria-label="Open full AI Analyst to explore more"
            >
              Explore more <ChevronRight size={13} />
            </button>
          </div>

          {/* Follow-up suggestions */}
          {answer.suggested_followups && answer.suggested_followups.length > 0 && (
            <div className="ai-suggestion-pills" style={{ marginTop: "10px" }}>
              {answer.suggested_followups.slice(0, 3).map((f, i) => (
                <button
                  key={i}
                  className="ai-pill"
                  onClick={() => { setAnswer(null); setQuestion(f); handleAsk(f); }}
                >
                  ↳ {f}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
