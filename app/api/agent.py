"""
AI Agent API Router — Person 3 (AI Business Intelligence Agent).

Exposes:
- POST /api/v1/agent/query          : Natural language Q&A and business reasoning
- POST /api/v1/agent/recommendations: Strategic, prioritized recommendations
- POST /api/v1/agent/diagnose       : Root-cause anomaly diagnosis
- POST /api/v1/agent/sql            : Safe read-only SQL query sandbox
- GET  /api/v1/agent/suggestions    : Contextual quick prompt pills
- GET  /api/v1/agent/capabilities   : Agent capabilities & schema inspection
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app.services.ai_agent_service import AIAgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["AI Business Intelligence Agent (Person 3)"], dependencies=[Depends(get_current_user)])


# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------

class AgentQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question about business metrics, products, or trends", min_length=2)
    date_range: str = Field(default="30d", description="Analysis time window: '7d', '30d', '90d', 'all'")
    source_name: Optional[str] = Field(default=None, description="Optional filter by platform (e.g. 'csv_upload', 'mock_ecommerce_api')")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default=None, description="Optional prior conversation turns")
    include_sql: bool = Field(default=True, description="Whether to include executed SQL and raw data results")


class RecommendationsRequest(BaseModel):
    date_range: str = Field(default="30d")
    source_name: Optional[str] = Field(default=None)
    category_focus: Optional[str] = Field(default=None, description="Optional focus area ('revenue', 'retention', 'catalog', 'operations')")


class DiagnoseRequest(BaseModel):
    date_range: str = Field(default="30d")
    source_name: Optional[str] = Field(default=None)
    alert_id: Optional[str] = Field(default=None, description="Optional specific alert identifier to diagnose")


class SQLSandboxRequest(BaseModel):
    query: str = Field(..., description="Read-only SQL SELECT query against clean tables")
    max_rows: int = Field(default=50, ge=1, le=100, description="Max rows to return (capped at 100)")


class InventoryReorderDraftRequest(BaseModel):
    product_name: str = Field(..., min_length=1)
    product_sku: Optional[str] = None
    source_name: str = Field(..., min_length=1)
    supplier_lead_time_days: int = Field(..., ge=0, le=180)
    target_cover_days: int = Field(default=14, ge=1, le=365)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/query", summary="Natural Language Question Answering & AI BI Reasoning")
def query_agent(
    req: AgentQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Person 3 AI Agent natural language query endpoint.
    Translates user questions into metric calculations, safe SQL executions,
    and business recommendations.
    """
    svc = AIAgentService(db)
    result = svc.process_query(
        query=req.query,
        date_range=req.date_range,
        source_name=req.source_name,
        conversation_history=req.conversation_history,
        include_sql=req.include_sql,
    )
    return result


@router.post("/query/stream", summary="Stream Natural Language Q&A Response via Server-Sent Events (SSE)")
def stream_query(
    req: AgentQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Executes business query reasoning and streams the response token by token via SSE.
    """
    import json
    import queue
    import threading
    from fastapi.responses import StreamingResponse

    svc = AIAgentService(db)
    def event_stream():
        messages: queue.Queue = queue.Queue()
        sentinel = object()
        chunk_count = 0

        def run_analysis():
            nonlocal chunk_count
            try:
                result = svc.process_query(
                    query=req.query,
                    date_range=req.date_range,
                    source_name=req.source_name,
                    conversation_history=req.conversation_history,
                    include_sql=req.include_sql,
                    on_chunk=lambda chunk: (messages.put({"chunk": chunk, "done": False}), setattr_counter()),
                )
                if chunk_count == 0:
                    # Built-in deterministic answers are still delivered progressively.
                    for offset in range(0, len(result["answer"]), 24):
                        messages.put({"chunk": result["answer"][offset:offset + 24], "done": False, "model_used": result["model_used"]})
                messages.put({"done": True, "full_result": result})
            except Exception as exc:
                logger.exception("Streaming agent query failed")
                messages.put({"error": "The analyst could not complete this answer."})
            finally:
                messages.put(sentinel)

        def setattr_counter():
            nonlocal chunk_count
            chunk_count += 1

        threading.Thread(target=run_analysis, daemon=True).start()
        while True:
            message = messages.get()
            if message is sentinel:
                break
            yield f"data: {json.dumps(message)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



@router.post("/recommendations", summary="Generate Prioritized Strategic Recommendations")
def get_recommendations(
    req: RecommendationsRequest,
    db: Session = Depends(get_db),
):
    """
    Evaluates current business KPIs and produces a concrete, prioritized action plan
    categorized by Revenue, Retention, Catalog, and Operations.
    """
    svc = AIAgentService(db)
    return svc.generate_recommendations(
        date_range=req.date_range,
        source_name=req.source_name,
        category_focus=req.category_focus,
    )


@router.post("/diagnose", summary="Diagnose Root Causes of Business Anomalies")
def diagnose_anomalies(
    req: DiagnoseRequest,
    db: Session = Depends(get_db),
):
    """
    Investigates anomaly signals (e.g. revenue drops, high cancellation rates,
    churn risks) and returns an evidence-backed diagnostic report with mitigation steps.
    """
    svc = AIAgentService(db)
    return svc.diagnose_anomalies(
        date_range=req.date_range,
        source_name=req.source_name,
        alert_id=req.alert_id,
    )


@router.post("/sql", summary="Safe Read-Only SQL Query Sandbox")
def execute_sql(
    req: SQLSandboxRequest,
    db: Session = Depends(get_db),
):
    raise HTTPException(status_code=403, detail="Direct SQL access is disabled for company workspaces. Ask the AI Analyst a business question instead.")


@router.post("/inventory-reorder-draft", summary="Prepare a restock draft from current stock and recent sales")
def prepare_inventory_reorder_draft(
    req: InventoryReorderDraftRequest,
    db: Session = Depends(get_db),
):
    """Calculate a draft quantity for human review; this does not place an order."""
    return AIAgentService(db).prepare_inventory_reorder_draft(
        product_name=req.product_name,
        product_sku=req.product_sku,
        source_name=req.source_name,
        supplier_lead_time_days=req.supplier_lead_time_days,
        target_cover_days=req.target_cover_days,
    )


@router.get("/suggestions", summary="Get Contextual Quick Prompt Suggestions")
def get_prompt_suggestions(
    date_range: str = Query(default="30d"),
    source_name: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Returns curated quick-prompt questions based on live business performance metrics.
    """
    svc = AIAgentService(db)
    return svc.get_suggested_queries(date_range=date_range, source_name=source_name)


@router.get("/capabilities", summary="Inspect AI Agent Capabilities & Schema Metadata")
def get_agent_capabilities(
    db: Session = Depends(get_db),
):
    """
    Returns introspection metadata about the AI Agent:
    available tools, database tables, safety rules, and reasoning modes.
    """
    svc = AIAgentService(db)
    schema = svc.get_schema_metadata()
    return {
        "service": "AI Business Intelligence Agent (Person 3)",
        "version": "1.0.0",
        "description": "Natural language analytics, root-cause diagnosis, and safe read-only SQL for small businesses.",
        "supported_models": [
            "built-in-analyst (deterministic zero-dependency)",
            "gemini-2.5-flash / gemini-1.5-pro",
            "gpt-4o / gpt-4o-mini",
        ],
        "database_schema": schema["tables"],
        "security_guardrails": schema["guardrails"],
    }
