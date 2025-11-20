import os
import pytest

try:
    import google.generativeai as genai
except Exception:
    pytest.skip("google.generativeai not installed; skipping.", allow_module_level=True)

if not os.getenv("GOOGLE_API_KEY"):
    pytest.skip("GOOGLE_API_KEY not set; skipping Gemini tests.", allow_module_level=True)

def test_gemini_quick_call():
    model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content("Say hello in one short sentence.")
    text = getattr(resp, "text", None) or str(resp)
    assert text.strip()
