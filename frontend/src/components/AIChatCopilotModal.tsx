import React, { useState, useEffect, useRef } from "react";
import {
  X,
  Copy,
  Check,
  Bot,
  Sparkles,
  Send,
  Database,
  AlertTriangle,
  Lightbulb,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  ShieldCheck,
  Play,
} from "lucide-react";

import {
  streamAIAgent,
  fetchRecommendations,
  fetchDiagnoses,
  executeSafeSQL,
  fetchPromptSuggestions,
} from "../services/agentApi";
import type {
  ChatMessage,
  StrategicRecommendation,
  AnomalyDiagnosis,
  SQLResults,
  PromptSuggestion,
  AnalysisEvidence,
} from "../types/agent";
import { MarkdownContent } from "./MarkdownContent";

interface AIChatCopilotModalProps {
  isOpen: boolean;
  onClose: () => void;
  aiData: any;
  dateRange: string;
  sourceName?: string;
}

const modelLabel = (model?: string) => {
  if (model === "gpt-4o-mini") return "OpenAI GPT-4o mini";
  if (model === "gemini-3.8-flash") return "Gemini 3.8 Flash";
  if (model === "built-in-analyst") return "Built-in analyst";
  return model?.replaceAll("_", " ") ?? "";
};

const evidenceDate = (value: string | null) => value ? new Date(value).toLocaleDateString() : null;

const EvidenceCard: React.FC<{ evidence: AnalysisEvidence }> = ({ evidence }) => <div className={`ai-evidence ${evidence.sufficiency.level}`}>
  <div className="ai-evidence-heading"><ShieldCheck size={13} /><strong>Analysis based on your data</strong><span>{evidence.sufficiency.level === "sufficient" ? "Data available" : evidence.sufficiency.level === "limited" ? "Limited sample" : "Not enough data"}</span></div>
  <div className="ai-evidence-facts">
    <span><b>Period</b> {evidence.period.label}{evidence.period.start ? ` · ${evidenceDate(evidence.period.start)}–${evidenceDate(evidence.period.end)}` : ""}</span>
    <span><b>Sources</b> {evidence.source_scope_label}{evidence.source_scope_label === "All company sources" && evidence.source_scope.length ? `: ${evidence.source_scope.join(", ")}` : ""}</span>
    <span><b>Records</b> {evidence.sample.completed_orders} completed orders · {evidence.sample.customer_records} customers</span>
  </div>
  {evidence.sufficiency.notes.map((note, index) => <p key={index}>{note}</p>)}
</div>;

export const AIChatCopilotModal: React.FC<AIChatCopilotModalProps> = ({
  isOpen,
  onClose,
  aiData,
  dateRange,
  sourceName,
}) => {
  const [activeTab, setActiveTab] = useState<"chat" | "recommendations" | "diagnose" | "sql" | "raw">("chat");

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [suggestions, setSuggestions] = useState<PromptSuggestion[]>([]);
  const [expandedSqlMsgId, setExpandedSqlMsgId] = useState<string | null>(null);

  // Recommendations State
  const [recommendations, setRecommendations] = useState<StrategicRecommendation[]>([]);
  const [execSummary, setExecSummary] = useState<string>("");
  const [recommendationEvidence, setRecommendationEvidence] = useState<AnalysisEvidence | null>(null);
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);

  // Diagnoses State
  const [diagnoses, setDiagnoses] = useState<AnomalyDiagnosis[]>([]);
  const [diagnosisEvidence, setDiagnosisEvidence] = useState<AnalysisEvidence | null>(null);
  const [isLoadingDiag, setIsLoadingDiag] = useState(false);

  // SQL Runner State
  const [sqlQuery, setSqlQuery] = useState("SELECT status, COUNT(*) AS orders, SUM(total_amount_usd) AS revenue FROM orders GROUP BY status;");
  const [sqlResult, setSqlResult] = useState<SQLResults | null>(null);
  const [sqlError, setSqlError] = useState<string | null>(null);
  const [isRunningSql, setIsRunningSql] = useState(false);

  // Raw Context Copy State
  const [copiedRaw, setCopiedRaw] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize Welcome Message and Suggestions
  useEffect(() => {
    if (isOpen) {
      if (messages.length === 0) {
        const rev = aiData?.headline_kpis?.revenue?.current || 0;
        const ords = aiData?.headline_kpis?.orders?.current || 0;
        const availableSources = aiData?.sales_performance?.revenue_by_platform?.map((item: { platform: string }) => item.platform) ?? [];
        const sourceScope = sourceName || (availableSources.length ? availableSources.join(", ") : "All company sources");
        setMessages([
          {
            id: "welcome-msg",
            role: "assistant",
            content: `Hello! I'm your AI Business Analyst.\n\nI can answer questions using your imported business data.\n\n- **Period:** ${dateRange}\n- **Sources:** ${sourceScope}\n- **Revenue (USD):** ${typeof rev === "number" ? rev.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "Not available"}\n- **Orders:** ${typeof ords === "number" ? ords.toLocaleString() : "Not available"}\n\nAsk about sales, customers, products, or trends. Orders with unsupported currencies are excluded from USD revenue totals.`,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            suggested_followups: [
              "What is our total revenue and sales trend?",
              "Which products are our top sellers?",
              "Why did revenue change this period?",
              "Give me 3 recommendations to increase revenue",
            ],
          },
        ]);
      }

      // Fetch quick prompt pills
      fetchPromptSuggestions(dateRange, sourceName)
        .then(setSuggestions)
        .catch((err) => console.debug("Suggestions fetch failed", err));
    }
  }, [isOpen, dateRange, sourceName, aiData]);

  // Scroll to bottom on new message
  useEffect(() => {
    if (activeTab === "chat") {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, activeTab]);

  // Load recommendations when tab is opened
  useEffect(() => {
    if (isOpen && activeTab === "recommendations") {
      setIsLoadingRecs(true);
      setRecommendations([]);
      setRecommendationEvidence(null);
      fetchRecommendations(dateRange, sourceName)
        .then((res) => {
          setRecommendations(res.recommendations);
          setExecSummary(res.executive_summary);
          setRecommendationEvidence(res.analysis_evidence ?? null);
        })
        .catch((err) => console.error("Recs load error", err))
        .finally(() => setIsLoadingRecs(false));
    }
  }, [isOpen, activeTab, dateRange, sourceName]);

  // Load diagnoses when tab is opened
  useEffect(() => {
    if (isOpen && activeTab === "diagnose") {
      setIsLoadingDiag(true);
      setDiagnoses([]);
      setDiagnosisEvidence(null);
      fetchDiagnoses(dateRange, sourceName)
        .then(items => { setDiagnoses(items); setDiagnosisEvidence(items[0]?.analysis_evidence ?? null); })
        .catch((err) => console.error("Diag load error", err))
        .finally(() => setIsLoadingDiag(false));
    }
  }, [isOpen, activeTab, dateRange, sourceName]);

  if (!isOpen) return null;

  // Send Question to AI Agent
  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputValue).trim();
    if (!query || isSending) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsSending(true);

    const aiMsgId = `ai-${Date.now()}`;
    const initialAiMsg: ChatMessage = {
      id: aiMsgId,
      role: "assistant",
      content: "...",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, initialAiMsg]);

    try {
      const history = messages.slice(-4).map((m) => ({ role: m.role, content: m.content }));
      let accumulatedContent = "";

      const res = await streamAIAgent(
        query,
        dateRange,
        sourceName,
        history,
        (chunk, modelUsed) => {
          accumulatedContent += chunk;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId
                ? { ...m, content: accumulatedContent, model_used: modelUsed || m.model_used }
                : m
            )
          );
        },
        (finalRes) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMsgId
                ? {
                    ...m,
                    content: finalRes.answer,
                    intent: finalRes.intent,
                    model_used: finalRes.model_used,
                    executed_sql: finalRes.executed_sql,
                    sql_results: finalRes.sql_results,
                    metrics_snapshot: finalRes.metrics_snapshot,
                    suggested_followups: finalRes.suggested_followups,
                    analysis_evidence: finalRes.analysis_evidence,
                  }
                : m
            )
          );
        }
      );

      // Ensure final state
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsgId
            ? {
                ...m,
                content: res.answer,
                intent: res.intent,
                model_used: res.model_used,
                executed_sql: res.executed_sql,
                sql_results: res.sql_results,
                metrics_snapshot: res.metrics_snapshot,
                suggested_followups: res.suggested_followups,
                analysis_evidence: res.analysis_evidence,
              }
            : m
        )
      );
    } catch (err: any) {
      setMessages((prev) => prev.filter((m) => m.id !== aiMsgId));
      const errorMsg: ChatMessage = {
        id: `ai-err-${Date.now()}`,
        role: "assistant",
        content: `⚠️ **Unable to complete request:** ${err.message || "Unknown error occurred"}. Please ensure backend API is running.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  // Run Custom Safe SQL
  const handleRunSQL = async () => {
    if (!sqlQuery.trim() || isRunningSql) return;
    setIsRunningSql(true);
    setSqlError(null);
    setSqlResult(null);

    try {
      const res = await executeSafeSQL(sqlQuery.trim());
      setSqlResult(res);
    } catch (err: any) {
      setSqlError(err.message || "Failed to execute query");
    } finally {
      setIsRunningSql(false);
    }
  };

  const handleCopyRaw = () => {
    navigator.clipboard.writeText(JSON.stringify(aiData, null, 2));
    setCopiedRaw(true);
    setTimeout(() => setCopiedRaw(false), 2000);
  };

  return (
    <div
      role="presentation"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.8)",
        backdropFilter: "blur(10px)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="AI Business Analyst"
        className="glass-card animate-fade-in"
        style={{
          width: "100%",
          maxWidth: "960px",
          height: "90vh",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          borderRadius: "20px",
          border: "1px solid var(--accent-indigo)",
          boxShadow: "0 20px 50px rgba(0,0,0,0.5)",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 24px",
            borderBottom: "1px solid var(--card-border)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            background: "var(--modal-sub-header)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "12px",
                background: "linear-gradient(135deg, var(--accent-indigo), var(--accent-emerald))",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 14px rgba(36, 107, 77, 0.2)",
              }}
            >
              <Bot size={22} color="#fff" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>
                  AI Business Analyst
                </h3>
                <span
                  style={{
                    fontSize: "0.7rem",
                    padding: "2px 8px",
                    borderRadius: "10px",
                    background: "var(--badge-green-bg)",
                    color: "var(--badge-green-text)",
                    fontWeight: 600,
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                >
                  <ShieldCheck size={12} /> Read-only analysis
                </span>
              </div>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "2px 0 0" }}>
                Ask questions, review trends, and explore recommendations based on your data.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close AI Business Analyst"
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-muted)",
              cursor: "pointer",
              padding: "4px",
              borderRadius: "8px",
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: "flex",
            borderBottom: "1px solid var(--card-border)",
            background: "var(--modal-tab-bar)",
            padding: "0 16px",
            gap: "8px",
          }}
        >
          <button
            onClick={() => setActiveTab("chat")}
            style={{
              padding: "12px 16px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "chat" ? "2px solid var(--accent-indigo)" : "2px solid transparent",
              color: activeTab === "chat" ? "var(--accent-indigo)" : "var(--text-secondary)",
              fontWeight: activeTab === "chat" ? 600 : 500,
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <Sparkles size={16} color={activeTab === "chat" ? "var(--accent-indigo)" : "currentColor"} />
            Chat
          </button>

          <button
            onClick={() => setActiveTab("recommendations")}
            style={{
              padding: "12px 16px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "recommendations" ? "2px solid var(--accent-indigo)" : "2px solid transparent",
              color: activeTab === "recommendations" ? "var(--accent-indigo)" : "var(--text-secondary)",
              fontWeight: activeTab === "recommendations" ? 600 : 500,
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <Lightbulb size={16} color={activeTab === "recommendations" ? "var(--accent-amber)" : "currentColor"} />
            Recommendations
          </button>

          <button
            onClick={() => setActiveTab("diagnose")}
            style={{
              padding: "12px 16px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "diagnose" ? "2px solid var(--accent-indigo)" : "2px solid transparent",
              color: activeTab === "diagnose" ? "var(--accent-indigo)" : "var(--text-secondary)",
              fontWeight: activeTab === "diagnose" ? 600 : 500,
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <AlertTriangle size={16} color={activeTab === "diagnose" ? "var(--accent-rose)" : "currentColor"} />
            Alerts & diagnosis
          </button>

        </div>

        {/* Tab 1: AI Analyst Chat */}
        {activeTab === "chat" && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            {/* Quick Prompt Suggestions */}
            {suggestions.length > 0 && (
              <div
                style={{
                  padding: "10px 20px",
                  display: "flex",
                  gap: "8px",
                  overflowX: "auto",
                  borderBottom: "1px solid var(--card-border)",
                  background: "var(--modal-tab-bar)",
                }}
              >
                {suggestions.map((s, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(s.prompt)}
                    style={{
                      whiteSpace: "nowrap",
                      padding: "6px 12px",
                      borderRadius: "16px",
                      border: "1px solid var(--pill-border)",
                      background: "var(--pill-bg)",
                      color: "var(--pill-text)",
                      fontSize: "0.75rem",
                      fontWeight: 500,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                  >
                    <Sparkles size={12} color="var(--accent-indigo)" />
                    {s.prompt}
                  </button>
                ))}
              </div>
            )}

            {/* Message Thread */}
            <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px", display: "flex", flexDirection: "column", gap: "16px" }}>
              {messages.map((m) => {
                const isAssistant = m.role === "assistant";
                return (
                  <div
                    key={m.id}
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      alignItems: isAssistant ? "flex-start" : "flex-end",
                    }}
                  >
                    <div
                      style={{
                        maxWidth: "85%",
                        padding: "14px 18px",
                        borderRadius: isAssistant ? "18px 18px 18px 4px" : "18px 18px 4px 18px",
                        background: isAssistant ? "var(--chat-assistant-bg)" : "linear-gradient(135deg, var(--accent-indigo), var(--accent-emerald))",
                        border: isAssistant ? "1px solid var(--chat-assistant-border)" : "none",
                        color: isAssistant ? "var(--chat-assistant-text)" : "#ffffff",
                        fontSize: "0.88rem",
                        lineHeight: 1.55,
                        boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
                      }}
                    >
                      {isAssistant ? (
                        <MarkdownContent content={m.content} />
                      ) : (
                        <div style={{ whiteSpace: "pre-wrap" }}>{m.content}</div>
                      )}

                      {/* Collapsible Executed SQL */}
                      {m.executed_sql && (
                        <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px solid var(--card-border)" }}>
                          <button
                            onClick={() => setExpandedSqlMsgId(expandedSqlMsgId === m.id ? null : m.id)}
                            style={{
                              background: "transparent",
                              border: "none",
                              color: "var(--accent-indigo)",
                              fontSize: "0.75rem",
                              fontWeight: 600,
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                              padding: 0,
                            }}
                          >
                            <Database size={13} />
                            {expandedSqlMsgId === m.id ? "Hide Generated Query" : "View Generated Query (not executed)"}
                            {expandedSqlMsgId === m.id ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                          </button>

                          {expandedSqlMsgId === m.id && (
                            <pre
                              style={{
                                marginTop: "8px",
                                background: "var(--code-bg)",
                                padding: "10px",
                                borderRadius: "8px",
                                fontSize: "0.75rem",
                                color: "var(--code-text)",
                                overflowX: "auto",
                              }}
                            >
                              {m.executed_sql}
                            </pre>
                          )}
                        </div>
                      )}
                    </div>

                    {isAssistant && m.analysis_evidence && <EvidenceCard evidence={m.analysis_evidence} />}

                    {/* Followup suggestions */}
                    {isAssistant && m.suggested_followups && m.suggested_followups.length > 0 && (
                      <div style={{ marginTop: "8px", display: "flex", flexWrap: "wrap", gap: "6px" }}>
                        {m.suggested_followups.map((f, fIdx) => (
                          <button
                            key={fIdx}
                            onClick={() => handleSendMessage(f)}
                            style={{
                              padding: "4px 10px",
                              borderRadius: "12px",
                              border: "1px solid var(--card-border)",
                              background: "var(--card-subtle-bg)",
                              color: "var(--text-secondary)",
                              fontSize: "0.75rem",
                              cursor: "pointer",
                            }}
                          >
                            ↳ {f}
                          </button>
                        ))}
                      </div>
                    )}

                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "4px" }}>
                      {m.timestamp} {m.model_used && `• ${modelLabel(m.model_used)}`}
                    </span>
                  </div>
                );
              })}

              {isSending && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--accent-indigo)", fontSize: "0.85rem" }}>
                  <RefreshCw size={16} className="animate-spin" />
                  <span>AI Agent is analyzing database metrics and reasoning...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <div
              style={{
                padding: "16px 24px",
                borderTop: "1px solid var(--card-border)",
                background: "var(--modal-sub-header)",
                display: "flex",
                gap: "12px",
              }}
            >
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                placeholder="Ask about sales, products, customers, or trends…"
                disabled={isSending}
                style={{
                  flex: 1,
                  padding: "12px 16px",
                  borderRadius: "12px",
                  border: "1px solid var(--input-border)",
                  background: "var(--input-bg)",
                  color: "var(--input-color)",
                  fontSize: "0.9rem",
                  outline: "none",
                }}
              />
              <button
                className="btn btn-primary"
                onClick={() => handleSendMessage()}
                disabled={isSending || !inputValue.trim()}
                style={{ padding: "0 20px" }}
              >
                <Send size={18} />
                Send
              </button>
            </div>
          </div>
        )}

        {/* Tab 2: Strategic Action Plan */}
        {activeTab === "recommendations" && (
          <div style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
            {isLoadingRecs ? (
              <div style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)" }}>
                <RefreshCw size={24} className="animate-spin" style={{ margin: "0 auto 12px" }} />
                <p>Generating concrete business recommendations based on database KPIs...</p>
              </div>
            ) : (
              <>
                {recommendationEvidence && <EvidenceCard evidence={recommendationEvidence} />}
                {execSummary && (
                  <div
                    style={{
                      padding: "16px 20px",
                      borderRadius: "14px",
                      background: "var(--pill-bg)",
                      border: "1px solid var(--pill-border)",
                      fontSize: "0.9rem",
                      color: "var(--text-primary)",
                      lineHeight: 1.6,
                    }}
                  >
                    <strong>🎯 Executive Summary:</strong> {execSummary}
                  </div>
                )}

                <div style={{ display: "grid", gap: "16px" }}>
                  {recommendations.map((rec) => (
                    <div
                      key={rec.id}
                      style={{
                        padding: "20px",
                        borderRadius: "16px",
                        background: "var(--card-subtle-bg)",
                        border: "1px solid var(--card-subtle-border)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px", marginBottom: "8px" }}>
                        <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>{rec.title}</h4>
                        <span
                          style={{
                            fontSize: "0.75rem",
                            padding: "3px 10px",
                            borderRadius: "12px",
                            fontWeight: 700,
                            background:
                              rec.priority === "HIGH"
                                ? "var(--badge-red-bg)"
                                : rec.priority === "MEDIUM"
                                ? "var(--badge-amber-bg)"
                                : "var(--pill-bg)",
                            color:
                              rec.priority === "HIGH"
                                ? "var(--badge-red-text)"
                                : rec.priority === "MEDIUM"
                                ? "var(--badge-amber-text)"
                                : "var(--text-secondary)",
                          }}
                        >
                          {rec.priority} PRIORITY
                        </span>
                      </div>

                      <div style={{ display: "flex", gap: "16px", fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "12px" }}>
                        <span>📁 Category: <strong>{rec.category}</strong></span>
                        <span>⚡ Impact: <strong style={{ color: "var(--accent-emerald)" }}>{rec.expected_impact}</strong></span>
                        <span>⏱️ Effort: <strong>{rec.implementation_effort}</strong></span>
                      </div>

                      <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", fontStyle: "italic", marginBottom: "14px" }}>
                        📊 {rec.data_justification}
                      </p>

                      <div style={{ background: "var(--modal-tab-bar)", padding: "12px 16px", borderRadius: "10px", border: "1px solid var(--card-border)" }}>
                        <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
                          Action Checklist:
                        </div>
                        <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "0.85rem", color: "var(--text-primary)" }}>
                          {rec.action_steps.map((step, sIdx) => (
                            <li key={sIdx} style={{ marginBottom: "4px" }}>{step}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Tab 3: Anomaly Diagnosis */}
        {activeTab === "diagnose" && (
          <div style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
            {diagnosisEvidence && <EvidenceCard evidence={diagnosisEvidence} />}
            {isLoadingDiag ? (
              <div style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)" }}>
                <RefreshCw size={24} className="animate-spin" style={{ margin: "0 auto 12px" }} />
                <p>Investigating root causes of operational alerts...</p>
              </div>
            ) : diagnoses.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px", color: "var(--accent-emerald)" }}>
                <CheckCircle2 size={36} style={{ margin: "0 auto 12px" }} />
                <h3>No major anomalies found</h3>
                <p style={{ color: "var(--text-secondary)" }}>No major anomalies were detected for this period.</p>
              </div>
            ) : (
              diagnoses.map((diag) => (
                <div
                  key={diag.id}
                  style={{
                    padding: "20px",
                    borderRadius: "16px",
                    background: "var(--card-subtle-bg)",
                    border: diag.severity === "danger" ? "1px solid var(--accent-border-danger)" : "1px solid var(--accent-border-warning)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                    <AlertTriangle size={20} color={diag.severity === "danger" ? "var(--accent-rose)" : "var(--accent-amber)"} />
                    <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>{diag.title}</h4>
                  </div>

                  <p style={{ fontSize: "0.9rem", color: "var(--text-primary)", marginBottom: "14px" }}>{diag.summary}</p>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "14px" }}>
                    <div style={{ background: "var(--modal-tab-bar)", padding: "12px", borderRadius: "10px", border: "1px solid var(--card-border)" }}>
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--accent-rose)", marginBottom: "4px" }}>
                        Possible causes:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                        {diag.root_causes.map((rc, rIdx) => (
                          <li key={rIdx}>{rc}</li>
                        ))}
                      </ul>
                    </div>

                    <div style={{ background: "var(--modal-tab-bar)", padding: "12px", borderRadius: "10px", border: "1px solid var(--card-border)" }}>
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--accent-emerald)", marginBottom: "4px" }}>
                        Suggested next steps:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                        {diag.mitigation_actions.map((act, aIdx) => (
                          <li key={aIdx}>{act}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab 4: Safe SQL Sandbox */}
        {activeTab === "sql" && (
          <div style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ padding: 20, borderRadius: 12, background: "var(--chat-assistant-bg)", color: "var(--text-secondary)" }}>
              <strong style={{ color: "var(--text-primary)" }}>Direct SQL is currently unavailable.</strong>
              <p style={{ marginBottom: 0 }}>Company data is isolated by workspace. Use the dashboard and AI Analyst for workspace-scoped business questions.</p>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <textarea
                value={sqlQuery}
                onChange={(e) => setSqlQuery(e.target.value)}
                disabled
                rows={4}
                style={{
                  width: "100%",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  background: "var(--code-bg)",
                  color: "var(--code-text)",
                  fontFamily: "monospace",
                  fontSize: "0.85rem",
                  border: "1px solid var(--input-border)",
                  outline: "none",
                }}
              />
              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <button
                  className="btn btn-primary"
                  onClick={handleRunSQL}
                  disabled
                  style={{ fontSize: "0.85rem", padding: "6px 16px" }}
                >
                  <Play size={14} />
                  {isRunningSql ? "Running..." : "Execute Query"}
                </button>
              </div>
            </div>

            {sqlError && (
              <div style={{ padding: "12px", borderRadius: "10px", background: "var(--badge-red-bg)", border: "1px solid var(--accent-border-danger)", color: "var(--badge-red-text)", fontSize: "0.85rem" }}>
                ⚠️ {sqlError}
              </div>
            )}

            {sqlResult && (
              <div style={{ marginTop: "12px" }}>
                <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "8px" }}>
                  Returned {sqlResult.row_count} row(s):
                </div>
                <div style={{ overflowX: "auto", maxHeight: "300px", borderRadius: "10px", border: "1px solid var(--card-border)" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", textAlign: "left" }}>
                    <thead>
                      <tr style={{ background: "var(--modal-tab-bar)", color: "var(--accent-indigo)" }}>
                        {sqlResult.columns.map((col, cIdx) => (
                          <th key={cIdx} style={{ padding: "8px 12px", borderBottom: "1px solid var(--card-border)" }}>
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sqlResult.rows.map((r, rIdx) => (
                        <tr key={rIdx} style={{ borderBottom: "1px solid var(--card-border)" }}>
                          {sqlResult.columns.map((col, cIdx) => (
                            <td key={cIdx} style={{ padding: "8px 12px", color: "var(--text-primary)" }}>
                              {String(r[col] ?? "")}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 5: Raw AI Context Inspector */}
        {activeTab === "raw" && (
          <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px" }}>
            <div style={{ marginBottom: "16px", padding: "12px 16px", background: "var(--pill-bg)", borderRadius: "10px", border: "1px solid var(--pill-border)", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              💡 <strong>Unified Payload:</strong> Exposed via <code>GET /api/v1/analytics/ai-context</code>. The AI Agent feeds this exact snapshot into its analytical engine.
            </div>

            <div style={{ position: "relative" }}>
              <button
                onClick={handleCopyRaw}
                className="btn btn-secondary"
                style={{ position: "absolute", top: "12px", right: "12px", fontSize: "0.75rem", padding: "4px 10px", zIndex: 10 }}
              >
                {copiedRaw ? <Check size={14} color="var(--accent-emerald)" /> : <Copy size={14} />}
                {copiedRaw ? "Copied!" : "Copy JSON"}
              </button>

              <pre
                style={{
                  background: "var(--code-bg)",
                  padding: "16px",
                  borderRadius: "12px",
                  fontSize: "0.8rem",
                  color: "var(--code-text)",
                  fontFamily: "monospace",
                  overflowX: "auto",
                  maxHeight: "480px",
                  border: "1px solid var(--card-border)",
                }}
              >
                {JSON.stringify(aiData, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={{ padding: "14px 24px", borderTop: "1px solid var(--card-border)", display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--modal-sub-header)" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            AI Analyst · Business insights from your company workspace
          </span>
          <button className="btn btn-primary" onClick={onClose} style={{ fontSize: "0.85rem" }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
