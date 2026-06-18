import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func


from src.database import get_db, engine, Base
from src.models import QueryLog
from src.schemas import QueryRequest, QueryResponse, AnalyticsSummary
from src.rag_engine import LegalRAGProcessor

rag_backend = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Safely initializes database schemas and heavyweight architectures on server bootstrap."""
    global rag_backend
    try:
       
        Base.metadata.create_all(bind=engine)
        
        
        rag_backend = LegalRAGProcessor()
    except Exception as e:
        import sys
        print(f"CRITICAL SYSTEM FAULT: Could not boot RAG engine dependencies. Reason: {str(e)}")
        sys.exit(1)
    yield

app = FastAPI(title="AWS Legal Contract RAG & Analytics Backend", lifespan=lifespan)

@app.post("/ingest", status_code=status.HTTP_200_OK)
def ingest_document():
    """Parses and vectors the local AWS agreement document into the FAISS workspace memory."""
    try:
        rag_backend.load_and_segment_document()
        rag_backend.generate_vector_index()
        return {"status": "success", "message": "AWS Contract parsed, embedded, and mapped safely."}
    except Exception as err:
        import traceback
        print("--- EXCEPTION TRACEBACK ---")
        traceback.print_exc()
        print("---------------------------")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))
    
@app.post("/ask", response_model=QueryResponse)
def ask_question(payload: QueryRequest, db: Session = Depends(get_db)):
    """Executes search queries across document vector indices, records system telemetry, and logs outcomes."""
    
    
    if not rag_backend.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The RAG vector layer is offline. Please run the document ingestion pipeline first."
        )

    clean_query = payload.query.strip()
    start_time = time.perf_counter()
    
    try:
        sources, generated_answer = rag_backend.execute_retrieval_query(clean_query)
    except Exception as err:
        import traceback
        print("\n--- ASK ENDPOINT CRASH TRACEBACK ---")
        traceback.print_exc()
        print("------------------------------------\n")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(err))
        
    execution_latency = time.perf_counter() - start_time

    fallback_phrase = "I am sorry, but the provided documentation does not contain that information."
    was_context_found = fallback_phrase not in generated_answer

    log_entry = QueryLog(
        query_text=clean_query,
        generated_response=generated_answer,
        context_found=was_context_found,
        latency_seconds=execution_latency
    )
    db.add(log_entry)
    db.commit()

    return QueryResponse(
        query=clean_query,
        answer=generated_answer,
        sources=sources,
        latency_seconds=execution_latency
    )

@app.get("/analytics", response_model=AnalyticsSummary)
def get_system_analytics(db: Session = Depends(get_db)):
    """Computes high-speed SQL aggregation summaries across historical pipeline log metrics."""
    total = db.query(func.count(QueryLog.id)).scalar() or 0
    unanswered = db.query(func.count(QueryLog.id)).filter(QueryLog.context_found == False).scalar() or 0
    avg_latency = db.query(func.avg(QueryLog.latency_seconds)).scalar() or 0.0

    frequent_records = (
        db.query(QueryLog.query_text, func.count(QueryLog.query_text).label("count_value"))
        .group_by(QueryLog.query_text)
        .order_by(func.count(QueryLog.query_text).desc())
        .limit(5)
        .all()
    )

    frequent_list = [{"query": row[0], "count": row[1]} for row in frequent_records]

    return AnalyticsSummary(
        total_queries=total,
        most_frequent_queries=frequent_list,
        unanswered_queries_count=unanswered,
        average_latency_seconds=float(avg_latency)
    )