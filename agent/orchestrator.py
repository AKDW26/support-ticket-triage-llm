# agent/orchestrator.py
import json, os, re, time
from typing import Dict, Any, List
# avoid name clash by aliasing the imported load_kb
from tools.kb_search import load_kb as kb_load_kb, search_kb_topk
from agent.llm import call_llm

KB = []

def load_kb(path: str):
    """
    Load KB using the tools.kb_search loader (aliased to kb_load_kb).
    This wrapper exists so app startup can call orchestrator.load_kb(...) safely.
    """
    global KB
    KB = kb_load_kb(path)
    return KB

_JSON_RE = re.compile(r"(\{.*\})", re.DOTALL)

def _try_parse_json(text: str):
    """Try to parse JSON from text. If direct parse fails, try to extract {...} substring."""
    if not text:
        return None
    # 1) direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # 2) try to find first {...} block (greedy)
    m = _JSON_RE.search(text)
    if m:
        candidate = m.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            # try to fix common issues: replace single quotes, remove trailing commas
            cand2 = candidate.replace("'", '"')
            cand2 = re.sub(r",\s*}", "}", cand2)
            cand2 = re.sub(r",\s*]", "]", cand2)
            try:
                return json.loads(cand2)
            except Exception:
                return None
    return None

def _build_prompt(description: str, kb_hits: List[Dict[str,Any]]) -> str:
    kb_snippets = "\n".join([f"- {h['id']}: {h['title']} (symptoms: {', '.join(h.get('symptoms', []))})" for h in kb_hits])
    prompt = (
        "You are an assistant that extracts structured triage info from a support ticket description.\n\n"
        "Ticket description:\n" + description + "\n\n"
        "Known-issues (top matches):\n" + (kb_snippets if kb_snippets else "(none)\n") + "\n\n"
        "Respond ONLY with a JSON object with these fields:\n"
        "summary: one-line summary string,\n"
        "category: one of [Billing, Login, Performance, Bug, Question/How-To, Account, Technical, Other],\n"
        "severity: one of [Low, Medium, High, Critical],\n"
        "known_issue: boolean,\n"
        "suggested_action: one-line suggested next action.\n\n"
        "IMPORTANT: Reply only with the JSON object (no surrounding explanation)."
    )
    return prompt

def _fallback_response(description: str) -> Dict[str,Any]:
    """Deterministic fallback so API never returns 500 for parsing errors."""
    text = description.lower()
    summary = (text[:120] + '...') if len(text) > 120 else text
    if "payment" in text or "card" in text:
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
    return {
        "summary": summary[:200],
        "category": category,
        "severity": severity,
        "known_issue": bool(known_issue),
        "suggested_action": suggested_action
    }

def process_ticket(description: str) -> Dict[str,Any]:
    # 1) KB search
    kb_hits = search_kb_topk(description, topk=3)

    # 2) Build prompt and call LLM
    prompt = _build_prompt(description, kb_hits)
    llm_response = None
    parsed = None

    try:
        llm_response = call_llm(prompt, max_tokens=600, temperature=0.0)
        # attempt parse
        parsed = _try_parse_json(llm_response)
    except Exception as e:
        # log and continue to retry below
        print("[orchestrator] LLM call exception:", repr(e))
        llm_response = None
        parsed = None

    # 3) If initial parse failed, retry with an explicit "ONLY JSON" instruction (single retry)
    if parsed is None:
        try:
            prompt2 = prompt + "\n\nIf you previously returned anything other than pure JSON, reply ONLY with the JSON object now. Do not include any commentary."
            llm_response2 = call_llm(prompt2, max_tokens=600, temperature=0.0)
            parsed = _try_parse_json(llm_response2)
            # if still None, try to extract JSON from original/second outputs
            if parsed is None:
                parsed = _try_parse_json(llm_response) or _try_parse_json(llm_response2)
        except Exception as e:
            print("[orchestrator] Retry LLM call failed:", repr(e))
            parsed = None

    # 4) Final fallback: if we still couldn't parse, return deterministic fallback
    if parsed is None:
        print("[orchestrator] Could not parse LLM JSON. LLM raw output (truncated):", (llm_response or "")[:500])
        parsed = _fallback_response(description)

    # 5) Attach KB hits and return
    parsed['kb_hits'] = kb_hits
    return parsed
