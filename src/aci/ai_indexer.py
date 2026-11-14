
from src.aci.ai_retrieval import (
    retrieve_company_performance,
    retrieve_company_comparison,
    retrieve_cash_flow,
    retrieve_revenue_forecast,
    retrieve_financial_anomalies,
    retrieve_financial_risk,
)

from src.aci.ai_rag import (
    index_records,
    collection_status,
)


COMPANIES = [
    "AMAZON.COM, INC.",
    "Alphabet Inc.",
    "MICROSOFT CORPORATION",
    "Meta Platforms, Inc.",
]

RETRIEVAL_FUNCTIONS = {
    "PERFORMANCE": retrieve_company_performance,
    "COMPARISON": retrieve_company_comparison,
    "CASH_FLOW": retrieve_cash_flow,
    "FORECAST": retrieve_revenue_forecast,
    "ANOMALIES": retrieve_financial_anomalies,
    "RISK": retrieve_financial_risk,
}


def index_company(company_name, limit=100):

    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("Limit must be an integer.")

    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")

    results = {}

    for category, retrieval_function in RETRIEVAL_FUNCTIONS.items():

        print(f"\nIndexing {category}: {company_name}")

        records = retrieval_function(
            company_name,
            limit
        )

        indexed = index_records(
            category,
            records
        )

        results[category] = {
            "retrieved": len(records),
            "indexed": indexed,
        }

        print(
            f"Retrieved: {len(records)} | Indexed: {indexed}"
        )

    return results


def index_all_companies(limit=100):

    summary = {}

    for company in COMPANIES:

        print("\n" + "=" * 55)
        print("COMPANY:", company)
        print("=" * 55)

        summary[company] = index_company(
            company,
            limit
        )

    print("\nFINAL CHROMADB STATUS")
    print(collection_status())

    return summary


if __name__ == "__main__":

    results = index_all_companies(limit=100)

    total = sum(
        category_result["indexed"]
        for company_result in results.values()
        for category_result in company_result.values()
    )

    print("\nTOTAL RECORDS INDEXED:", total)
