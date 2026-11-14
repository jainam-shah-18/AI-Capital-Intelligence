
import hashlib
import json
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import chromadb
import requests


OLLAMA_BASE_URL = os.getenv(
    "ACI_OLLAMA_URL",
    "http://localhost:11434"
)

EMBEDDING_MODEL = "nomic-embed-text:latest"

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHROMA_PATH = PROJECT_ROOT / "data" / "vector_store"

COLLECTION_NAME = "aci_financial_knowledge"

CHROMA_PATH.mkdir(parents=True, exist_ok=True)

_client = chromadb.PersistentClient(path=str(CHROMA_PATH))

_collection = _client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


def serialize_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if value is None:
        return "Not available"

    return str(value)


def create_document(category, record):
    company = record.get("COMPANY_NAME", "Unknown company")

    lines = [
        f"Category: {category}",
        f"Company: {company}"
    ]

    for key, value in record.items():
        if key == "COMPANY_NAME":
            continue

        lines.append(
            f"{key}: {serialize_value(value)}"
        )

    return "\n".join(lines)


def create_embedding(text):
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={
            "model": EMBEDDING_MODEL,
            "input": text
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    embeddings = data.get("embeddings", [])

    if not embeddings:
        raise RuntimeError(
            "Ollama returned no embedding."
        )

    return embeddings[0]


def document_id(category, record):
    raw = json.dumps(
        {
            "category": category,
            "record": {
                key: serialize_value(value)
                for key, value in record.items()
            }
        },
        sort_keys=True,
        default=str
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


def index_records(category, records):
    if not records:
        return 0

    documents = []
    ids = []
    embeddings = []
    metadatas = []

    for record in records:
        document = create_document(category, record)

        documents.append(document)
        ids.append(document_id(category, record))

        embeddings.append(
            create_embedding(document)
        )

        metadatas.append({
            "category": category,
            "company": str(
                record.get("COMPANY_NAME", "Unknown")
            ),
            "period_end": serialize_value(
                record.get("PERIOD_END")
                or record.get("TARGET_PERIOD_END")
            )
        })

    _collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return len(documents)


def retrieve_context(
    question,
    company_name=None,
    category=None,
    top_k=5
):
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    if isinstance(top_k, bool) or not isinstance(top_k, int):
        raise ValueError("top_k must be an integer.")

    if not 1 <= top_k <= 10:
        raise ValueError("top_k must be between 1 and 10.")

    query_embedding = create_embedding(question)

    filters = []

    if company_name:
        filters.append({
            "company": company_name
        })

    if category:
        filters.append({
            "category": category
        })

    where = None

    if len(filters) == 1:
        where = filters[0]
    elif len(filters) > 1:
        where = {"$and": filters}

    if _collection.count() == 0:
        return []

    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, _collection.count()),
        where=where,
        include=["documents", "metadatas", "distances"]
    )

    output = []

    for i, document in enumerate(results["documents"][0]):
        output.append({
            "document": document,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })

    return output


def collection_status():
    return {
        "collection": COLLECTION_NAME,
        "document_count": _collection.count(),
        "storage_path": str(CHROMA_PATH)
    }
