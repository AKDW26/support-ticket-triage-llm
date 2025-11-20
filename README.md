# 🧠 Support Ticket Triage Agent (LLM-Powered)

This project implements a small but realistic **AI-powered support ticket triage agent** designed for the take-home assignment.
It extracts structured information from free-text support tickets, searches a knowledge base of known issues, and returns a structured triage response via an API.

The solution focuses on **architecture, robustness, and clean code** while remaining simple enough for a 3–4 hour assignment.


# ⭐ Features

### ✔️ **LLM-powered extraction**

* Summary (1–2 lines)
* Category (Billing, Login, Bug, Performance, etc.)
* Severity (Low/Medium/High/Critical)
* Known issue (boolean)
* Suggested next action

### ✔️ **Semantic KB Search (TF-IDF + Cosine Similarity)**

* Top 3 related known issues returned
* Match scores included
* 10-item sample KB included (`kb/known_issues.json`)

### ✔️ **Robust LLM Integration**

* Primary: Google Gemini via `google-generativeai`
* Fully functional **fallback mock LLM** (deterministic output)
  → Ensures the agent works even if API key is missing or rate-limited.

### ✔️ **Production-ready API (FastAPI)**

* `POST /triage` endpoint
* Input validation
* JSON output
* Clean separation of concerns (API → Orchestrator → Tools → LLM)

### ✔️ **Tests (pytest)**

* KB search test
* API test
* Behavior with missing API key
* Empty description edge case

### ✔️ **Containerization**

* Dockerfile included


# 📁 Project Structure

```
app/
 └── main.py               # FastAPI app & /triage endpoint

agent/
 ├── llm.py                # LLM wrapper (Gemini + mock fallback)
 └── orchestrator.py       # Core triage logic, JSON parsing, fallback logic

tools/
 └── kb_search.py          # TF-IDF KB search

kb/
 └── known_issues.json     # 10-item mock knowledge base

tests/
 ├── test_kb_search.py
 └── test_triage.py

README.md
Dockerfile
requirements.txt
.env.example
```

---

# 🚀 Getting Started

## 1. **Clone / Extract**

If using ZIP:
Extract the folder and enter it:

```
cd support-ticket-triage-agent
```

If using Git:

```
git clone <your_repo_url>
cd <repo_folder>
```

---

## 2. **Environment Setup**

### Create virtual environment (recommended):

```
python3 -m venv .venv
source .venv/bin/activate     # Linux/Mac
.venv\Scripts\activate        # Windows
```

### Install dependencies:

```
pip install -r requirements.txt
```

### Configure environment variables:

Copy:

```
cp .env.example .env
```

Edit `.env`:

```
GOOGLE_API_KEY=your_key_here
GOOGLE_MODEL=gemini-2.5-flash
```

> If no key is provided, system gracefully falls back to a mock LLM.

---

# ▶️ Running the API

Start the service:

```
uvicorn app.main:app --reload --port 8000
```

Visit:

* Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc → [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

# 📬 API Usage

### **POST /triage**

#### Request

```json
{
  "description": "Checkout keeps failing with error 500 on mobile."
}
```

#### Response (example)

```json
{
  "summary": "checkout keeps failing with error 500 on mobile",
  "category": "Bug",
  "severity": "High",
  "known_issue": true,
  "suggested_action": "Escalate to backend team",
  "kb_hits": [
    {
      "id": "ISSUE-101",
      "title": "Checkout error 500 on mobile",
      "match_score": 0.92
    }
  ]
}
```

---

# 🧪 Running Tests

```
pytest -q
```

Tests include:

* TF-IDF semantic search ranking
* /triage endpoint basic behavior
* Missing API key behavior
* Edge-case: empty description

---

# 🏗️ Architecture & Design Notes

### **1. Clear agent architecture**

* **Orchestrator** drives flow:
  KB search → prompt construction → LLM call → JSON parsing → fallback → response
* **LLM wrapper** handles unreliable API behavior & provides deterministic fallback
* **Tools** contain reusable functional utilities (KB search)

### **2. LLM Integration**

* Primary: Google Generative AI (Gemini)
* Handles different response shapes gracefully
* Full JSON extraction → ensures API always returns structured output
* Mock deterministic LLM ensures offline usability

### **3. KB Search**

* TF-IDF vectorization using scikit-learn
* Cosine similarity ranking
* 10 curated mock entries for demo purposes

### **4. Error Handling**

* Multiple layers of fallback:

  * Retry LLM
  * Repair malformed JSON
  * Extract JSON via regex
  * Final deterministic rule-based fallback

### **5. JSON Safety**

* LLM prompted strictly to return raw JSON
* Orchestrator attempts:

  * strict parse
  * JSON block extraction
  * repair quotes & trailing commas
* Ensures the endpoint **never** returns unstructured LLM output

---

# 🏭 Production Considerations

### **Deployment**

* Containerized via Docker
* Suitable for Cloud Run / AWS ECS / Azure Container Apps
* Keep secrets in Secret Manager (never in source)
* Auto-run KB loading at startup

### **Observability**

* Add request logging
* Add Prometheus metrics
* Add trace IDs for LLM calls

### **Scaling**

* API is stateless → horizontal scaling
* Vectorizer + TF-IDF matrix can be cached globally
* For large KBs → move to vector DB (Pinecone, Qdrant, Weaviate)

### **Cost & Latency**

* Gemini usage kept minimal (single prompt)
* Optionally downgrade to "flash" or batch requests
* Fallback ensures zero downtime

---

# 📞 Contact

Feel free to reach out if any clarifications are needed!
pport ticket triage project)
