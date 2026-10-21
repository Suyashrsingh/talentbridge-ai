import os
import re
import json
import hashlib
import urllib.request
import time
import streamlit as st
from openai import OpenAI
import httpx
import pypdf
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

st.set_page_config(
    page_title="TalentBridge AI - Career Matcher & Resume Auditor",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
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

def extract_competencies(text):
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

def compute_deterministic_score(resume_text, job_text, matched_skills, total_required):
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
    # Bound between 5% and 98%
    return min(max(final_score, 5), 98)

def compute_hybrid_match_metrics(resume_text, job_text):
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

# ----------------- MODERN DARK GLASS UI STYLING -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Dark Canvas */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background: radial-gradient(circle at 12% 10%, rgba(99, 102, 241, 0.20) 0%, transparent 45%),
                    radial-gradient(circle at 88% 14%, rgba(168, 85, 247, 0.18) 0%, transparent 45%),
                    radial-gradient(circle at 50% 90%, rgba(59, 130, 246, 0.14) 0%, transparent 55%),
                    #080A14 !important;
        color: #F8FAFC !important;
    }

    /* Hide Streamlit Default Chrome & ugly instruction text */
    header[data-testid="stHeader"], .stDeployButton, [data-testid="stToolbar"], #MainMenu, footer {
        display: none !important;
    }

    div[data-testid="InputInstructions"] {
        display: none !important;
    }

    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1220px !important;
    }

    /* Glossy Navbar */
    .glossy-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 28px;
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(28px) saturate(190%);
        -webkit-backdrop-filter: blur(28px) saturate(190%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.15), 0 12px 35px rgba(0, 0, 0, 0.4);
    }

    .brand-wrap {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .brand-logo {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        font-size: 1.35rem;
        font-weight: 800;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.5);
    }

    .brand-text {
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        color: #FFFFFF;
        margin: 0;
    }

    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 9999px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #34D399;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .status-pulse {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        display: inline-block;
    }

    /* Model Status Banner */
    .model-status-card {
        background: rgba(99, 102, 241, 0.10);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 14px;
        padding: 14px 20px;
        margin: 16px 0;
        display: flex;
        align-items: center;
        gap: 12px;
        color: #FFFFFF;
        font-size: 0.95rem;
    }

    .model-status-switch {
        background: rgba(245, 158, 11, 0.12) !important;
        border: 1px solid rgba(245, 158, 11, 0.4) !important;
        color: #FEF3C7 !important;
    }

    .model-status-success {
        background: rgba(16, 185, 129, 0.12) !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        color: #D1FAE5 !important;
    }

    /* High-Tech Generating Analysis Loader */
    .generating-loader-box {
        background: linear-gradient(135deg, rgba(30, 27, 75, 0.75) 0%, rgba(15, 23, 42, 0.90) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(139, 92, 246, 0.4);
        border-radius: 16px;
        padding: 22px 26px;
        margin: 18px 0 24px 0;
        box-shadow: 0 12px 35px rgba(99, 102, 241, 0.25), inset 0 1px 1px rgba(255, 255, 255, 0.15);
        animation: pulseBorder 2.4s infinite ease-in-out;
    }

    @keyframes pulseBorder {
        0%, 100% {
            border-color: rgba(139, 92, 246, 0.35);
            box-shadow: 0 8px 30px rgba(99, 102, 241, 0.2);
        }
        50% {
            border-color: rgba(168, 85, 247, 0.65);
            box-shadow: 0 12px 42px rgba(168, 85, 247, 0.4);
        }
    }

    .loader-header {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 14px;
    }

    .spinner-ring {
        width: 30px;
        height: 30px;
        border: 3px solid rgba(255, 255, 255, 0.15);
        border-top: 3px solid #8B5CF6;
        border-right: 3px solid #6366F1;
        border-radius: 50%;
        animation: ringSpin 0.85s linear infinite;
        flex-shrink: 0;
    }

    @keyframes ringSpin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .loader-title {
        font-size: 1.08rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.015em;
    }

    .loader-subtitle {
        font-size: 0.88rem;
        color: rgba(255, 255, 255, 0.78);
        margin-top: 3px;
    }

    .shimmer-progress-bar {
        width: 100%;
        height: 6px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 9999px;
        overflow: hidden;
        position: relative;
        margin-bottom: 14px;
    }

    .shimmer-progress-fill {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        width: 100%;
        background: linear-gradient(90deg, transparent, #8B5CF6, #6366F1, #EC4899, transparent);
        background-size: 200% 100%;
        animation: shimmerSlide 1.5s infinite linear;
    }

    @keyframes shimmerSlide {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    .loader-steps {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }

    .step-pill {
        font-size: 0.8rem;
        font-weight: 600;
        padding: 5px 13px;
        border-radius: 9999px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: rgba(255, 255, 255, 0.65);
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.25s ease;
    }

    .step-pill.active {
        background: rgba(139, 92, 246, 0.25);
        border-color: rgba(139, 92, 246, 0.55);
        color: #DDD6FE;
        box-shadow: 0 0 14px rgba(139, 92, 246, 0.3);
    }

    .step-pill.done {
        background: rgba(16, 185, 129, 0.18);
        border-color: rgba(16, 185, 129, 0.45);
        color: #6EE7B7;
    }

    /* Inputs & Textareas */
    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
    div[data-testid="stTextArea"] div[data-baseweb="textarea"],
    div[data-testid="stTextArea"] div[data-baseweb="base-input"],
    .stTextInput input,
    .stTextArea textarea {
        background-color: #0F172A !important;
        background: #0F172A !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        border-radius: 14px !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        padding: 14px !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.4) !important;
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #8B5CF6 !important;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.35) !important;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.035) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 16px !important;
        padding: 16px 20px !important;
        box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.12), 0 8px 24px rgba(0, 0, 0, 0.25) !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stMetric"]:hover {
        border-color: rgba(255, 255, 255, 0.18) !important;
        transform: translateY(-2px) !important;
    }

    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 2.1rem !important;
    }

    /* Native Alerts */
    div[data-testid="stAlert"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 12px !important;
        border-width: 1px !important;
        border-left-width: 4px !important;
        color: #F8FAFC !important;
        padding: 14px 18px !important;
        margin-bottom: 10px !important;
    }

    /* Primary Action Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #7C3AED 100%) !important;
        background-size: 200% 200% !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.45) !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
        font-size: 1.02rem !important;
        padding: 0.85rem 2rem !important;
        box-shadow: 0 10px 30px -5px rgba(99, 102, 241, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.2) !important;
        transition: all 0.25s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) scale(1.005) !important;
        box-shadow: 0 16px 40px -4px rgba(139, 92, 246, 0.7), inset 0 1px 1px rgba(255, 255, 255, 0.3) !important;
        background-position: right center !important;
    }

    .stButton > button:active {
        transform: translateY(1px) scale(0.99) !important;
    }

    /* ----------------- REFINED SEGMENTED PILL TABS ----------------- */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        padding: 5px !important;
        gap: 6px !important;
        margin-bottom: 24px !important;
        width: fit-content !important;
        max-width: 100% !important;
    }

    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: rgba(255, 255, 255, 0.65) !important;
        border-radius: 10px !important;
        font-size: 0.92rem !important;
        font-weight: 500 !important;
        padding: 8px 18px !important;
        border: none !important;
        background: transparent !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #FFFFFF !important;
        background: rgba(255, 255, 255, 0.04) !important;
    }

    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25) !important;
    }

    div[data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        background: transparent !important;
    }

    /* Footer */
    .glossy-footer {
        margin-top: 5rem;
        padding: 24px 30px;
        background: rgba(255, 255, 255, 0.025);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }

    .footer-left {
        color: rgba(255, 255, 255, 0.65);
        font-size: 0.9rem;
    }

    .footer-center {
        color: rgba(255, 255, 255, 0.92);
        font-size: 0.94rem;
        font-weight: 500;
    }

    .footer-author {
        color: #C084FC;
        font-weight: 700;
    }

    .footer-right {
        color: rgba(255, 255, 255, 0.65);
        font-size: 0.86rem;
    }

    /* ========================================================
       RESPONSIVE DESIGN & ADAPTIVE BREAKPOINTS
       Mobile (<640px) | Tablet (641px-1024px) | Desktop (>1024px)
       ======================================================== */

    /* Global Box Sizing & Fluid Container */
    *, *:before, *:after {
        box-sizing: border-box !important;
    }

    html, body {
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }

    /* Fluid Hero Typography */
    .hero-container {
        margin-bottom: 2rem;
    }

    .hero-title {
        font-size: clamp(1.65rem, 4.5vw, 2.5rem);
        font-weight: 800;
        letter-spacing: -0.04em;
        color: #FFFFFF;
        margin: 0 0 8px 0;
        line-height: 1.18;
    }

    .hero-subtitle {
        font-size: clamp(0.92rem, 2vw, 1.05rem);
        color: rgba(255, 255, 255, 0.72);
        margin: 0 0 1.8rem 0;
        line-height: 1.55;
    }

    /* Mobile-first / Adaptive Tablet (<= 1024px) */
    @media (max-width: 1024px) {
        .block-container {
            padding-top: 1.4rem !important;
            padding-bottom: 2.8rem !important;
            padding-left: 1.25rem !important;
            padding-right: 1.25rem !important;
        }

        .glossy-navbar {
            padding: 14px 22px;
            margin-bottom: 1.6rem;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.7rem !important;
        }
    }

    /* Mobile Breakpoint (<= 640px) */
    @media (max-width: 640px) {
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
        }

        /* Navbar stacks on small screens */
        .glossy-navbar {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
            padding: 14px 16px;
            border-radius: 16px;
            margin-bottom: 1.25rem;
        }

        .brand-wrap {
            gap: 10px;
        }

        .brand-logo {
            width: 36px;
            height: 36px;
            font-size: 1.15rem;
            border-radius: 10px;
        }

        .brand-text {
            font-size: 1.18rem;
        }

        .status-badge {
            width: 100%;
            justify-content: center;
            font-size: 0.76rem;
            padding: 6px 12px;
            text-align: center;
        }

        /* Hero */
        .hero-container {
            margin-bottom: 1.4rem;
        }

        /* Generating Loader Mobile */
        .generating-loader-box {
            padding: 16px 16px;
            border-radius: 14px;
            margin: 14px 0 18px 0;
        }

        .loader-header {
            gap: 12px;
            margin-bottom: 12px;
        }

        .spinner-ring {
            width: 24px;
            height: 24px;
            border-width: 2.5px;
        }

        .loader-title {
            font-size: 0.98rem;
            line-height: 1.3;
        }

        .loader-subtitle {
            font-size: 0.82rem;
            line-height: 1.35;
        }

        .loader-steps {
            gap: 6px;
            flex-direction: column;
        }

        .step-pill {
            width: 100%;
            justify-content: flex-start;
            font-size: 0.76rem;
            padding: 5px 10px;
        }

        /* Metric Cards on Mobile */
        [data-testid="stMetric"] {
            padding: 12px 14px !important;
            border-radius: 14px !important;
            margin-bottom: 8px !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.78rem !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.45rem !important;
            line-height: 1.2 !important;
        }

        /* Chat Form On Mobile */
        div[data-testid="stForm"] div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 8px !important;
        }

        /* Footer on Mobile */
        .glossy-footer {
            flex-direction: column;
            text-align: center;
            gap: 12px;
            padding: 18px 16px;
            margin-top: 2.5rem;
            border-radius: 16px;
        }

        .footer-left, .footer-center, .footer-right {
            text-align: center;
            width: 100%;
            font-size: 0.82rem;
        }
    }

    /* Swipeable / Scrollable Pill Tabs on Small Devices */
    .stTabs [data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
        padding: 5px !important;
        gap: 6px !important;
        margin-bottom: 22px !important;
        width: 100% !important;
        max-width: 100% !important;
        border-radius: 14px !important;
    }

    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
        display: none !important;
    }

    .stTabs [data-baseweb="tab"] {
        white-space: nowrap !important;
        flex-shrink: 0 !important;
        font-size: 0.88rem !important;
        padding: 8px 14px !important;
    }

    /* Fluid Inputs & Radio buttons */
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input {
        width: 100% !important;
        box-sizing: border-box !important;
    }

    div[role="radiogroup"] {
        flex-wrap: wrap !important;
        gap: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE & DETERMINISTIC CACHE -----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "hybrid_metrics" not in st.session_state:
    st.session_state.hybrid_metrics = None
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "job_desc" not in st.session_state:
    st.session_state.job_desc = ""
if "cached_audits" not in st.session_state:
    st.session_state.cached_audits = {}

# ----------------- DYNAMIC MODEL CATALOG -----------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_available_models(api_key):
    if not api_key:
        return []
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}", "HTTP-Referer": "http://localhost:8501", "X-Title": "TalentBridge"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [m["id"] for m in data.get("data", [])]
    except Exception:
        return []

all_openrouter_models = fetch_available_models(OPENROUTER_API_KEY)
total_model_count = len(all_openrouter_models) if all_openrouter_models else 460

def parse_pdf(file):
    try:
        reader = pypdf.PdfReader(file)
        return "\n".join([page.extract_text() or "" for page in reader.pages]).strip()
    except Exception as e:
        st.error(f"Error parsing PDF: {e}")
        return ""

def execute_llm_call_with_live_status(messages, json_mode=False, status_placeholder=None, status_callback=None):
    """Executes LLM call with live status notices and model failover."""
    primary_chain = [
        "deepseek/deepseek-chat",
        "openai/gpt-4o-mini",
        "meta-llama/llama-3.3-70b-instruct",
        "qwen/qwen-2.5-72b-instruct"
    ]
    
    active_pool = [m for m in primary_chain if not all_openrouter_models or m in all_openrouter_models]
    if not active_pool:
        active_pool = primary_chain
        
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        timeout=httpx.Timeout(60.0, connect=15.0),
        max_retries=1,
        default_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "TalentBridge"}
    )
    
    last_exception = None
    for i, model_name in enumerate(active_pool):
        if status_callback is not None:
            if i == 0:
                status_callback("querying", model_name, None)
            else:
                prev_model = active_pool[i - 1]
                status_callback("switching", model_name, prev_model)
        elif status_placeholder is not None:
            if i == 0:
                status_placeholder.markdown(f"""
                <div class="model-status-card">
                    <span class="status-pulse"></span>
                    Querying AI Model: <strong>{model_name}</strong>...
                </div>
                """, unsafe_allow_html=True)
            else:
                prev_model = active_pool[i - 1]
                status_placeholder.markdown(f"""
                <div class="model-status-card model-status-switch">
                    <span class="status-pulse" style="background-color: #F59E0B;"></span>
                    <span><strong>{prev_model}</strong> busy or unavailable &bull; <em>Switching model to {model_name}...</em></span>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.5)

        try:
            kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.0  # Zero temperature for deterministic responses
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
                
            response = client.chat.completions.create(**kwargs)
            
            if status_callback is not None:
                status_callback("success", model_name, None)
            elif status_placeholder is not None:
                status_placeholder.markdown(f"""
                <div class="model-status-card model-status-success">
                    <span class="status-pulse"></span>
                    Verified &bull; Generated response using <strong>{model_name}</strong>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.5)
                status_placeholder.empty()

            return response.choices[0].message.content, model_name

        except Exception as e:
            last_exception = e
            continue
            
    if status_placeholder is not None:
        status_placeholder.empty()
    raise last_exception

def clean_pure_text(text):
    if not text:
        return ""
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'\*{1,3}', '', text)
    text = re.sub(r'^(Certainly!|Here is your|Sure,|As requested|Hello!)[^\n]*\n+', '', text, flags=re.IGNORECASE)
    return text.strip()

# ----------------- 1. TOP NAVBAR -----------------
st.markdown(f"""
<div class="glossy-navbar">
    <div class="brand-wrap">
        <div class="brand-logo">✦</div>
        <div class="brand-text">TalentBridge AI</div>
    </div>
    <div class="status-badge">
        <span class="status-pulse"></span> Deterministic Scoring Active &bull; {total_model_count}+ Models
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- 2. HERO SECTION -----------------
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">Resume Matcher &amp; Roadmap</h1>
    <p class="hero-subtitle">Deterministic competency auditing, what to add/remove, and targeted upskilling roadmaps.</p>
</div>
""", unsafe_allow_html=True)

# ----------------- 3. INPUT WORKSPACE -----------------
col_resume, col_job = st.columns(2, gap="large")

with col_resume:
    st.markdown("**📄 Candidate Resume**")
    input_type = st.radio("Resume input type", ["Upload PDF", "Paste Text"], horizontal=True, label_visibility="collapsed")
    
    if input_type == "Upload PDF":
        pdf_file = st.file_uploader("Upload resume file", type=["pdf"], label_visibility="collapsed")
        if pdf_file is not None:
            extracted = parse_pdf(pdf_file)
            if extracted:
                st.session_state.resume_text = extracted
                st.success(f"✓ Parsed `{pdf_file.name}` ({len(extracted.split())} words)")
    else:
        st.session_state.resume_text = st.text_area(
            "Resume text",
            value=st.session_state.resume_text,
            height=200,
            placeholder="Paste your education, skills, work experience, and projects here...",
            label_visibility="collapsed"
        )

with col_job:
    st.markdown("**💼 Target Job Description**")
    st.session_state.job_desc = st.text_area(
        "Job description text",
        value=st.session_state.job_desc,
        height=252,
        placeholder="Paste role responsibilities, required programming languages, tools, and qualifications...",
        label_visibility="collapsed"
    )

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

analyze_clicked = st.button("✦ Run Complete Resume Audit & Roadmap Analysis", use_container_width=True)
status_banner = st.empty()

# ----------------- 4. COMPREHENSIVE AUDIT EXECUTION (DETERMINISTIC & CACHED) -----------------
if analyze_clicked:
    if not OPENROUTER_API_KEY:
        st.error("OpenRouter API key is missing. Please add it to your .env file.")
    elif not st.session_state.resume_text.strip():
        st.warning("Please upload a PDF or paste your resume.")
    elif not st.session_state.job_desc.strip():
        st.warning("Please paste the target job description.")
    else:
        def render_audit_loader(stage_title, details_text, step_num=1, is_switch=False):
            step1_class = "done" if step_num > 1 else ("active" if step_num == 1 else "")
            step2_class = "done" if step_num > 2 else ("active" if step_num == 2 else "")
            step3_class = "done" if step_num > 3 else ("active" if step_num == 3 else "")
            
            border_style = "border-color: rgba(245, 158, 11, 0.6); box-shadow: 0 0 32px rgba(245, 158, 11, 0.3);" if is_switch else ""
            spinner_style = "border-top-color: #F59E0B; border-right-color: #F59E0B;" if is_switch else ""
            
            status_banner.markdown(f"""
            <div class="generating-loader-box" style="{border_style}">
                <div class="loader-header">
                    <div class="spinner-ring" style="{spinner_style}"></div>
                    <div>
                        <div class="loader-title">{stage_title}</div>
                        <div class="loader-subtitle">{details_text}</div>
                    </div>
                </div>
                <div class="shimmer-progress-bar">
                    <div class="shimmer-progress-fill"></div>
                </div>
                <div class="loader-steps">
                    <span class="step-pill {step1_class}">
                        {'✓' if step_num > 1 else '⚙️'} 1. Competency Extraction
                    </span>
                    <span class="step-pill {step2_class}">
                        {'✓' if step_num > 2 else '⚙️'} 2. Multi-Agent Reasoning
                    </span>
                    <span class="step-pill {step3_class}">
                        {'✓' if step_num > 3 else '✦'} 3. Roadmap &amp; Rewrites
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Create unique fingerprint hash of the exact resume + job description
        inputs_fingerprint = hashlib.sha256(
            (st.session_state.resume_text.strip().lower() + "|||" + st.session_state.job_desc.strip().lower()).encode("utf-8")
        ).hexdigest()
        
        # Check if identical inputs were already audited
        if inputs_fingerprint in st.session_state.cached_audits:
            cached_entry = st.session_state.cached_audits[inputs_fingerprint]
            render_audit_loader(
                "Instant Retrieval &bull; Verified Analysis Ready",
                f"Identical resume and job inputs detected &bull; <strong>Stable score locked at {cached_entry['data']['match_score']}%.</strong>",
                step_num=3
            )
            time.sleep(0.5)
            st.session_state.audit_data = cached_entry["data"]
            st.session_state.hybrid_metrics = cached_entry["metrics"]
            status_banner.empty()
            st.rerun()
            
        try:
            # Immediate feedback: Scanning & Competency Extraction
            render_audit_loader(
                "Analyzing Resume & Cross-Referencing Job Spec...",
                "Scanning technical keywords, extracting competencies, and calculating deterministic ATS score...",
                step_num=1
            )
            time.sleep(0.3)
            
            # 1. Deterministic Overlap Computation & Stable Mathematical Score
            metrics = compute_hybrid_match_metrics(st.session_state.resume_text, st.session_state.job_desc)
            st.session_state.hybrid_metrics = metrics
            deterministic_score = metrics["deterministic_score"]
            
            # Grounded ATS standing based strictly on deterministic score
            if deterministic_score >= 75:
                stable_ats_status = "High Alignment"
            elif deterministic_score >= 50:
                stable_ats_status = "Moderate Fit"
            else:
                stable_ats_status = "Action Required - High Skill Deficit"
            
            matched_str = ", ".join(metrics["matched_skills"]) if metrics["matched_skills"] else "None explicitly found"
            missing_str = ", ".join(metrics["missing_skills"]) if metrics["missing_skills"] else "None explicitly found"
            
            # 2. Strict Prompting with Locked Score
            system_prompt = (
                "You are TalentBridge AI, an elite ATS Algorithm Specialist and Senior Silicon Valley Technical Director. "
                "You perform rigorous, comprehensive resume audits against target job descriptions. "
                f"The exact deterministic match score for this candidate is mathematically fixed at {deterministic_score}%. "
                f"The qualification status is fixed at '{stable_ats_status}'. "
                "CRITICAL INSTRUCTIONS:\n"
                f"1. Set 'match_score' strictly to {deterministic_score}.\n"
                f"2. Set 'ats_status' strictly to '{stable_ats_status}'.\n"
                "3. Explicitly specify 'what_to_add' to the resume (specific keywords, metrics, projects, links).\n"
                "4. Explicitly specify 'what_to_remove' from the resume (irrelevant coursework, generic buzzwords, passive phrases).\n"
                "5. Explicitly specify 'what_to_skill_up' with prioritized milestones, reasons, action projects, and official learning resources.\n"
                "6. Provide 2 Before and After resume bullet transformations.\n"
                "7. Respond purely in valid JSON format without markdown wrapping."
            )
            
            user_prompt = f"""
AUDIT THIS CANDIDATE RESUME AGAINST THIS JOB DESCRIPTION:

MATHEMATICALLY VERIFIED GROUND TRUTH DATA:
- Fixed Deterministic Score: {deterministic_score}%
- Fixed Status: {stable_ats_status}
- Matched Skills: [{matched_str}]
- Missing Required Skills: [{missing_str}]
- Total Core Skills Evaluated: {metrics['total_required']}

FULL CANDIDATE RESUME:
{st.session_state.resume_text}

FULL JOB SPECIFICATION:
{st.session_state.job_desc}

Return a valid JSON object with the following exact keys:
{{
  "match_score": {deterministic_score},
  "ats_status": "{stable_ats_status}",
  "executive_overview": <candid, realistic 2-3 sentence overview of candidate qualifications for this role reflecting the {deterministic_score}% score>,
  "verified_strengths": [<list of 3 to 4 specific technical strengths verified on resume>],
  "what_to_add": [<list of 4 to 6 specific items to ADD to the resume: missing tech keywords, quantifiable metrics, sections, links>],
  "what_to_remove": [<list of 3 to 5 specific items to REMOVE from the resume: subjective buzzwords, outdated info, passive language>],
  "what_to_skill_up": [
    {{
      "priority": <"High Priority" | "Medium Priority">,
      "skill": <missing technology name>,
      "why_needed": <why this skill is critical for the target role>,
      "action_plan": <concrete mini-project or repository to build for proof-of-work>,
      "recommended_resources": <recommended official documentation or free course>
    }}
  ],
  "resume_rewrites": [
    {{
      "original": <bullet point from resume that needs improvement>,
      "optimized": <high-impact rewritten bullet point with action verbs and metrics tailored to target role>,
      "why_this_works": <recruiter rationale>
    }},
    {{
      "original": <second bullet point from resume>,
      "optimized": <second rewritten bullet point>,
      "why_this_works": <recruiter rationale>
    }}
  ]
}}
"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            def on_audit_status(status_type, model_name, prev_model=None):
                if status_type == "querying":
                    render_audit_loader(
                        f"AI Agent Generating Analysis ({model_name})...",
                        "Synthesizing executive fit assessment, additions, removals, and targeted roadmap...",
                        step_num=2
                    )
                elif status_type == "switching":
                    render_audit_loader(
                        f"Switching AI Model to {model_name}...",
                        f"{prev_model} busy or timed out &bull; Seamlessly switching to next model...",
                        step_num=2,
                        is_switch=True
                    )
                    time.sleep(0.5)
                elif status_type == "success":
                    render_audit_loader(
                        f"Structuring Recommendations ({model_name})...",
                        "Formatting executive overview, targeted additions, and bullet rewrites...",
                        step_num=3
                    )
                    time.sleep(0.4)

            raw_text, engine_used = execute_llm_call_with_live_status(
                messages, 
                json_mode=True, 
                status_placeholder=status_banner,
                status_callback=on_audit_status
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
                
            # Strictly lock match_score & ats_status to deterministic calculation
            data["match_score"] = deterministic_score
            data["ats_status"] = stable_ats_status
            
            st.session_state.audit_data = data
            
            # Cache this audit by input fingerprint
            st.session_state.cached_audits[inputs_fingerprint] = {
                "data": data,
                "metrics": metrics
            }
            
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": f"You are TalentBridge AI. Verified match score is mathematically locked at {deterministic_score}%. "
                               f"Matched skills: {matched_str}. Missing skills: {missing_str}. "
                               f"Summary: {data.get('executive_overview', '')}. "
                               f"Answer candidate follow-ups directly, professionally, in clean text without HTML tags, hashtags, or asterisks."
                },
                {
                    "role": "assistant",
                    "content": f"Audit complete. Your ATS match score is mathematically verified and locked at **{deterministic_score}%** (processed via {engine_used}). Review the comprehensive overview, additions, removals, and upskilling plan below."
                }
            ]
            render_audit_loader(
                "Analysis Complete! Rendering Dashboard...",
                f"Stable score locked at {deterministic_score}% &bull; Preparing roadmap...",
                step_num=4
            )
            time.sleep(0.4)
            status_banner.empty()
            st.rerun()

        except Exception as e:
            status_banner.empty()
            st.error(
                f"⚠️ **Network or Model Notice:** {e}\n\n"
                "Please check your internet connection and click **✦ Run Complete Resume Audit & Roadmap Analysis** again."
            )

# ----------------- 5. CLEAN TEXT OVERVIEW & ANALYSIS DASHBOARD -----------------
if st.session_state.audit_data and st.session_state.hybrid_metrics:
    data = st.session_state.audit_data
    metrics = st.session_state.hybrid_metrics
    score_val = data.get("match_score", metrics["deterministic_score"])
    ats_status = data.get("ats_status", "Moderate Fit")
    
    st.markdown("---")
    
    # 1. High-Level Metrics (Clean Streamlit Native Cards)
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("ATS Match Score (Locked)", f"{score_val}%")
    m_col2.metric("Qualification Standing", ats_status)
    m_col3.metric("Verified Skill Overlap", f"{len(metrics['matched_skills'])} of {metrics['total_required']} Core Skills")
    
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    
    # 2. Sleek Segmented Pill Tabs
    tab_overview, tab_add, tab_remove, tab_skillup, tab_rewrites = st.tabs([
        "Overview",
        "What to Add",
        "What to Remove",
        "Upskilling Plan",
        "Bullet Rewrites"
    ])
    
    # TAB 1: Executive Overview & Strengths
    with tab_overview:
        st.subheader("Executive Fit Assessment")
        st.write(data.get("executive_overview", "Audit assessment completed."))
        
        st.markdown("### Verified Candidate Strengths")
        strengths = data.get("verified_strengths", [])
        if strengths:
            for s in strengths:
                st.success(f"✓ {s}")
        else:
            st.write("No direct strengths verified for this specific technical role.")
            
        st.markdown("### Technical Competencies Detected")
        col_m, col_g = st.columns(2)
        with col_m:
            st.write("**Matched on Resume:**")
            if metrics["matched_skills"]:
                for s in metrics["matched_skills"]:
                    st.write(f"- {s}")
            else:
                st.write("*No direct required technology overlap detected.*")
        with col_g:
            st.write("**Missing from Resume:**")
            if metrics["missing_skills"]:
                for s in metrics["missing_skills"]:
                    st.write(f"- {s}")
            else:
                st.write("*All required technologies satisfied.*")
                
    # TAB 2: What to Add to Resume
    with tab_add:
        st.subheader("What to ADD to Your Resume")
        st.write("Adding these specific technical keywords, quantifiable performance metrics, and portfolio links will directly improve your alignment with this role and boost ATS ranking:")
        add_items = data.get("what_to_add", [])
        for item in add_items:
            st.info(f"➕ {item}")
            
    # TAB 3: What to Remove from Resume
    with tab_remove:
        st.subheader("What to REMOVE or REPHRASE on Your Resume")
        st.write("Removing irrelevant coursework, subjective buzzwords, and passive phrasing keeps your resume concise, engineering-focused, and recruiter-friendly:")
        remove_items = data.get("what_to_remove", [])
        for item in remove_items:
            st.warning(f"➖ {item}")
            
    # TAB 4: What to Skill Up (Targeted Roadmap)
    with tab_skillup:
        st.subheader("Targeted Upskilling Plan")
        st.write("Follow this prioritized sequence to master missing competencies and build verifiable proof-of-work repositories:")
        skill_steps = data.get("what_to_skill_up", [])
        for i, step in enumerate(skill_steps, start=1):
            with st.container():
                priority = step.get("priority", "High Priority")
                skill_name = step.get("skill", f"Skill {i}")
                st.markdown(f"#### Milestone {i}: {skill_name} ({priority})")
                st.write(f"**Why Needed:** {step.get('why_needed', '')}")
                st.write(f"**Action Plan / Project:** {step.get('action_plan', '')}")
                st.write(f"**Recommended Resources:** {step.get('recommended_resources', '')}")
                st.divider()
                
    # TAB 5: Resume Bullet Rewrites
    with tab_rewrites:
        st.subheader("High-Impact Bullet Point Transformations")
        st.write("Convert descriptive student or passive tasks into high-impact, metric-driven engineering bullets that pass ATS algorithms:")
        rewrites = data.get("resume_rewrites", [])
        for rw in rewrites:
            c_orig, c_opt = st.columns(2)
            with c_orig:
                st.error(f"**Current Phrasing (Before):**\n\n{rw.get('original', '')}")
            with c_opt:
                st.success(f"**ATS-Optimized Phrasing (After):**\n\n{rw.get('optimized', '')}")
            st.write(f"**Recruiter Rationale:** {rw.get('why_this_works', '')}")
            st.divider()

    # 3. Download Clean Report (.txt)
    report_text = f"""TALENTBRIDGE RESUME AUDIT & ROADMAP REPORT
=============================================================
MATCH SCORE (LOCKED): {score_val}%
ATS STATUS: {ats_status}
VERIFIED OVERLAP: {len(metrics['matched_skills'])} of {metrics['total_required']} Core Technologies

1. EXECUTIVE OVERVIEW
-------------------------------------------------------------
{data.get('executive_overview', '')}

Verified Strengths:
"""
    for s in data.get('verified_strengths', []):
        report_text += f"- {s}\n"
        
    report_text += """
2. WHAT TO ADD TO YOUR RESUME
-------------------------------------------------------------
"""
    for item in data.get('what_to_add', []):
        report_text += f"+ {item}\n"
        
    report_text += """
3. WHAT TO REMOVE FROM YOUR RESUME
-------------------------------------------------------------
"""
    for item in data.get('what_to_remove', []):
        report_text += f"- {item}\n"
        
    report_text += """
4. WHAT TO SKILL UP (UPSKILLING PLAN)
-------------------------------------------------------------
"""
    for step in data.get('what_to_skill_up', []):
        report_text += f"[{step.get('priority', 'Priority')}] {step.get('skill', '')}\n"
        report_text += f"  Why Needed: {step.get('why_needed', '')}\n"
        report_text += f"  Action Plan: {step.get('action_plan', '')}\n"
        report_text += f"  Resources: {step.get('recommended_resources', '')}\n\n"
        
    report_text += """
5. RESUME BULLET REWRITES
-------------------------------------------------------------
"""
    for rw in data.get('resume_rewrites', []):
        report_text += f"Before: {rw.get('original')}\n"
        report_text += f"After:  {rw.get('optimized')}\n"
        report_text += f"Reason: {rw.get('why_this_works')}\n\n"

    st.download_button(
        label="📥 Download Full Executive Audit Report (.txt)",
        data=report_text,
        file_name="TalentBridge_Audit_Report.txt",
        mime="text/plain",
        use_container_width=True
    )

    # ----------------- 6. FOLLOW-UP COACH (CLEAN CHAT FLOW) -----------------
    st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True)
    st.markdown("### 💬 Interactive Follow-Up Coach")
    st.write("Ask follow-up questions, request customized interview preparation, or ask for guidance on specific bullet points:")
    
    q1, q2, q3 = st.columns(3)
    quick_choice = None
    with q1:
        if st.button("🎯 5 Technical Interview Qs", use_container_width=True):
            quick_choice = "Provide 5 technical interview questions targeting my identified missing skills along with model answers in clean text without HTML tags or asterisks."
    with q2:
        if st.button("✉️ Draft Custom Cover Letter", use_container_width=True):
            quick_choice = "Write a professional, persuasive cover letter tailored to this role that highlights my strengths and bridges skill gaps in clean text without HTML tags or asterisks."
    with q3:
        if st.button("🛠️ Project Architecture Blueprint", use_container_width=True):
            quick_choice = "Give me a technical architecture blueprint and folder structure for the recommended proof-of-work project in clean text without HTML tags or asterisks."
            
    # Conversation History
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            role_title = "You (Candidate)" if msg["role"] == "user" else "TalentBridge Coach"
            with st.chat_message(msg["role"]):
                st.write(f"**{role_title}:**")
                st.write(clean_pure_text(msg['content']))
            
    # Clean Inline Input Bar
    chat_status = st.empty()
    with st.form("clean_chat_bar", clear_on_submit=True):
        c_input, c_btn = st.columns([5, 1])
        with c_input:
            typed_msg = st.text_input(
                "Follow up question",
                placeholder="Ask about your roadmap, interview prep, or resume bullet rewrites...",
                label_visibility="collapsed"
            )
        with c_btn:
            submit_btn = st.form_submit_button("Ask ➔", use_container_width=True)
            
    active_prompt = quick_choice or (typed_msg if submit_btn and typed_msg.strip() else None)
    
    if active_prompt:
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        try:
            reply_raw, _ = execute_llm_call_with_live_status(
                st.session_state.messages, 
                json_mode=False, 
                status_placeholder=chat_status
            )
            reply = clean_pure_text(reply_raw)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
        except Exception as e:
            st.error(f"⚠️ Connection notice: {e}")

# ----------------- 7. FOOTER (ALWAYS AT THE VERY BOTTOM) -----------------
st.markdown("""
<div class="glossy-footer">
    <div class="footer-left">
        &copy; 2026 <strong>TalentBridge AI</strong> &bull; All rights reserved.
    </div>
    <div class="footer-center">
        Made with <span style="color: #EC4899; font-size: 1.1rem;">&hearts;</span> by <span class="footer-author">Suyash Singh &amp; Shubhada Shingane</span>
    </div>
    <div class="footer-right">
        AI Agent Development &bull; CSE Department
    </div>
</div>
""", unsafe_allow_html=True)
