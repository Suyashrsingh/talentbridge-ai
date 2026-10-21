# TalentBridge AI 🎯
### Intelligent Resume Checker, Job Matcher & Skill Gap Roadmap Platform
**B.Tech CSE Practical Experiment No. 10: AI Agent Development**

Developed with ❤️ by **Suyash Singh & Shubhada Shingane** (CSE Department)

[![TalentBridge AI CI/CD Pipeline](https://github.com/Suyashrsingh/talentbridge-ai/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Suyashrsingh/talentbridge-ai/actions/workflows/ci-cd.yml)
[![Deployed on Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black?logo=vercel)](https://vercel.com)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Tailwind-61DAFB?logo=react)](https://react.dev)

---

## 📌 Project Overview
**TalentBridge AI** is a production-grade full-stack AI career platform that bridges the gap between candidate resumes and modern job requirements. It performs rigorous semantic audits, calculates exact and calibrated ATS match scores across 6 technical domains, and builds concrete upskilling roadmaps with proof-of-work project blueprints for every missing skill.

---

## 🏗️ System Architecture

```text
       +-------------------------------------------------------------+
       |                  Candidate / User                           |
       +------------------------------+------------------------------+
                                      | (PDF Resume / Text / Job Spec)
                                      v
       +-------------------------------------------------------------+
       |               React + Tailwind CSS Frontend                 |
       |  (Glassmorphism, Lucide Icons, Real-time Multi-Stage Loader)|
       +------------------------------+------------------------------+
                                      | (REST / Multipart POST)
                                      v
       +-------------------------------------------------------------+
       |               FastAPI Python Serverless API                 |
       |   (PDF Parser, 50/30/20 Calibrated Scoring, SHA-256 Cache)  |
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |             OpenRouter Multi-Model Gateway                  |
       | (GPT-4o-mini / DeepSeek Chat / LLaMA-3.3-70B / Qwen-2.5-72B)|
       +------------------------------+------------------------------+
                                      |
                                      v
       +-------------------------------------------------------------+
       |   Structured Report & Interactive Career Coach Chatbot      |
       +-------------------------------------------------------------+
```

---

## 📁 Project Structure (Vercel Ready)

```text
talentbridge-ai/
├── .github/
│   └── workflows/
│       └── ci-cd.yml             # GitHub Actions CI/CD pipeline
├── api/
│   ├── index.py                  # Vercel Python Serverless Function entrypoint
│   └── requirements.txt          # Serverless Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.tsx               # Main React Application & UI components
│   │   ├── main.tsx              # React DOM entry
│   │   └── index.css             # Glassmorphism, animations & Tailwind styles
│   ├── package.json              # Frontend dependencies & scripts
│   ├── tailwind.config.js        # Tailwind CSS theme configuration
│   └── vite.config.ts            # Vite bundler & dev proxy config
├── server.py                     # FastAPI Core Application & ATS Engine
├── requirements.txt              # Project Python dependencies
├── vercel.json                   # Vercel deployment routes & build rules
├── package.json                  # Root build runner for Vercel
├── .gitignore                    # Ignored files (node_modules, .env, dist)
└── README.md                     # Documentation
```

---

## 🚀 Deployment on Vercel

### Method 1: Import via Vercel Dashboard (Recommended)
1. Go to [Vercel Dashboard](https://vercel.com/new).
2. Import this repository: `https://github.com/Suyashrsingh/talentbridge-ai`.
3. In **Environment Variables**, add:
   - `OPENROUTER_API_KEY`: Your OpenRouter API key.
4. Click **Deploy**. Vercel will automatically build the React frontend and deploy the FastAPI backend as a serverless function!

### Method 2: Deploy via Vercel CLI
```bash
npm install -g vercel
vercel
```

---

## 💻 Local Development Setup

### 1. Clone & Configure Environment
```bash
git clone https://github.com/Suyashrsingh/talentbridge-ai.git
cd talentbridge-ai
cp .env.example .env
# Edit .env and paste your OPENROUTER_API_KEY
```

### 2. Start FastAPI Backend
```bash
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```
API runs on: **http://localhost:8000** (Interactive Swagger docs: **http://localhost:8000/docs**)

### 3. Start React Frontend
```bash
cd frontend
npm install
npm run dev
```
UI runs on: **http://localhost:5173** (Proxies `/api` calls directly to port 8000)

---

## 🌟 Key Technical Features

1. **Accurate & Calibrated ATS Scoring (Zero Mockups):**
   - Strictly computed via:
     $$\text{Match Score} = \text{round}(0.50 \times S_{\text{core}} + 0.30 \times S_{\text{experience}} + 0.20 \times S_{\text{supporting}})$$
   - Transparent breakdown shown for Core Skills, Experience Scope, and Supporting Qualifications.
   - Real multi-point SVG curve plotted across 6 technical domains: Languages, Frameworks, Databases, Cloud & DevOps, Architecture, and Practices.

2. **Targeted Upskilling Roadmap:**
   - Every detected skill gap automatically generates a prioritized milestone with:
     - Clear justification of why the target company requires it.
     - Concrete, real-world proof-of-work project to build on GitHub.
     - Direct links to official documentation and tutorials.

3. **Ultra-Glossy Translucent UI:**
   - Designed to executive SaaS standards (Apple / Linear / Stripe aesthetics).
   - Specular reflections, ambient aurora light orbs, and responsive segmented tabs.

4. **Interactive Career Advisor Chatbot:**
   - Follow-up interview coaching, project architecture blueprints, and cover letter generation.

---

## 👥 Authors
- **Suyash Singh** ([GitHub](https://github.com/Suyashrsingh))
- **Shubhada Shingane**
