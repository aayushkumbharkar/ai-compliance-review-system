# 🛡️ AI Compliance Builder

**An AI-native suspicious transaction review system built for modern financial compliance.**

This system combines deterministic risk scoring with LLM-powered reasoning and human-in-the-loop decision making. Every flagged transaction is scored, analyzed by AI, and confirmed by a human — with a full audit trail.

---

## 1. Project Overview

### The Problem

Financial institutions are required to detect and report suspicious transactions. Traditional rule-based systems generate too many false positives, and analysts waste hours reviewing transactions that aren't actually risky.

### Why Rules Alone Aren't Enough

A hard-coded rule like "flag anything over $10,000" catches obvious cases but misses subtle patterns — like a user who normally spends $50 suddenly making 5 purchases of $400 in 2 minutes from a new country. Context matters, and rules don't understand context.

### How This System Works

This project takes a layered approach:

1. **Deterministic rules** catch measurable anomalies (amount spikes, country changes, transaction bursts)
2. **An LLM** reads the full context and produces structured reasoning — explaining _why_ a transaction looks suspicious and what regulations may apply
3. **A human reviewer** sees both the rules and the AI's analysis, then makes the final call
4. **Every decision is logged** with a timestamp for regulatory audit

The AI advises. The human decides. The system records everything.

---

## 2. Live Demo

🔗 **[Launch the App →](YOUR_STREAMLIT_CLOUD_URL_HERE)**

> Replace the link above with your deployed Streamlit Cloud URL.

### How to Use It

1. Open the app — it loads 100,000 synthetic transactions and flags the suspicious ones
2. Use the **sidebar dropdown** to select a flagged transaction
3. Review the **Transaction Details** and **Deterministic Risk Metrics**
4. Click **"Generate AI Report"** to get the LLM's structured analysis
5. Make your decision: **Approve**, **Escalate**, or **Confirm Freeze** (when applicable)
6. Your decision is saved to the audit log automatically

---

## 3. Architecture Overview

The system is split into four independent layers, each with a single responsibility.

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI (app.py)                 │
│         Sidebar selection → Details → AI Report         │
│              → Human Decision → Audit Log               │
└────────────┬──────────────┬──────────────┬──────────────┘
             │              │              │
     ┌───────▼───────┐ ┌───▼────────┐ ┌───▼──────────┐
     │  Risk Engine  │ │ LLM Engine │ │  Audit Log   │
     │ (risk_engine) │ │(llm_engine)│ │(decision_log)│
     └───────┬───────┘ └───┬────────┘ └──────────────┘
             │              │
     ┌───────▼──────────────▼───────┐
     │   Data Generator             │
     │   (data_generator.py)        │
     └──────────────────────────────┘
```

### Layer by Layer

| Layer               | File                | What It Does                                                                                                                                                                        |
| ------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Data Generation** | `data_generator.py` | Creates 100K realistic transactions across 1,000 users. Injects anomalies (amount spikes, country changes, burst activity) into ~5% of users.                                       |
| **Risk Scoring**    | `risk_engine.py`    | Computes a deterministic risk score (0–1) per transaction using weighted signals: amount z-score, country change, device change, and burst detection.                               |
| **LLM Reasoning**   | `llm_engine.py`     | Sends flagged transactions to Groq's Llama 3.1 model. Returns a structured JSON report with risk summary, anomalies, regulatory concerns, recommended action, and confidence score. |
| **Human Review**    | `app.py`            | Streamlit dashboard where a compliance analyst reviews the AI's recommendation and makes the final decision.                                                                        |
| **Audit Logging**   | `decision_log.json` | Every human decision is recorded with transaction ID, risk score, AI recommendation, human decision, confidence, and timestamp.                                                     |

### Data Flow

```
Generate transactions → Score each one → Flag if score > 0.5
    → Display in dashboard → Human requests AI report
    → AI returns structured JSON → Human approves/escalates/freezes
    → Decision logged with timestamp
```

---

## 4. Key Features

- **Deterministic Risk Scoring**
  Weighted formula using amount deviation, country change, device change, and burst detection. No black boxes — every score is explainable.

- **Structured AI Reasoning**
  The LLM returns strict JSON with a defined schema, not free-form text. Every response includes `risk_summary`, `key_anomalies`, `regulatory_concerns`, `recommended_action`, and `confidence`.

- **Human Decision Boundary**
  The AI recommends — the human confirms. No transaction is auto-approved or auto-frozen. This matches real-world regulatory requirements.

- **Production-Safe Logging**
  The decision log handles empty files, corrupted JSON, and missing fields gracefully. It never crashes due to bad data.

- **Fault Tolerance**
  If the LLM returns malformed output, the system falls back to a safe default. If the API key is missing, the app still loads — it just shows a fallback response when AI is requested.

---

## 5. Technical Stack

| Component          | Technology           |
| ------------------ | -------------------- |
| Frontend           | Streamlit            |
| Language           | Python 3.10+         |
| LLM Provider       | Groq API             |
| LLM Model          | Llama 3.1 8B Instant |
| Data Processing    | Pandas, NumPy        |
| Audit Storage      | JSON file            |
| Environment Config | python-dotenv        |

---

## 6. Why This Is Production-Oriented

This is not a demo that breaks when you look at it wrong. Specific design decisions:

- **Safe fallback behavior** — If the LLM fails, the system returns a structured default response with `"recommended_action": "escalate"` instead of crashing.

- **No silent crashes** — All exceptions are caught and logged. Bare `except:` clauses are replaced with specific exception types (`json.JSONDecodeError`, `IOError`).

- **Structured output validation** — After parsing LLM output, the system verifies all 5 required keys exist. Missing keys trigger the fallback.

- **Timestamped audit trail** — Every logged decision includes an ISO 8601 timestamp. This is a basic regulatory requirement.

- **Clean separation of concerns** — Data generation, risk scoring, LLM interaction, and the UI are in separate files with no circular dependencies. Each can be tested and replaced independently.

- **Cached computation** — The 100K-row flagged transaction scan runs once and is cached, not re-executed on every UI interaction.

---

## 7. Future Improvements

- **Replace JSON logging with PostgreSQL** — For multi-user access, query support, and durability.
- **Add monitoring and alerting** — Track LLM latency, failure rates, and flag volume over time.
- **Model versioning** — Log which model version produced each recommendation for auditability.
- **Deploy as an API service** — Expose the risk engine and LLM layer as REST endpoints for integration with existing banking systems.
- **Role-based access control** — Different permission levels for analysts, managers, and auditors.
- **Real transaction data ingestion** — Replace synthetic data with a secure pipeline from live transaction feeds.

---

## License

This project is for portfolio and educational purposes.

---

_Built with Python, Streamlit, and Groq._
