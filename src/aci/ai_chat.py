
from src.aci.ai_assistant import (
    ask_company_performance,
    ask_cash_flow,
    ask_company_comparison,
    ask_revenue_forecast,
    ask_financial_anomalies,
    ask_financial_risk,
)

from src.aci.ai_rag import retrieve_context


ROUTES = {
    "PERFORMANCE": ask_company_performance,
    "CASH_FLOW": ask_cash_flow,
    "COMPARISON": ask_company_comparison,
    "FORECAST": ask_revenue_forecast,
    "ANOMALIES": ask_financial_anomalies,
    "RISK": ask_financial_risk,
}


def detect_category(question):

    q = question.lower()

    if any(word in q for word in [
        "forecast", "predict", "future", "next quarter"
    ]):
        return "FORECAST"

    if any(word in q for word in [
        "cash flow", "cashflow", "capex",
        "free cash flow", "operating cash"
    ]):
        return "CASH_FLOW"

    if any(word in q for word in [
        "compare", "comparison", "peer",
        "ranking", "rank"
    ]):
        return "COMPARISON"

    if any(word in q for word in [
        "anomaly", "anomalies", "unusual",
        "outlier", "abnormal"
    ]):
        return "ANOMALIES"

    if any(word in q for word in [
        "risk", "monitoring", "flag",
        "financial health", "warning"
    ]):
        return "RISK"

    return "PERFORMANCE"


def ask_financial_question(
    company_name,
    question,
    limit=8,
    top_k=3
):

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not isinstance(company_name, str) or not company_name.strip():
        raise ValueError("Company name cannot be empty.")

    category = detect_category(question)

    assistant_function = ROUTES[category]

    result = assistant_function(
        company_name,
        question,
        limit
    )

    context = retrieve_context(
        question=question,
        company_name=result.get("company", company_name),
        category=category,
        top_k=top_k
    )

    result["detected_category"] = category
    result["rag_records_used"] = len(context)
    result["rag_context"] = context

    result["architecture"] = "HYBRID_SNOWFLAKE_CHROMADB"

    return result
