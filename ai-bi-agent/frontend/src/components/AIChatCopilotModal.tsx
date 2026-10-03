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
  FileText,
  Play,
} from "lucide-react";

import {
  askAIAgent,
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
} from "../types/agent";

interface AIChatCopilotModalProps {
  isOpen: boolean;
  onClose: () => void;
  aiData: any;
  dateRange: string;
  sourceName?: string;
}

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
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);

  // Diagnoses State
  const [diagnoses, setDiagnoses] = useState<AnomalyDiagnosis[]>([]);
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
        setMessages([
          {
            id: "welcome-msg",
            role: "assistant",
            content: `👋 **Hello! I'm your AI Business Intelligence Agent.**\n\nI have structured, real-time access to your operational business data for period \`${dateRange}\`.\n\n- **Current Revenue:** $${rev.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}\n- **Completed Orders:** ${ords}\n- **Security Guarantee:** Safe, strictly read-only SQL querying with automated guardrails.\n\nAsk me any question below or click one of the suggested prompts!`,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            suggested_followups: [
              "What is our total revenue and sales trend?",
              "Which products are our top sellers?",
              "Why did revenue decline this period?",
              "Give me 3 prioritized recommendations to increase sales",
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
    if (isOpen && activeTab === "recommendations" && recommendations.length === 0) {
      setIsLoadingRecs(true);
      fetchRecommendations(dateRange, sourceName)
        .then((res) => {
          setRecommendations(res.recommendations);
          setExecSummary(res.executive_summary);
        })
        .catch((err) => console.error("Recs load error", err))
        .finally(() => setIsLoadingRecs(false));
    }
  }, [isOpen, activeTab, dateRange, sourceName, recommendations.length]);

  // Load diagnoses when tab is opened
  useEffect(() => {
    if (isOpen && activeTab === "diagnose" && diagnoses.length === 0) {
      setIsLoadingDiag(true);
      fetchDiagnoses(dateRange, sourceName)
        .then(setDiagnoses)
        .catch((err) => console.error("Diag load error", err))
        .finally(() => setIsLoadingDiag(false));
    }
  }, [isOpen, activeTab, dateRange, sourceName, diagnoses.length]);

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

    try {
      const history = messages.slice(-4).map((m) => ({ role: m.role, content: m.content }));
      const res = await askAIAgent(query, dateRange, sourceName, history, true);

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: res.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        intent: res.intent,
        model_used: res.model_used,
        executed_sql: res.executed_sql,
        sql_results: res.sql_results,
        metrics_snapshot: res.metrics_snapshot,
        suggested_followups: res.suggested_followups,
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
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
            background: "rgba(15, 23, 42, 0.7)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "12px",
                background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 16px rgba(99, 102, 241, 0.4)",
              }}
            >
              <Bot size={22} color="#fff" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 700, margin: 0 }}>
                  Person 3 — AI Business Intelligence Agent
                </h3>
                <span
                  style={{
                    fontSize: "0.7rem",
                    padding: "2px 8px",
                    borderRadius: "10px",
                    background: "rgba(16, 185, 129, 0.2)",
                    color: "#34d399",
                    fontWeight: 600,
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                  }}
                >
                  <ShieldCheck size={12} /> Safe Read-Only
                </span>
              </div>
              <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", margin: "2px 0 0" }}>
                Autonomous reasoning, root-cause anomaly diagnosis & actionable recommendations
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
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
            background: "rgba(10, 15, 29, 0.5)",
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
              color: activeTab === "chat" ? "#fff" : "var(--text-secondary)",
              fontWeight: activeTab === "chat" ? 600 : 500,
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <Sparkles size={16} color={activeTab === "chat" ? "var(--accent-indigo)" : "currentColor"} />
            AI Copilot Chat
          </button>

          <button
            onClick={() => setActiveTab("recommendations")}
            style={{
              padding: "12px 16px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "recommendations" ? "2px solid var(--accent-indigo)" : "2px solid transparent",
              color: activeTab === "recommendations" ? "#fff" : "var(--text-secondary)",
              fontWeight: activeTab === "recommendations" ? 600 : 500,
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <Lightbulb size={16} color={activeTab === "recommendations" ? "#fbbf24" : "currentColor"} />
            Strategic Action Plan
          </button>

          <button
            onClick={() => setActiveTab("diagnose")}
            style={{
              padding: "12px 16px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "diagnose" ? "2px solid var(--accent-indigo)" : "2px solid transparent",
              color: activeTab === "diagnose" ? "#fff" : "var(--text-secondary)",
              fontWeight: activeTab === "diagnose" ? 600 : 500,
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <AlertTriangle size={16} color={activeTab === "diagnose" ? "#f43f5e" : "currentColor"} />
            Anomaly Diagnosis
          </button>

          <button
            onClick={() => setActiveTab("sql")}
            style={{
              padding: "12px 16px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "sql" ? "2px solid var(--accent-indigo)" : "2px solid transparent",
              color: activeTab === "sql" ? "#fff" : "var(--text-secondary)",
              fontWeight: activeTab === "sql" ? 600 : 500,
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <Database size={16} color={activeTab === "sql" ? "#38bdf8" : "currentColor"} />
            Safe SQL Runner
          </button>

          <button
            onClick={() => setActiveTab("raw")}
            style={{
              padding: "12px 16px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "raw" ? "2px solid var(--accent-indigo)" : "2px solid transparent",
              color: activeTab === "raw" ? "#fff" : "var(--text-secondary)",
              fontWeight: activeTab === "raw" ? 600 : 500,
              fontSize: "0.85rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              marginLeft: "auto",
            }}
          >
            <FileText size={16} color={activeTab === "raw" ? "var(--accent-indigo)" : "currentColor"} />
            Raw Context (Person 2)
          </button>
        </div>

        {/* Tab 1: AI Copilot Chat */}
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
                  borderBottom: "1px solid rgba(255,255,255,0.05)",
                  background: "rgba(15, 23, 42, 0.4)",
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
                      border: "1px solid rgba(99, 102, 241, 0.3)",
                      background: "rgba(99, 102, 241, 0.1)",
                      color: "#cbd5e1",
                      fontSize: "0.75rem",
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
                        background: isAssistant ? "rgba(30, 41, 59, 0.7)" : "linear-gradient(135deg, #4f46e5, #7c3aed)",
                        border: isAssistant ? "1px solid rgba(255, 255, 255, 0.08)" : "none",
                        color: "#fff",
                        fontSize: "0.88rem",
                        lineHeight: 1.55,
                      }}
                    >
                      {/* Markdown text formatted with simple rules */}
                      <div style={{ whiteSpace: "pre-wrap" }}>
                        {m.content}
                      </div>

                      {/* Collapsible Executed SQL */}
                      {m.executed_sql && (
                        <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
                          <button
                            onClick={() => setExpandedSqlMsgId(expandedSqlMsgId === m.id ? null : m.id)}
                            style={{
                              background: "transparent",
                              border: "none",
                              color: "#38bdf8",
                              fontSize: "0.75rem",
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                              padding: 0,
                            }}
                          >
                            <Database size={13} />
                            {expandedSqlMsgId === m.id ? "Hide Safe SQL Query" : "View Executed Read-Only SQL"}
                            {expandedSqlMsgId === m.id ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                          </button>

                          {expandedSqlMsgId === m.id && (
                            <pre
                              style={{
                                marginTop: "8px",
                                background: "#090d16",
                                padding: "10px",
                                borderRadius: "8px",
                                fontSize: "0.75rem",
                                color: "#34d399",
                                overflowX: "auto",
                              }}
                            >
                              {m.executed_sql}
                            </pre>
                          )}
                        </div>
                      )}
                    </div>

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
                              border: "1px solid rgba(255,255,255,0.1)",
                              background: "rgba(255,255,255,0.04)",
                              color: "#94a3b8",
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
                      {m.timestamp} {m.model_used && `• ${m.model_used}`}
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
                background: "rgba(15, 23, 42, 0.6)",
                display: "flex",
                gap: "12px",
              }}
            >
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                placeholder="Ask anything about sales, products, anomalies, churn, or safe SQL..."
                disabled={isSending}
                style={{
                  flex: 1,
                  padding: "12px 16px",
                  borderRadius: "12px",
                  border: "1px solid var(--card-border)",
                  background: "rgba(0, 0, 0, 0.4)",
                  color: "#fff",
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
                {execSummary && (
                  <div
                    style={{
                      padding: "16px 20px",
                      borderRadius: "14px",
                      background: "rgba(99, 102, 241, 0.12)",
                      border: "1px solid rgba(99, 102, 241, 0.3)",
                      fontSize: "0.9rem",
                      color: "#e2e8f0",
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
                        background: "rgba(30, 41, 59, 0.5)",
                        border: "1px solid rgba(255, 255, 255, 0.08)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "12px", marginBottom: "8px" }}>
                        <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0 }}>{rec.title}</h4>
                        <span
                          style={{
                            fontSize: "0.75rem",
                            padding: "3px 10px",
                            borderRadius: "12px",
                            fontWeight: 700,
                            background:
                              rec.priority === "HIGH"
                                ? "rgba(244, 63, 94, 0.2)"
                                : rec.priority === "MEDIUM"
                                ? "rgba(251, 191, 36, 0.2)"
                                : "rgba(148, 163, 184, 0.2)",
                            color:
                              rec.priority === "HIGH"
                                ? "#f43f5e"
                                : rec.priority === "MEDIUM"
                                ? "#fbbf24"
                                : "#cbd5e1",
                          }}
                        >
                          {rec.priority} PRIORITY
                        </span>
                      </div>

                      <div style={{ display: "flex", gap: "16px", fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "12px" }}>
                        <span>📁 Category: <strong>{rec.category}</strong></span>
                        <span>⚡ Impact: <strong style={{ color: "#34d399" }}>{rec.expected_impact}</strong></span>
                        <span>⏱️ Effort: <strong>{rec.implementation_effort}</strong></span>
                      </div>

                      <p style={{ fontSize: "0.85rem", color: "#94a3b8", fontStyle: "italic", marginBottom: "14px" }}>
                        📊 {rec.data_justification}
                      </p>

                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px 16px", borderRadius: "10px" }}>
                        <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#cbd5e1", marginBottom: "6px" }}>
                          Action Checklist:
                        </div>
                        <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "0.85rem", color: "#e2e8f0" }}>
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
            {isLoadingDiag ? (
              <div style={{ textAlign: "center", padding: "40px", color: "var(--text-secondary)" }}>
                <RefreshCw size={24} className="animate-spin" style={{ margin: "0 auto 12px" }} />
                <p>Investigating root causes of operational alerts...</p>
              </div>
            ) : diagnoses.length === 0 ? (
              <div style={{ textAlign: "center", padding: "40px", color: "#34d399" }}>
                <CheckCircle2 size={36} style={{ margin: "0 auto 12px" }} />
                <h3>All Business Metrics Stable</h3>
                <p style={{ color: "var(--text-secondary)" }}>No severe anomalies or drops detected for this period.</p>
              </div>
            ) : (
              diagnoses.map((diag) => (
                <div
                  key={diag.id}
                  style={{
                    padding: "20px",
                    borderRadius: "16px",
                    background: "rgba(30, 41, 59, 0.5)",
                    border: diag.severity === "danger" ? "1px solid rgba(244, 63, 94, 0.4)" : "1px solid rgba(251, 191, 36, 0.4)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                    <AlertTriangle size={20} color={diag.severity === "danger" ? "#f43f5e" : "#fbbf24"} />
                    <h4 style={{ fontSize: "1.05rem", fontWeight: 700, margin: 0 }}>{diag.title}</h4>
                  </div>

                  <p style={{ fontSize: "0.9rem", color: "#e2e8f0", marginBottom: "14px" }}>{diag.summary}</p>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "14px" }}>
                    <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "10px" }}>
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#f87171", marginBottom: "4px" }}>
                        Root Causes Identified:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "0.82rem", color: "#cbd5e1" }}>
                        {diag.root_causes.map((rc, rIdx) => (
                          <li key={rIdx}>{rc}</li>
                        ))}
                      </ul>
                    </div>

                    <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "10px" }}>
                      <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#34d399", marginBottom: "4px" }}>
                        Recommended Mitigation Steps:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "0.82rem", color: "#cbd5e1" }}>
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
            <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
              🔒 <strong>Safe Read-Only SQL Console:</strong> You can query clean business tables (<code>orders</code>, <code>order_items</code>, <code>customers</code>, <code>products</code>). Mutation and DDL queries are automatically blocked by the safety guardrail.
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <textarea
                value={sqlQuery}
                onChange={(e) => setSqlQuery(e.target.value)}
                rows={4}
                style={{
                  width: "100%",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  background: "#090d16",
                  color: "#38bdf8",
                  fontFamily: "monospace",
                  fontSize: "0.85rem",
                  border: "1px solid rgba(255,255,255,0.1)",
                  outline: "none",
                }}
              />
              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <button
                  className="btn btn-primary"
                  onClick={handleRunSQL}
                  disabled={isRunningSql || !sqlQuery.trim()}
                  style={{ fontSize: "0.85rem", padding: "6px 16px" }}
                >
                  <Play size={14} />
                  {isRunningSql ? "Running..." : "Execute Query"}
                </button>
              </div>
            </div>

            {sqlError && (
              <div style={{ padding: "12px", borderRadius: "10px", background: "rgba(244, 63, 94, 0.15)", border: "1px solid rgba(244, 63, 94, 0.4)", color: "#f87171", fontSize: "0.85rem" }}>
                ⚠️ {sqlError}
              </div>
            )}

            {sqlResult && (
              <div style={{ marginTop: "12px" }}>
                <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "8px" }}>
                  Returned {sqlResult.row_count} row(s):
                </div>
                <div style={{ overflowX: "auto", maxHeight: "300px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.08)" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem", textAlign: "left" }}>
                    <thead>
                      <tr style={{ background: "rgba(15, 23, 42, 0.9)", color: "var(--accent-indigo)" }}>
                        {sqlResult.columns.map((col, cIdx) => (
                          <th key={cIdx} style={{ padding: "8px 12px", borderBottom: "1px solid rgba(255,255,255,0.1)" }}>
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sqlResult.rows.map((r, rIdx) => (
                        <tr key={rIdx} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                          {sqlResult.columns.map((col, cIdx) => (
                            <td key={cIdx} style={{ padding: "8px 12px", color: "#e2e8f0" }}>
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
            <div style={{ marginBottom: "16px", padding: "12px 16px", background: "rgba(99, 102, 241, 0.1)", borderRadius: "10px", border: "1px solid rgba(99, 102, 241, 0.2)", fontSize: "0.85rem", color: "#cbd5e1" }}>
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
                  background: "#090d16",
                  padding: "16px",
                  borderRadius: "12px",
                  fontSize: "0.8rem",
                  color: "#34d399",
                  fontFamily: "monospace",
                  overflowX: "auto",
                  maxHeight: "480px",
                  border: "1px solid rgba(255,255,255,0.06)",
                }}
              >
                {JSON.stringify(aiData, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={{ padding: "14px 24px", borderTop: "1px solid var(--card-border)", display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(15, 23, 42, 0.7)" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Powered by Person 3 AI Agent • Safe SQL & Analytical Reasoning Engine
          </span>
          <button className="btn btn-primary" onClick={onClose} style={{ fontSize: "0.85rem" }}>
            Close Agent
          </button>
        </div>
      </div>
    </div>
  );
};
