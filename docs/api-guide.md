# EcoSynapse AI — API Documentation & Integration Guide

This guide provides end-to-end documentation for interacting with the EcoSynapse AI FastAPI backend.

---

## 1. Base URL & Endpoints

| Environment | Base URL | Description |
|---|---|---|
| **Local Development** | `http://localhost:8000` | Local FastAPI backend instance |
| **Production Cloud** | `https://daruka.onrender.com` | Production Render deployment |

---

## 2. Core Endpoints

### 2.1 Health & Telemetry
- **Endpoint**: `GET /health`
- **Description**: Performs self-diagnostics on DB connectivity, knowledge base availability, and runtime telemetry.
- **Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "knowledge_chunks": 420,
  "telemetry": {
    "uptime_seconds": 1845.2,
    "memory_mb": 64.2
  }
}
```

### 2.2 Ecological Assessment Query
- **Endpoint**: `POST /api/v1/assessments`
- **Description**: Submits an ecological inquiry for evidence-grounded multi-agent synthesis.
- **Request Body**:
```json
{
  "query": "What are the impacts of riparian restoration on macroinvertebrate diversity?",
  "region": "Pacific Northwest",
  "confidence_threshold": 0.75
}
```

### 2.3 Evidence Retrieval & Verification
- **Endpoint**: `GET /api/v1/evidence/verify`
- **Description**: Verifies candidate ecological claims against indexed peer-reviewed literature.

### 2.4 Knowledge Graph Traversal
- **Endpoint**: `GET /api/v1/graph/nodes`
- **Description**: Retrieves interconnected ecological entities, trophic interactions, and intervention nodes.

---

## 3. Python Integration Example

```python
import requests

API_URL = "http://localhost:8000/api/v1/assessments"

payload = {
    "query": "Evaluate the effect of biochar amendment on soil microbial respiration in boreal forests."
}

response = requests.post(API_URL, json=payload, timeout=30)
if response.status_code == 200:
    data = response.json()
    print("Synthesis:", data["synthesis"])
    print("Confidence Score:", data["confidence_score"])
    print("Citations:", len(data["evidence_citations"]))
```

---

## 4. Error Responses

The API uses standard HTTP response codes:
- `200 OK`: Successful query synthesis.
- `400 Bad Request`: Missing or malformed query payload.
- `422 Unprocessable Entity`: Field validation error.
- `500 Internal Server Error`: Backend runtime exception with request ID tracking.
