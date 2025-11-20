# agent/llm.py
import os
import time
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")

genai = None
_import_err = None
client_model = None

if GOOGLE_API_KEY:
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=GOOGLE_API_KEY)
        # prepare a model object (this API shape works for google-generativeai versions exposing GenerativeModel)
        try:
            client_model = genai.GenerativeModel(GOOGLE_MODEL)
        except Exception:
            client_model = None
    except Exception as e:
        _import_err = e
        genai = None
        client_model = None

def _extract_text_from_response(response) -> str:
    # Try several response shapes, return a string
    try:
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        # Some responses provide .candidates or .output
        if hasattr(response, "candidates"):
            c = response.candidates
            if isinstance(c, (list, tuple)) and len(c) > 0:
                first = c[0]
                # dict-like
                if isinstance(first, dict):
                    return (first.get("content") or first.get("message") or first.get("text") or "").strip()
                else:
                    return (getattr(first, "content", None) or getattr(first, "message", None) or "").strip()
        # fallback: stringify
        return str(response)
    except Exception:
        return str(response)

def _mock_llm_response(prompt: str) -> str:
    # Deterministic mock output (valid JSON) used only as last-resort fallback
    text = prompt.lower()
    summary = (text[:120] + '...') if len(text) > 120 else text
    if "payment" in text or "card" in text or "invoice" in text:
        category = "Billing"
    elif "login" in text or "password" in text:
        category = "Login"
    elif "slow" in text or "latency" in text or "timeout" in text:
        category = "Performance"
    elif "error" in text or "500" in text:
        category = "Bug"
    else:
        category = "Technical"
    severity = "High" if ("500" in text or "data loss" in text or "unable" in text) else ("Medium" if "error" in text or "failed" in text else "Low")
    known_issue = any(k in text for k in ("500", "payment", "timeout", "sms", "export"))
    suggested_action = "Escalate to backend team" if severity in ("High","Critical") else "Ask customer for logs/screenshots"
    out = {
        "summary": summary[:200],
        "category": category,
        "severity": severity,
        "known_issue": bool(known_issue),
        "suggested_action": suggested_action
    }
    return json.dumps(out)

def call_llm(prompt: str, max_tokens: int = 300, temperature: float = 0.0, retries: int = 2) -> str:
    """
    Call Gemini via google.generativeai.GenerativeModel.generate_content.
    Falls back to deterministic mock JSON if the model or client isn't available.
    """
    # If client_model isn't available, log and fallback to mock (keeps dev flow smooth)
    if client_model is None:
        note = "GOOGLE_API_KEY missing or client model unavailable."
        if _import_err:
            note += f" Import error: {_import_err}"
        print("[llm] WARNING:", note)
        return _mock_llm_response(prompt)

    last_exc = None
    for attempt in range(retries + 1):
        try:
            # Try the simplest generate_content invocation (positional); many client versions accept this.
            # We avoid using keywords like max_output_tokens that some client versions don't accept.
            resp = client_model.generate_content(prompt)

            # If your client returns an object with `.text`, prefer that; otherwise extract robustly.
            return _extract_text_from_response(resp)
        except TypeError as te:
            # If this specific signature fails due to unexpected kwargs or signature mismatch,
            # try one more permissive approach (some versions accept a single dict arg).
            try:
                resp = client_model.generate_content({"prompt": prompt})
                return _extract_text_from_response(resp)
            except Exception:
                last_exc = te  # fall through to fallback below
        except Exception as e:
            last_exc = e
            time.sleep(1 + attempt * 2)

