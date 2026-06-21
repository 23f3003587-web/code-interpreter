import os
import sys
import traceback
import json
import re
from io import StringIO
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # works locally; ignored on Render if you set env var there

app = FastAPI(title="Code Interpreter + AI Error Analysis")

# CORS enabled (required for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str

def execute_python_code(code: str) -> dict:
    """
    Tool: Execute Python code and return exact stdout or traceback.
    """
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        exec(code)   # For production untrusted code, replace with your goboxd/nsjail sandbox
        output = sys.stdout.getvalue()
        return {"success": True, "output": output}
    except Exception:
        output = traceback.format_exc()
        return {"success": False, "output": output}
    finally:
        sys.stdout = old_stdout

def extract_lines_from_traceback(tb: str) -> List[int]:
    """Fallback regex extractor (used if AI fails or no token)."""
    matches = re.findall(r'line (\d+), in', tb)
    return sorted(set(int(m) for m in matches)) if matches else []

def analyze_error_with_ai(code: str, tb: str) -> List[int]:
    """
    AI Agent: Uses LLM (via aipipe) with structured JSON output to find exact error lines.
    Only called when execution fails.
    """
    token = os.getenv("AIPIPE_TOKEN")
    if not token:
        print("⚠️ No AIPIPE_TOKEN — using fallback line extraction")
        return extract_lines_from_traceback(tb)

    try:
        client = OpenAI(
            api_key=token,
            base_url="https://aipipe.org/openrouter/v1"   # ← aipipe proxy
        )

        prompt = f"""You are an expert Python debugger.
Identify the EXACT line number(s) (1-indexed) in the CODE below where the error occurred.
Use the TRACEBACK only as a hint — map it back to the CODE lines.
Return ONLY valid JSON in this exact format: {{"error_lines": [3]}} or {{"error_lines": [2, 5]}}
No explanations, no markdown, no extra text.

CODE:
{code}

TRACEBACK:
{tb}
"""

        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001",   # cheap & fast via OpenRouter
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=150
        )

        content = response.choices[0].message.content.strip()

        # Clean possible code fences
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed = json.loads(content)
        lines = parsed.get("error_lines", [])
        return [int(x) for x in lines if str(x).isdigit()]

    except Exception as e:
        print(f"AI analysis error: {e} — falling back to regex")
        return extract_lines_from_traceback(tb)

@app.post("/code-interpreter")
async def code_interpreter(req: CodeRequest):
    result = execute_python_code(req.code)

    if result["success"]:
        return {"error": [], "result": result["output"]}
    else:
        # Only call AI when there is an error (as required)
        error_lines = analyze_error_with_ai(req.code, result["output"])
        return {"error": error_lines, "result": result["output"]}

@app.get("/")
async def root():
    return {
        "message": "Code Interpreter API ready. POST JSON to /code-interpreter",
        "example": {"code": "x=5\ny=10\nprint(x+y)"}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    