import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")

print("Using model:", model_name)

if not key:
    print("GOOGLE_API_KEY not set.")
    raise SystemExit(1)

try:
    import google.generativeai as genai
    genai.configure(api_key=key)

    # The correct modern API:
    model = genai.GenerativeModel(model_name)

    response = model.generate_content("Say hello in one short sentence.")
    print("Output:", response.text)

except Exception as e:
    print("Gemini call failed:", repr(e))
    raise
