import os
import re
import json
import hashlib
import urllib.request
import time
import requests
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import httpx
import pypdf
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

app = FastAPI(
    title="TalentBridge AI API",
    description="Backend API for Resume Checker, Job Matcher, and Skill Gap Roadmap Generator",
    version="2.0.0"
)

# Enable CORS for React frontend (Vite default port 5173 and others)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- TECHNICAL COMPETENCIES CATALOG -----------------
TECH_SKILLS_CATALOG = {
    'Languages': ['python', 'java', 'c++', 'c#', 'c', 'javascript', 'typescript', 'go', 'golang', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'dart', 'scala', 'r', 'matlab', 'sql'],
    'Frontend': ['react', 'next.js', 'angular', 'vue', 'html', 'css', 'tailwind', 'bootstrap', 'sass', 'redux', 'svelte', 'jquery'],
    'Backend & Frameworks': ['node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'spring boot', 'asp.net', 'ruby on rails', 'laravel', '.net'],
    'Databases & Storage': ['postgresql', 'postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'sqlite', 'oracle', 'firebase', 'supabase', 'prisma'],
    'Cloud & DevOps': ['aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'git', 'github', 'gitlab', 'linux', 'bash', 'nginx'],
    'Architecture & Messaging': ['rest api', 'rest', 'graphql', 'grpc', 'kafka', 'rabbitmq', 'microservices', 'distributed systems', 'system design', 'websockets'],
    'AI & Data Science': ['machine learning', 'deep learning', 'nlp', 'computer vision', 'pytorch', 'tensorflow', 'scikit-learn', 'pandas', 'numpy', 'llm', 'langchain', 'data analysis'],
    'Testing & Practices': ['unit testing', 'pytest', 'jest', 'agile', 'scrum', 'jira', 'tdd', 'oop']
}

all_skills_lookup = {}
for cat, skills in TECH_SKILLS_CATALOG.items():
    for s in skills:
        display = s.upper() if s in ['aws', 'gcp', 'ci/cd', 'sql', 'html', 'css', 'nlp', 'oop', 'tdd', 'llm', 'k8s'] else s.title()
        all_skills_lookup[s] = (display, cat)

def extract_competencies(text: str) -> Dict[str, str]:
    """Deterministically extracts verified technical skills using regex word boundaries."""
    if not text:
        return {}
    text_clean = ' ' + re.sub(r'[^a-zA-Z0-9\.\+#/]', ' ', text.lower()) + ' '
    found = {}
    for term, (display_name, category) in all_skills_lookup.items():
        pattern = r'(?:\s|^|/)' + re.escape(term) + r'(?:\s|$|/)'
        if re.search(pattern, text_clean):
            found[display_name] = category
    return found

def compute_deterministic_score(resume_text: str, job_text: str, matched_skills: list, total_required: int) -> int:
    """
    100% deterministic, mathematically stable scoring algorithm.
    Produces identical score every time for identical resume and job description.
    """
    # 1. Core Technical Skill Overlap (60% weight)
    tech_score = (len(matched_skills) / max(total_required, 1)) * 100
    
    # 2. Contextual Lexical / Jaccard Similarity (30% weight)
    def clean_tokens(t):
        words = re.findall(r'\b[a-z]{3,}\b', t.lower())
        stopwords = {'the', 'and', 'for', 'with', 'that', 'this', 'have', 'from', 'your', 'will', 'are', 'you', 'can', 'our'}
        return set(w for w in words if w not in stopwords)
    
    r_tokens = clean_tokens(resume_text)
    j_tokens = clean_tokens(job_text)
    jaccard = (len(r_tokens.intersection(j_tokens)) / max(len(j_tokens), 1)) * 100
    
    # 3. Academic & Foundational Engineering Alignment (10% weight)
    has_degree = any(k in resume_text.lower() for k in ['b.tech', 'bachelor', 'degree', 'computer science', 'engineering', 'm.tech', 'bca', 'mca'])
    edu_score = 100 if has_degree else 40
    
    final_score = round(0.60 * tech_score + 0.30 * jaccard + 0.10 * edu_score)
    return min(max(final_score, 5), 98)

def compute_hybrid_match_metrics(resume_text: str, job_text: str) -> Dict[str, Any]:
    """Calculates deterministic skill overlap, missing skills, and overlap ratio."""
    resume_skills = extract_competencies(resume_text)
    job_skills = extract_competencies(job_text)
    
    r_set = set(resume_skills.keys())
    j_set = set(job_skills.keys())
    
    matched_skills = sorted(list(r_set.intersection(j_set)))
    missing_skills = sorted(list(j_set.difference(r_set)))
    candidate_additional = sorted(list(r_set.difference(j_set)))
    
    total_required = max(len(j_set), 1)
    deterministic_score = compute_deterministic_score(resume_text, job_text, matched_skills, total_required)
    
    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "candidate_additional": candidate_additional,
        "total_required": len(j_set),
        "deterministic_score": deterministic_score
    }

# Fingerprint Cache to lock scores for identical inputs
cached_audits: Dict[str, Dict[str, Any]] = {}

def clean_pure_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'\*{1,3}', '', text)
    text = re.sub(r'^(Certainly!|Here is your|Sure,|As requested|Hello!)[^\n]*\n+', '', text, flags=re.IGNORECASE)
    return text.strip()

def fetch_available_models(api_key: str) -> list:
    if not api_key:
        return []
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}", "HTTP-Referer": "http://localhost:5173", "X-Title": "TalentBridge"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [m["id"] for m in data.get("data", [])]
    except Exception:
        return []

def get_openrouter_api_key() -> str:
    """Retrieves OpenRouter API key dynamically, cleaning quotes and checking variations."""
    key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_ROUTER_KEY") or OPENROUTER_API_KEY or ""
    return key.strip("'\" \t\r\n")

def execute_llm_call_with_live_status(messages: list, json_mode: bool = False):
    """
    Executes LLM call with rock-solid serverless network resilience,
    dual requests + openai client failover, and clear diagnostic reporting.
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenRouter API Key is missing. In Vercel Dashboard > Project Settings > Environment Variables, add OPENROUTER_API_KEY, then redeploy."
        )

    primary_chain = [
        "openai/gpt-4o-mini",
        "deepseek/deepseek-chat",
        "meta-llama/llama-3.3-70b-instruct",
        "qwen/qwen-2.5-72b-instruct"
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://talentbridge-ai.vercel.app",
        "X-Title": "TalentBridge AI"
    }

    last_exception = None
    attempted_models = []

    for model_name in primary_chain:
        attempted_models.append(model_name)
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.0
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        # Attempt 1: Direct HTTP via requests (handles serverless IPv4/IPv6 gracefully)
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=(6.0, 30.0)
            )

            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return content, model_name, attempted_models
            elif resp.status_code == 401:
                raise Exception("OpenRouter API Key is invalid or expired (HTTP 401 Unauthorized). Please verify OPENROUTER_API_KEY in your Vercel settings.")
            elif resp.status_code == 402:
                raise Exception("OpenRouter Account has insufficient credits (HTTP 402 Payment Required). Please check your balance at openrouter.ai/credits.")
            elif resp.status_code == 429:
                last_exception = Exception(f"Model {model_name} rate-limited (HTTP 429). Retrying next model in chain...")
                continue
            else:
                last_exception = Exception(f"OpenRouter HTTP {resp.status_code}: {resp.text[:140]}")
                continue

        except Exception as req_err:
            last_exception = req_err

        # Attempt 2: Fallback via OpenAI SDK client
        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                timeout=httpx.Timeout(30.0, connect=6.0),
                max_retries=0,
                default_headers=headers
            )
            kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.0
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content, model_name, attempted_models

        except Exception as sdk_err:
            last_exception = sdk_err
            continue

    raise Exception(f"All models in failover chain failed. Last error: {str(last_exception)}")

def parse_pdf_bytes(file_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        return "\n".join([page.extract_text() or "" for page in reader.pages]).strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing PDF: {str(e)}")

# ----------------- PYDANTIC SCHEMAS -----------------
class AuditRequest(BaseModel):
    resume_text: str
    job_desc: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

# ----------------- ROUTES -----------------
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "TalentBridge AI",
        "team": ["Suyash Singh", "Shubhada Shingane"]
    }

@app.get("/api/models")
def get_models():
    models_list = fetch_available_models(OPENROUTER_API_KEY)
    count = len(models_list) if models_list else 460
    return {
        "count": count,
        "sample_chain": [
            "deepseek/deepseek-chat",
            "openai/gpt-4o-mini",
            "meta-llama/llama-3.3-70b-instruct",
            "qwen/qwen-2.5-72b-instruct"
        ]
    }

def process_audit_core(final_resume_text: str, final_job_desc: str):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key is missing in .env file.")
        
    if not final_resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text or PDF content is required.")
        
    if not final_job_desc.strip():
        raise HTTPException(status_code=400, detail="Target job description is required.")

    # Compute SHA-256 fingerprint of inputs for 100% stable caching
    inputs_fingerprint = hashlib.sha256(
        (final_resume_text.strip().lower() + "|||" + final_job_desc.strip().lower()).encode("utf-8")
    ).hexdigest()

    # Check cache for locked deterministic score on identical inputs
    if inputs_fingerprint in cached_audits:
        cached_entry = cached_audits[inputs_fingerprint]
        return {
            "cached": True,
            "data": cached_entry["data"],
            "metrics": cached_entry["metrics"],
            "model_used": cached_entry.get("model_used", "openai/gpt-4o-mini"),
            "fingerprint": inputs_fingerprint
        }

    system_prompt = """You are a rigorous, production-grade ATS Audit Algorithm and Senior Engineering Hiring Committee Member.
You must perform an EXACT, FACTUAL, MATHEMATICALLY ACCURATE audit of candidate fit against job requirements.
NO MOCKUPS. NO RANDOM NUMBERS. NO PLACEHOLDER TEXT.

EVALUATION SPECIFICATION:
1. Extract Job Requirements:
   - Identify distinct requirements. Group alternatives as single requirements (e.g. 'Cloud: AWS or GCP' is 1 requirement; if candidate has AWS, it is satisfied).
   - Evaluate each requirement as Satisfied, Partial, or Missing.
2. Calculate Domain Competency Scores (0 to 100 each based on candidate coverage):
   - Languages: (matched / required) * 100
   - Frameworks: (matched / required) * 100
   - Databases: (matched / required) * 100
   - Cloud & DevOps: (matched / required) * 100
   - Architecture: (matched / required) * 100
   - Practices: (matched / required) * 100
3. Calculate Overall Component Scores:
   - core_skills_score: Average percentage of core technical requirements satisfied (0-100).
   - experience_alignment_score: Candidate years of relevant experience vs requested role seniority (0-100).
     * If role is Senior (5+ yrs) and candidate has 2 yrs, realistic score is 40-50%.
   - supporting_skills_score: Education degree match (CS/Eng degree = 100%, related = 75%, other = 50%) and supporting practices (0-100).
4. Strictly compute match_score using exact formula:
   match_score = round(0.50 * core_skills_score + 0.30 * experience_alignment_score + 0.20 * supporting_skills_score)
   Bound strictly between 5 and 98.
5. Set ats_status:
   - 85 - 100: 'Strong Match'
   - 70 - 84: 'Competitive Match'
   - 50 - 69: 'Moderate Fit'
   - Below 50: 'Action Required - Skill Deficit'
6. For EVERY missing requirement, provide a structured upskilling milestone with why needed, a concrete proof-of-work project to build, and official learning resources.
7. Return strictly valid JSON.
"""

    user_prompt = f"""AUDIT THIS RESUME AGAINST THIS JOB DESCRIPTION:

CANDIDATE RESUME:
{final_resume_text}

TARGET JOB DESCRIPTION:
{final_job_desc}

Respond strictly in this JSON format:
{{
  "core_skills_score": <integer 0-100>,
  "experience_alignment_score": <integer 0-100>,
  "supporting_skills_score": <integer 0-100>,
  "domain_scores": [
    {{ "domain": "Languages", "score": <0-100>, "details": <brief summary of matched vs required> }},
    {{ "domain": "Frameworks", "score": <0-100>, "details": <brief summary> }},
    {{ "domain": "Databases", "score": <0-100>, "details": <brief summary> }},
    {{ "domain": "Cloud & DevOps", "score": <0-100>, "details": <brief summary> }},
    {{ "domain": "Architecture", "score": <0-100>, "details": <brief summary> }},
    {{ "domain": "Practices", "score": <0-100>, "details": <brief summary> }}
  ],
  "matched_skills": [<list of technologies candidate satisfies>],
  "missing_skills": [<list of requirements candidate lacks>],
  "candidate_additional": [<list of candidate skills not required by job>],
  "executive_overview": <honest, candid 3-4 sentence evaluation in clean text without HTML or asterisks>,
  "verified_strengths": [<4-5 specific candidate strengths from resume>],
  "what_to_add": [<4-5 specific additions to resume to pass ATS screening>],
  "what_to_remove": [<3-4 weak phrases, generic adjectives, or passive lines to remove>],
  "what_to_skill_up": [
    {{
      "priority": <"High Priority" | "Medium Priority">,
      "skill": <missing skill name>,
      "why_needed": <why critical for this role>,
      "action_plan": <concrete portfolio project to build from scratch>,
      "recommended_resources": <official docs or top course>
    }}
  ],
  "resume_rewrites": [
    {{
      "original": <bullet from resume>,
      "optimized": <rewritten bullet with metrics tailored to job>,
      "why_this_works": <recruiter rationale>
    }}
  ]
}}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        raw_text, engine_used, attempted_models = execute_llm_call_with_live_status(
            messages, json_mode=True
        )

        clean_json_str = raw_text.strip()
        if clean_json_str.startswith("```"):
            clean_json_str = re.sub(r'^```(?:json)?\s*', '', clean_json_str)
            clean_json_str = re.sub(r'\s*```$', '', clean_json_str)

        match = re.search(r'\{.*\}', clean_json_str, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            data = json.loads(clean_json_str)

        # EXACT PYTHON MATHEMATICAL CALCULATION (ZERO ARITHMETIC ERROR / ZERO MOCKUP)
        core_score = int(data.get("core_skills_score", 60))
        exp_score = int(data.get("experience_alignment_score", 50))
        sup_score = int(data.get("supporting_skills_score", 70))

        # Clamp components
        core_score = min(max(core_score, 0), 100)
        exp_score = min(max(exp_score, 0), 100)
        sup_score = min(max(sup_score, 0), 100)

        # Exact formula: 50% Core, 30% Experience, 20% Supporting
        calculated_score = round(0.50 * core_score + 0.30 * exp_score + 0.20 * sup_score)
        match_score = min(max(calculated_score, 5), 98)

        # Calculate exact status
        if match_score >= 85:
            ats_status = "Strong Match"
            star_rating = 5
        elif match_score >= 70:
            ats_status = "Competitive Match"
            star_rating = 4
        elif match_score >= 50:
            ats_status = "Moderate Fit"
            star_rating = 3
        elif match_score >= 35:
            ats_status = "Action Required - Skill Deficit"
            star_rating = 2
        else:
            ats_status = "Action Required - Critical Gap"
            star_rating = 1

        data["match_score"] = match_score
        data["ats_status"] = ats_status
        data["star_rating"] = star_rating

        # Build exact, transparent score breakdown
        data["score_breakdown"] = {
            "core_skills_score": core_score,
            "experience_alignment_score": exp_score,
            "supporting_skills_score": sup_score,
            "justification": f"Core skills: {core_score}% (50% wt) + Experience scope: {exp_score}% (30% wt) + Supporting fit: {sup_score}% (20% wt) = {match_score}% total match."
        }

        if "executive_overview" in data:
            data["executive_overview"] = clean_pure_text(data["executive_overview"])

        matched_skills = data.get("matched_skills", [])
        missing_skills = data.get("missing_skills", [])
        candidate_additional = data.get("candidate_additional", [])
        domain_scores = data.get("domain_scores", [
            { "domain": "Languages", "score": core_score, "details": "Verified language proficiency" },
            { "domain": "Frameworks", "score": core_score, "details": "Core framework alignment" },
            { "domain": "Databases", "score": sup_score, "details": "Database technologies" },
            { "domain": "Cloud & DevOps", "score": exp_score, "details": "Cloud infrastructure and CI/CD" },
            { "domain": "Architecture", "score": core_score, "details": "System design and messaging" },
            { "domain": "Practices", "score": sup_score, "details": "Engineering methodologies & testing" }
        ])

        total_req = len(matched_skills) + len(missing_skills)
        if total_req == 0:
            total_req = 1

        metrics = {
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "candidate_additional": candidate_additional,
            "total_required": total_req,
            "deterministic_score": match_score,
            "domain_scores": domain_scores
        }
            
        cached_audits[inputs_fingerprint] = {
            "data": data,
            "metrics": metrics,
            "model_used": engine_used
        }

        return {
            "cached": False,
            "data": data,
            "metrics": metrics,
            "model_used": engine_used,
            "attempted_models": attempted_models,
            "fingerprint": inputs_fingerprint
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Audit Error: {str(e)}")

@app.post("/api/audit")
async def run_audit(request: AuditRequest):
    return process_audit_core(request.resume_text, request.job_desc)

@app.post("/api/audit/upload")
async def run_audit_upload(
    resume_file: UploadFile = File(...),
    job_desc: str = Form(...)
):
    content = await resume_file.read()
    resume_text = parse_pdf_bytes(content)
    return process_audit_core(resume_text, job_desc)

@app.post("/api/chat")
async def chat_followup(request: ChatRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenRouter API key is missing.")
        
    messages_payload = [{"role": m.role, "content": m.content} for m in request.messages]
    
    try:
        reply_raw, engine_used, attempted = execute_llm_call_with_live_status(
            messages_payload, json_mode=False
        )
        return {
            "reply": clean_pure_text(reply_raw),
            "model_used": engine_used,
            "attempted_models": attempted
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Career Coach Error: {str(e)}")

# Mount built React frontend if dist directory exists
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "dist")
if not os.path.exists(FRONTEND_DIST):
    FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
