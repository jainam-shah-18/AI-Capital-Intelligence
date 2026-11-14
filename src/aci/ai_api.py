
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.aci.ai_chat import ask_financial_question
from src.aci.ai_rag import collection_status


app = FastAPI(
    title="AI Capital Intelligence API",
    description="Hybrid financial intelligence using Snowflake and ChromaDB.",
    version="1.0.0",
)


class FinancialQuestion(BaseModel):
    company_name: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=3, max_length=1000)
    limit: int = Field(default=8, ge=1, le=100)
    top_k: int = Field(default=3, ge=1, le=10)


@app.get("/")
def root():
    return {
        "project": "AI Capital Intelligence",
        "status": "ONLINE",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "HEALTHY",
        "vector_database": collection_status(),
    }


@app.post("/ask")
def ask_question(request: FinancialQuestion):

    try:
        result = ask_financial_question(
            company_name=request.company_name,
            question=request.question,
            limit=request.limit,
            top_k=request.top_k,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Financial assistant request failed. Check application logs.",
        )
