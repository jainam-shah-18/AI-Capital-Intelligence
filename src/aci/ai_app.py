import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

COMPANIES = [
    "AMAZON.COM, INC.",
    "Alphabet Inc.",
    "MICROSOFT CORPORATION",
    "Meta Platforms, Inc.",
]

st.set_page_config(
    page_title="AI Capital Intelligence",
    page_icon="📊",
    layout="wide",
)

st.title("📊 AI Capital Intelligence")
st.caption("Hybrid financial intelligence powered by Snowflake, ChromaDB and local AI infrastructure.")

# Sidebar
with st.sidebar:
    st.header("Configuration")

    company = st.selectbox(
        "Select company",
        COMPANIES,
    )

    limit = st.slider(
        "Financial records",
        min_value=1,
        max_value=100,
        value=8,
    )

    top_k = st.slider(
        "RAG context records",
        min_value=1,
        max_value=10,
        value=3,
    )

    st.divider()
    st.subheader("System status")

    try:
        health = requests.get(
            f"{API_URL}/health",
            timeout=10,
        )
        health.raise_for_status()

        health_data = health.json()

        st.success("API Healthy")
        st.write(
            "ChromaDB documents:",
            health_data["vector_database"]["document_count"],
        )

    except requests.RequestException:
        st.error("API unavailable. Start FastAPI first.")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant" and message.get("details"):
            details = message["details"]

            st.caption(
                f"Source: {details.get('answer_source', 'N/A')} | "
                f"Period: {details.get('latest_period', 'N/A')} | "
                f"RAG records: {details.get('rag_records_used', 0)}"
            )

            with st.expander("View retrieved knowledge"):
                for index, record in enumerate(
                    details.get("rag_context", []),
                    start=1,
                ):
                    st.markdown(f"**Retrieved record {index}**")
                    st.text(record.get("document", ""))

# User question
question = st.chat_input(
    "Ask about revenue, cash flow, forecasts, anomalies or company risk..."
)

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question,
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing financial data..."):
            try:
                response = requests.post(
                    f"{API_URL}/ask",
                    json={
                        "company_name": company,
                        "question": question,
                        "limit": limit,
                        "top_k": top_k,
                    },
                    timeout=180,
                )

                response.raise_for_status()
                result = response.json()

                answer = result.get(
                    "answer",
                    "No answer returned.",
                )

                st.markdown(answer)

                st.caption(
                    f"Source: {result.get('answer_source', 'N/A')} | "
                    f"Period: {result.get('latest_period', 'N/A')} | "
                    f"RAG records: {result.get('rag_records_used', 0)}"
                )

                with st.expander("View retrieved knowledge"):
                    for index, record in enumerate(
                        result.get("rag_context", []),
                        start=1,
                    ):
                        st.markdown(f"**Retrieved record {index}**")
                        st.text(record.get("document", ""))

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "details": result,
                })

            except requests.RequestException as exc:
                st.error(f"API request failed: {exc}")

            except Exception as exc:
                st.error(f"Unexpected error: {exc}")