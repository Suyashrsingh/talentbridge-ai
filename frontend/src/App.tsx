import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, 
  Upload, 
  FileText, 
  CheckCircle2, 
  XCircle, 
  ArrowRight, 
  Download, 
  RefreshCw, 
  Send, 
  Bot, 
  Briefcase, 
  BookOpen, 
  Target, 
  Zap, 
  TrendingUp, 
  FileCheck, 
  Star, 
  Layers, 
  Award, 
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Compass
} from 'lucide-react';
import confetti from 'canvas-confetti';

interface SkillStep {
  priority: string;
  skill: string;
  why_needed: string;
  action_plan: string;
  recommended_resources: string;
}

interface RewriteItem {
  original: string;
  optimized: string;
  why_this_works: string;
}

interface DomainScore {
  domain: string;
  score: number;
  details: string;
}

interface ScoreBreakdown {
  core_skills_score: number;
  experience_alignment_score: number;
  supporting_skills_score: number;
  justification: string;
}

interface AuditData {
  match_score: number;
  ats_status: string;
  star_rating?: number;
  domain_scores?: DomainScore[];
  executive_overview: string;
  score_breakdown?: ScoreBreakdown;
  verified_strengths: string[];
  what_to_add: string[];
  what_to_remove: string[];
  what_to_skill_up: SkillStep[];
  resume_rewrites: RewriteItem[];
}

interface HybridMetrics {
  matched_skills: string[];
  missing_skills: string[];
  candidate_additional: string[];
  total_required: number;
  deterministic_score: number;
  domain_scores?: DomainScore[];
}

interface ChatMsg {
  role: 'user' | 'assistant' | 'system';
  content: string;
  model_used?: string;
}

const SAMPLE_RESUME = `Experienced Software Engineer with 2+ years building backend systems and cloud services.
Education: B.Tech in Computer Science and Engineering (2024)

Skills:
- Languages: Python, JavaScript, TypeScript, SQL
- Frameworks: Django, FastAPI, Express.js, Node.js
- Databases: PostgreSQL, MongoDB, Redis
- Cloud & DevOps: Docker, Git, GitHub Actions, Linux, AWS (EC2, S3)
- Practices: REST APIs, Microservices, Agile, Unit Testing (PyTest)

Experience:
Backend Developer at TechSolutions (2024 - Present):
- Developed and maintained microservices using Python FastAPI and PostgreSQL.
- Implemented Redis caching layer reducing API response latency by 45%.
- Containerized applications using Docker and set up automated CI/CD pipelines.
- Wrote comprehensive unit tests achieving 88% test coverage.

Projects:
- Distributed Task Queue: Built a Celery-like asynchronous queue in Python using Redis and WebSockets.
- E-Commerce Microservices: Scalable shopping platform with JWT authentication and Stripe integration.`;

const SAMPLE_JOB = `Senior Backend Engineer (Python / Cloud)

About the Role:
We are looking for a skilled Backend Engineer to scale our distributed cloud microservices. 

Responsibilities:
- Design, build, and optimize high-throughput REST APIs and messaging architectures.
- Collaborate with frontend and DevOps engineers to deploy services to Kubernetes clusters.
- Manage relational and NoSQL databases, optimizing queries and data pipelines.

Requirements:
- Bachelor's or Master's degree in Computer Science, Engineering, or equivalent practical experience.
- Strong proficiency in Python, FastAPI, and PostgreSQL.
- Experience with Docker, Kubernetes (K8s), and cloud platforms (AWS / GCP).
- Experience with Kafka or RabbitMQ event-driven architecture.
- Solid understanding of CI/CD pipelines, Git, and automated testing.`;

export default function App() {
  const [inputType, setInputType] = useState<'text' | 'upload'>('text');
  const [resumeText, setResumeText] = useState(SAMPLE_RESUME);
  const [jobDesc, setJobDesc] = useState(SAMPLE_JOB);
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'add' | 'remove' | 'skillup' | 'rewrites'>('overview');

  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<{ step: number; title: string; subtitle: string }>({
    step: 1,
    title: 'Analyzing Resume Profile...',
    subtitle: 'Extracting competencies and matching against target specifications...'
  });

  const [auditData, setAuditData] = useState<AuditData | null>(null);
  const [hybridMetrics, setHybridMetrics] = useState<HybridMetrics | null>(null);
  const [modelUsed, setModelUsed] = useState<string>('openai/gpt-4o-mini');
  const [modelCount, setModelCount] = useState<number>(460);

  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const resultsRef = useRef<HTMLDivElement>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch('/api/models')
      .then(res => res.json())
      .then(data => {
        if (data.count) setModelCount(data.count);
      })
      .catch(() => setModelCount(460));
  }, []);

  const triggerConfetti = () => {
    try {
      confetti({
        particleCount: 80,
        spread: 65,
        origin: { y: 0.6 }
      });
    } catch {}
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        setPdfFile(file);
      } else {
        alert('Please upload a valid PDF document.');
      }
    }
  };

  const runAudit = async () => {
    setErrorMsg(null);
    if (inputType === 'upload' && !pdfFile && !resumeText.trim()) {
      setErrorMsg('Please select a PDF file or paste your resume text.');
      return;
    }
    if (inputType === 'text' && !resumeText.trim()) {
      setErrorMsg('Please paste your resume text to begin.');
      return;
    }
    if (!jobDesc.trim()) {
      setErrorMsg('Please paste the target job description.');
      return;
    }

    setLoading(true);
    setLoadingStage({
      step: 1,
      title: 'Analyzing Resume Profile...',
      subtitle: 'Extracting competencies and evaluating qualification alignment...'
    });

    try {
      let res;
      if (inputType === 'upload' && pdfFile) {
        const formData = new FormData();
        formData.append('resume_file', pdfFile);
        formData.append('job_desc', jobDesc);

        setTimeout(() => {
          setLoadingStage({
            step: 2,
            title: 'Synthesizing Strategic Analysis...',
            subtitle: 'Evaluating role requirements, skill gaps, and career roadmap...'
          });
        }, 1000);

        res = await fetch('/api/audit/upload', {
          method: 'POST',
          body: formData,
        });
      } else {
        setTimeout(() => {
          setLoadingStage({
            step: 2,
            title: 'Synthesizing Strategic Analysis...',
            subtitle: 'Evaluating role requirements, skill gaps, and career roadmap...'
          });
        }, 700);

        res = await fetch('/api/audit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ resume_text: resumeText, job_desc: jobDesc }),
        });
      }

      const resText = await res.text();
      let result: any;
      try {
        result = resText ? JSON.parse(resText) : {};
      } catch {
        throw new Error(`Server returned status ${res.status}: ${resText.slice(0, 100) || 'Empty body'}`);
      }

      if (!res.ok) {
        throw new Error(result.detail || result.message || `Audit failed with status ${res.status}`);
      }

      setLoadingStage({
        step: 3,
        title: 'Analysis Complete!',
        subtitle: `Match score calculated at ${result.data.match_score}%. Preparing dashboard...`
      });

      setTimeout(() => {
        setAuditData(result.data);
        setHybridMetrics(result.metrics);
        setModelUsed(result.model_used || 'openai/gpt-4o-mini');
        setLoading(false);

        setMessages([
          {
            role: 'assistant',
            content: `Your resume analysis is complete with an ATS match score of ${result.data.match_score}%. Review your key strengths, suggested additions, and personalized upskilling roadmap below. What would you like to explore first?`
          }
        ]);

        if (result.data.match_score >= 70) {
          triggerConfetti();
        }

        setTimeout(() => {
          resultsRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 200);
      }, 500);

    } catch (err: any) {
      setLoading(false);
      setErrorMsg(err.message || 'Error occurred during audit processing.');
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || chatInput;
    if (!text.trim() || chatLoading) return;

    const newMessages: ChatMsg[] = [...messages, { role: 'user', content: text }];
    setMessages(newMessages);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            {
              role: 'system',
              content: `You are TalentBridge AI Career Coach. Deterministic score: ${auditData?.match_score}%. ATS Status: ${auditData?.ats_status}. Answer directly and concisely in clean text without markdown asterisks or raw HTML tags.`
            },
            ...newMessages
          ]
        })
      });

      const resText = await res.text();
      let data: any;
      try {
        data = resText ? JSON.parse(resText) : {};
      } catch {
        throw new Error(`Coach returned status ${res.status}`);
      }

      if (!res.ok) {
        throw new Error(data.detail || 'Coach response error.');
      }

      setMessages([...newMessages, { role: 'assistant', content: data.reply, model_used: data.model_used }]);
      setTimeout(() => {
        chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    } catch (err: any) {
      setMessages([...newMessages, { role: 'assistant', content: 'Connection notice: Coach temporarily unavailable. Please retry.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const downloadReport = () => {
    if (!auditData || !hybridMetrics) return;
    let txt = `TALENTBRIDGE RESUME AUDIT & ROADMAP REPORT\n=============================================================\n`;
    txt += `ATS MATCH SCORE: ${auditData.match_score}%\n`;
    txt += `QUALIFICATION STANDING: ${auditData.ats_status}\n`;
    txt += `CORE TECH OVERLAP: ${hybridMetrics.matched_skills.length} of ${hybridMetrics.total_required} Core Technologies\n\n`;
    txt += `1. EXECUTIVE OVERVIEW\n-------------------------------------------------------------\n${auditData.executive_overview}\n\n`;
    txt += `Verified Candidate Strengths:\n`;
    auditData.verified_strengths.forEach(s => { txt += `- ${s}\n`; });
    txt += `\n2. WHAT TO ADD TO YOUR RESUME\n-------------------------------------------------------------\n`;
    auditData.what_to_add.forEach(a => { txt += `+ ${a}\n`; });
    txt += `\n3. WHAT TO REMOVE FROM YOUR RESUME\n-------------------------------------------------------------\n`;
    auditData.what_to_remove.forEach(r => { txt += `- ${r}\n`; });
    txt += `\n4. UPSKILLING MILESTONES\n-------------------------------------------------------------\n`;
    auditData.what_to_skill_up.forEach((step, i) => {
      txt += `[Milestone ${i+1}] ${step.skill} (${step.priority})\n`;
      txt += `  Why Needed: ${step.why_needed}\n`;
      txt += `  Action Plan: ${step.action_plan}\n`;
      txt += `  Resources: ${step.recommended_resources}\n\n`;
    });
    txt += `5. RESUME BULLET REWRITES\n-------------------------------------------------------------\n`;
    auditData.resume_rewrites.forEach(rw => {
      txt += `Before: ${rw.original}\n`;
      txt += `After:  ${rw.optimized}\n`;
      txt += `Reason: ${rw.why_this_works}\n\n`;
    });

    const blob = new Blob([txt], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'TalentBridge_Audit_Report.txt';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen text-[#1E2235] flex flex-col justify-between relative selection:bg-[#6C4BE8]/15 selection:text-[#6C4BE8]">
      
      {/* AMBIENT AURORA LIGHT BLOBS (FOR ULTRA-TRANSPARENT FROSTED GLASS EFFECT) */}
      <div className="ambient-blob-1" aria-hidden="true"></div>
      <div className="ambient-blob-2" aria-hidden="true"></div>
      <div className="ambient-blob-3" aria-hidden="true"></div>

      {/* 1. TOP NAVBAR (HIGHLY RESPONSIVE & GLOSSY) */}
      <header className="max-w-7xl mx-auto w-full px-4 sm:px-6 pt-5 sm:pt-7 pb-2 relative z-10">
        <nav className="glossy-card px-5 sm:px-7 py-3.5 sm:py-4 flex flex-col sm:flex-row items-center justify-between gap-3.5 sm:gap-4">
          
          {/* Brand Logo & Title */}
          <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-start">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-2xl bg-gradient-to-br from-[#6C4BE8] via-[#7B56F7] to-[#926EFF] flex items-center justify-center text-white font-black text-xl shadow-purple-btn transition-transform hover:scale-105 duration-300">
                ✦
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-lg sm:text-xl tracking-tight text-[#1E2235]">TalentBridge</span>
                  <span className="px-2.5 py-0.5 rounded-full bg-[#6C4BE8]/10 border border-[#6C4BE8]/20 text-[#6C4BE8] text-[10px] sm:text-[11px] font-extrabold uppercase tracking-wider">
                    Studio
                  </span>
                </div>
                <p className="text-[11px] sm:text-xs text-[#7E8B9B]">Intelligent Career Studio &amp; Roadmap</p>
              </div>
            </div>

            {/* Mobile Reset Shortcut */}
            <button
              onClick={() => {
                setResumeText(SAMPLE_RESUME);
                setJobDesc(SAMPLE_JOB);
                setPdfFile(null);
                setAuditData(null);
                setMessages([]);
              }}
              className="p-2 sm:hidden rounded-full bg-white/70 hover:bg-white text-[#6C4BE8] transition cursor-pointer border border-[#E2E7F4]"
              title="Reset Sample Data"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Right Status Pill & Desktop Reset */}
          <div className="flex items-center gap-2.5 sm:gap-3 w-full sm:w-auto justify-between sm:justify-end">
            <div className="flex items-center gap-2 px-3.5 sm:px-4 py-1.5 sm:py-2 rounded-full glossy-pill text-[11px] sm:text-xs w-full sm:w-auto justify-center">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="font-semibold text-[#1E2235]">ATS Engine Active</span>
            </div>

            <button
              onClick={() => {
                setResumeText(SAMPLE_RESUME);
                setJobDesc(SAMPLE_JOB);
                setPdfFile(null);
                setAuditData(null);
                setMessages([]);
              }}
              className="hidden sm:flex p-2.5 rounded-full bg-white/70 hover:bg-white text-[#6C4BE8] transition-all hover:rotate-180 duration-500 cursor-pointer border border-[#E2E7F4] shadow-sm"
              title="Reset Sample Data"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </nav>
      </header>

      {/* 2. MAIN CONTENT AREA */}
      <main className="max-w-7xl mx-auto w-full px-4 sm:px-6 py-4 sm:py-6 flex-grow relative z-10">
        
        {/* HERO TITLE */}
        <div className="mb-6 sm:mb-8 text-center sm:text-left">
          <h1 className="text-2xl sm:text-4xl lg:text-[42px] font-extrabold text-[#1E2235] tracking-tight leading-tight">
            Resume Matcher &amp; Career Roadmap
          </h1>
          <p className="text-xs sm:text-base text-[#6B7280] mt-1.5 max-w-2xl">
            Evaluate your resume against target roles, identify critical skill gaps, and build your personalized career roadmap.
          </p>
        </div>

        {/* ERROR BANNER */}
        {errorMsg && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-50/90 backdrop-blur-md border border-rose-200 text-rose-700 text-xs sm:text-sm flex items-center gap-3 animate-fadeInUp">
            <XCircle className="w-5 h-5 flex-shrink-0 text-rose-500" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* 3. DUAL INPUT WORKSPACE (GLOSSY TRANSLUCENT CARDS) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 sm:gap-6">
          
          {/* LEFT: CANDIDATE RESUME */}
          <div className="glossy-card p-5 sm:p-7 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-[#F0EDFD] flex items-center justify-center text-[#6C4BE8]">
                    <FileText className="w-4 h-4" />
                  </div>
                  <h2 className="font-extrabold text-[#1E2235] text-base sm:text-lg">Candidate Resume</h2>
                </div>
                
                {/* Mode Pill Toggle */}
                <div className="flex p-1 rounded-full bg-[#EBF0F9]/80 backdrop-blur-md border border-[#E0E5F2] text-xs font-semibold">
                  <button
                    onClick={() => setInputType('text')}
                    className={`px-3.5 sm:px-4 py-1.5 rounded-full transition-all duration-300 cursor-pointer ${
                      inputType === 'text' 
                        ? 'bg-[#6C4BE8] text-white shadow-purple-btn' 
                        : 'text-[#6B7280] hover:text-[#1E2235]'
                    }`}
                  >
                    Paste Text
                  </button>
                  <button
                    onClick={() => setInputType('upload')}
                    className={`px-3.5 sm:px-4 py-1.5 rounded-full transition-all duration-300 cursor-pointer ${
                      inputType === 'upload' 
                        ? 'bg-[#6C4BE8] text-white shadow-purple-btn' 
                        : 'text-[#6B7280] hover:text-[#1E2235]'
                    }`}
                  >
                    Upload PDF
                  </button>
                </div>
              </div>

              {inputType === 'upload' ? (
                <div className="mt-3">
                  <label className="border-2 border-dashed border-[#DDD7FA] hover:border-[#6C4BE8] rounded-3xl p-6 sm:p-8 flex flex-col items-center justify-center text-center cursor-pointer bg-white/40 hover:bg-white/70 backdrop-blur-md transition-all duration-300 group">
                    <div className="w-12 h-12 rounded-full bg-[#ECE8FE] flex items-center justify-center mb-3 text-[#6C4BE8] group-hover:scale-110 transition-transform">
                      <Upload className="w-6 h-6" />
                    </div>
                    <span className="text-sm font-bold text-[#1E2235]">Upload your resume in PDF</span>
                    <span className="text-xs text-[#7E8B9B] mt-1">Directly extracted via secure PDF parser</span>
                    <input 
                      type="file" 
                      accept=".pdf" 
                      onChange={handleFileUpload} 
                      className="hidden" 
                    />
                  </label>

                  {pdfFile && (
                    <div className="mt-3.5 p-3 rounded-2xl glossy-pill flex items-center justify-between animate-fadeInUp">
                      <div className="flex items-center gap-2.5 overflow-hidden">
                        <FileCheck className="w-5 h-5 text-[#6C4BE8] flex-shrink-0" />
                        <span className="text-xs sm:text-sm font-semibold text-[#1E2235] truncate">{pdfFile.name}</span>
                        <span className="text-[11px] text-[#7E8B9B]">({Math.round(pdfFile.size / 1024)} KB)</span>
                      </div>
                      <button 
                        onClick={() => setPdfFile(null)}
                        className="text-xs text-rose-500 hover:text-rose-600 font-bold px-2 py-1 cursor-pointer"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="mt-3">
                  <textarea
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                    rows={8}
                    placeholder="Paste education, work history, programming languages, and projects..."
                    className="w-full rounded-2xl glossy-input p-4 text-xs font-mono text-[#1E2235] leading-relaxed resize-none outline-none"
                  />
                  <div className="flex justify-between items-center text-[11px] text-[#7E8B9B] mt-1.5 px-1">
                    <span>Includes competencies &amp; achievements</span>
                    <span>{resumeText.split(/\s+/).filter(Boolean).length} words</span>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-4 pt-3.5 border-t border-[#EEF2FA] flex items-center justify-between text-xs text-[#7E8B9B]">
              <span className="flex items-center gap-1.5 font-medium text-[#6C4BE8]">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Full Competency Scan
              </span>
              <span>ATS Compliant Format</span>
            </div>
          </div>

          {/* RIGHT: TARGET JOB DESCRIPTION */}
          <div className="glossy-card p-5 sm:p-7 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-[#F0EDFD] flex items-center justify-center text-[#6C4BE8]">
                    <Briefcase className="w-4 h-4" />
                  </div>
                  <h2 className="font-extrabold text-[#1E2235] text-base sm:text-lg">Target Job Description</h2>
                </div>
                <button
                  onClick={() => setJobDesc(SAMPLE_JOB)}
                  className="px-3.5 py-1.5 rounded-full bg-white/70 hover:bg-[#F0EDFD] text-[#6C4BE8] text-xs font-bold transition-all hover:scale-105 duration-200 cursor-pointer border border-[#E2D9FC]"
                >
                  Load Sample
                </button>
              </div>

              <div className="mt-3">
                <textarea
                  value={jobDesc}
                  onChange={(e) => setJobDesc(e.target.value)}
                  rows={8}
                  placeholder="Paste role responsibilities, required programming languages, tools, and qualifications..."
                  className="w-full rounded-2xl glossy-input p-4 text-xs font-mono text-[#1E2235] leading-relaxed resize-none outline-none"
                />
                <div className="flex justify-between items-center text-[11px] text-[#7E8B9B] mt-1.5 px-1">
                  <span>Evaluates required skills, cloud stack &amp; degree fit</span>
                  <span>{jobDesc.split(/\s+/).filter(Boolean).length} words</span>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3.5 border-t border-[#EEF2FA] flex items-center justify-between text-xs text-[#7E8B9B]">
              <span className="flex items-center gap-1.5 font-medium text-[#6C4BE8]">
                <Target className="w-4 h-4 text-[#6C4BE8]" /> Role Requirement Analysis
              </span>
              <span>Precision Keyword Match</span>
            </div>
          </div>
        </div>

        {/* 4. PRIMARY ACTION BUTTON */}
        <div className="mt-6 sm:mt-7">
          <button
            onClick={runAudit}
            disabled={loading}
            className={`w-full py-4 px-8 glossy-btn text-base sm:text-lg font-extrabold flex items-center justify-center gap-3 cursor-pointer ${
              loading ? 'opacity-80 cursor-wait' : ''
            }`}
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Analyzing Competencies &amp; Generating Roadmap...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>✦ Run Complete Resume Audit &amp; Roadmap Analysis</span>
              </>
            )}
          </button>
        </div>

        {/* 5. GENERATING EFFECT (HIGH-TECH GLOSSY LOADER) */}
        {loading && (
          <div className="mt-6 p-6 sm:p-7 glossy-card-elevated border border-[#DDD5FE] shadow-purple-glow animate-fadeInUp">
            <div className="flex items-center gap-4 mb-4">
              <div className="relative">
                <div className="w-10 h-10 rounded-full border-3 border-[#ECE8FE] border-t-[#6C4BE8] animate-spin flex-shrink-0"></div>
                <div className="absolute inset-0 w-10 h-10 rounded-full border-2 border-transparent border-b-[#A78BFA] animate-spin-slow"></div>
              </div>
              <div>
                <h3 className="font-extrabold text-base sm:text-lg text-[#1E2235]">{loadingStage.title}</h3>
                <p className="text-xs sm:text-sm text-[#6B7280] mt-0.5">{loadingStage.subtitle}</p>
              </div>
            </div>

            {/* Shimmer Bar */}
            <div className="w-full h-2 bg-[#F0EDFD] rounded-full overflow-hidden relative mb-4">
              <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-[#6C4BE8] to-transparent animate-shimmer"></div>
            </div>

            {/* Step badges */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <div className={`px-4 py-2.5 rounded-2xl text-xs font-bold flex items-center gap-2 transition-all duration-300 ${
                loadingStage.step >= 1 ? 'glossy-pill text-[#6C4BE8] border border-[#E2D9FC]' : 'bg-white/40 text-[#9CA3AF]'
              }`}>
                {loadingStage.step > 1 ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : <Layers className="w-4 h-4 animate-spin-slow" />}
                <span>1. Extracting Skills</span>
              </div>
              <div className={`px-4 py-2.5 rounded-2xl text-xs font-bold flex items-center gap-2 transition-all duration-300 ${
                loadingStage.step >= 2 ? 'glossy-pill text-[#6C4BE8] border border-[#E2D9FC]' : 'bg-white/40 text-[#9CA3AF]'
              }`}>
                {loadingStage.step > 2 ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : <Bot className="w-4 h-4" />}
                <span>2. Matching Requirements</span>
              </div>
              <div className={`px-4 py-2.5 rounded-2xl text-xs font-bold flex items-center gap-2 transition-all duration-300 ${
                loadingStage.step >= 3 ? 'bg-[#EBFBF3] text-emerald-700 border border-emerald-200' : 'bg-white/40 text-[#9CA3AF]'
              }`}>
                {loadingStage.step >= 3 ? <CheckCircle2 className="w-4 h-4 text-emerald-500" /> : <Target className="w-4 h-4" />}
                <span>3. Generating Roadmap</span>
              </div>
            </div>
          </div>
        )}

        {/* 6. COMPREHENSIVE AUDIT DASHBOARD */}
        {auditData && hybridMetrics && (
          <div ref={resultsRef} className="mt-10 sm:mt-12 space-y-7 sm:space-y-8 animate-fadeInUp">
            
            {/* GRAPHIC UPDATE TRAJECTORY CARD (GENUINE DOMAIN COMPETENCY CURVE) */}
            <div className="glossy-card-elevated p-6 sm:p-8 relative overflow-hidden">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-4 mb-4">
                <div>
                  <span className="text-[11px] sm:text-xs font-bold uppercase tracking-wider text-[#7E8B9B]">Accurate Competency Analysis</span>
                  <h2 className="text-xl sm:text-2xl font-black text-[#1E2235] tracking-tight mt-0.5">Role Domain Competency Breakdown</h2>
                </div>
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full glossy-pill text-[#6C4BE8] text-xs font-bold">
                  <Award className="w-4 h-4 text-[#6C4BE8]" />
                  <span>Verified Assessment &bull; {auditData.match_score}% Match</span>
                </div>
              </div>

              {/* REAL DOMAIN SVG CURVE PLOT */}
              {(() => {
                const domains = auditData.domain_scores && auditData.domain_scores.length === 6
                  ? auditData.domain_scores
                  : [
                      { domain: 'Languages', score: auditData.score_breakdown?.core_skills_score || auditData.match_score, details: '' },
                      { domain: 'Frameworks', score: auditData.score_breakdown?.core_skills_score || auditData.match_score, details: '' },
                      { domain: 'Databases', score: auditData.score_breakdown?.supporting_skills_score || auditData.match_score, details: '' },
                      { domain: 'Cloud & DevOps', score: auditData.score_breakdown?.experience_alignment_score || auditData.match_score, details: '' },
                      { domain: 'Architecture', score: auditData.score_breakdown?.core_skills_score || auditData.match_score, details: '' },
                      { domain: 'Practices', score: auditData.score_breakdown?.supporting_skills_score || auditData.match_score, details: '' }
                    ];

                const points = domains.map((d, i) => {
                  const x = 70 + i * 132;
                  const y = Math.round(160 - (d.score / 100) * 115);
                  return { x, y, ...d };
                });

                let linePath = `M ${points[0].x},${points[0].y}`;
                for (let i = 0; i < points.length - 1; i++) {
                  const p0 = points[i];
                  const p1 = points[i + 1];
                  const cx = (p0.x + p1.x) / 2;
                  linePath += ` C ${cx},${p0.y} ${cx},${p1.y} ${p1.x},${p1.y}`;
                }
                const areaPath = `${linePath} L ${points[points.length - 1].x},190 L ${points[0].x},190 Z`;

                return (
                  <div>
                    <div className="w-full h-44 sm:h-52 relative my-2">
                      <svg className="w-full h-full overflow-visible" viewBox="0 0 800 200" preserveAspectRatio="none">
                        <defs>
                          <linearGradient id="waveGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#6C4BE8" stopOpacity="0.25" />
                            <stop offset="70%" stopColor="#855BF8" stopOpacity="0.08" />
                            <stop offset="100%" stopColor="#6C4BE8" stopOpacity="0.00" />
                          </linearGradient>
                        </defs>

                        {/* Background Grid reference lines */}
                        <line x1="40" y1="45" x2="760" y2="45" stroke="#E2E7F4" strokeDasharray="3 3" strokeWidth="1" />
                        <line x1="40" y1="102" x2="760" y2="102" stroke="#E2E7F4" strokeDasharray="3 3" strokeWidth="1" />
                        <line x1="40" y1="160" x2="760" y2="160" stroke="#E2E7F4" strokeDasharray="3 3" strokeWidth="1" />

                        {/* Shaded Area */}
                        <path d={areaPath} fill="url(#waveGradient)" />

                        {/* Spline Curve */}
                        <path d={linePath} fill="none" stroke="#6C4BE8" strokeWidth="3.5" strokeLinecap="round" />

                        {/* Individual Domain Points & Score Tags */}
                        {points.map((pt, idx) => (
                          <g key={idx}>
                            <circle cx={pt.x} cy={pt.y} r="6" fill="#6C4BE8" stroke="#FFFFFF" strokeWidth="3" className="filter drop-shadow-sm transition-transform hover:scale-125" />
                            <text 
                              x={pt.x} 
                              y={Math.max(22, pt.y - 12)} 
                              textAnchor="middle" 
                              className="text-[12px] font-black fill-[#1E2235] select-none"
                            >
                              {pt.score}%
                            </text>
                          </g>
                        ))}
                      </svg>
                    </div>

                    {/* REAL DOMAIN BREAKDOWN CARDS */}
                    <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 text-center pt-3 border-t border-[#EEF2FA]">
                      {points.map((pt, idx) => (
                        <div key={idx} className="p-2 rounded-xl bg-white/60 backdrop-blur-md border border-[#E9EEF8] shadow-sm">
                          <div className="text-[11px] font-semibold text-[#7E8B9B] truncate" title={pt.domain}>{pt.domain}</div>
                          <div className="text-sm font-black text-[#6C4BE8] mt-0.5">{pt.score}%</div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}

              {/* 4 STAT VALUES */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6 mt-6 border-t border-[#EEF2FA] text-center sm:text-left">
                <div className="p-2 sm:p-0">
                  <div className="text-xs font-bold text-[#7E8B9B]">Overall Match Score</div>
                  <div className="text-2xl sm:text-3xl font-black text-[#6C4BE8] mt-1">{auditData.match_score}%</div>
                </div>
                <div className="p-2 sm:p-0">
                  <div className="text-xs font-bold text-[#7E8B9B]">ATS Standing</div>
                  <div className="text-base sm:text-lg font-extrabold text-[#1E2235] mt-1 truncate">{auditData.ats_status}</div>
                </div>
                <div className="p-2 sm:p-0">
                  <div className="text-xs font-bold text-[#7E8B9B]">Core Requirements Match</div>
                  <div className="text-2xl sm:text-3xl font-black text-[#1E2235] mt-1">
                    {hybridMetrics.matched_skills.length} <span className="text-xs text-[#7E8B9B] font-medium">of {hybridMetrics.total_required}</span>
                  </div>
                </div>
                <div className="p-2 sm:p-0">
                  <div className="text-xs font-bold text-[#7E8B9B]">Profile Standing</div>
                  <div className="flex items-center justify-center sm:justify-start gap-1 text-[#6C4BE8] mt-2">
                    {[1, 2, 3, 4, 5].map(i => (
                      <Star 
                        key={i} 
                        className={`w-3.5 sm:w-4 h-3.5 sm:h-4 ${
                          i <= (auditData.star_rating || Math.round(auditData.match_score / 20))
                            ? 'fill-[#6C4BE8] text-[#6C4BE8]' 
                            : 'text-slate-300'
                        }`} 
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* SEGMENTED PILL TABS (SWIPEABLE ON MOBILE) */}
            <div className="glossy-card p-2 sm:p-2.5">
              <div className="flex gap-2 overflow-x-auto no-scrollbar pb-1 sm:pb-0">
                {[
                  { id: 'overview', label: 'Overview', icon: BookOpen },
                  { id: 'add', label: `What to Add (${auditData.what_to_add.length})`, icon: CheckCircle2 },
                  { id: 'remove', label: `What to Remove (${auditData.what_to_remove.length})`, icon: XCircle },
                  { id: 'skillup', label: `Upskilling Plan (${auditData.what_to_skill_up.length})`, icon: TrendingUp },
                  { id: 'rewrites', label: 'Bullet Rewrites', icon: Zap }
                ].map(tab => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`px-4 sm:px-5 py-2.5 rounded-full font-bold text-xs sm:text-sm whitespace-nowrap transition-all duration-300 flex items-center gap-2 cursor-pointer ${
                        activeTab === tab.id 
                          ? 'bg-[#6C4BE8] text-white shadow-purple-btn scale-[1.02]' 
                          : 'text-[#6B7280] hover:text-[#1E2235] hover:bg-white/60'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* TAB CONTENTS (GLOSSY TRANSLUCENT CONTAINER) */}
            <div className="glossy-card p-6 sm:p-8">
              
              {/* TAB 1: EXECUTIVE OVERVIEW */}
              {activeTab === 'overview' && (
                <div className="space-y-6 animate-fadeInUp">
                  
                  {/* RECRUITER FIT ASSESSMENT */}
                  <div>
                    <h3 className="text-base sm:text-lg font-extrabold text-[#1E2235] mb-2 flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-[#6C4BE8]" />
                      Recruiter Fit Assessment
                    </h3>
                    <p className="text-[#333A4D] text-xs sm:text-sm md:text-base leading-relaxed bg-white/70 backdrop-blur-md p-4 sm:p-5 rounded-2xl border border-[#E9EEF8] shadow-sm">
                      {auditData.executive_overview}
                    </p>
                  </div>

                  {/* TRANSPARENT ATS SCORE BREAKDOWN */}
                  {auditData.score_breakdown && (
                    <div className="p-4 sm:p-5 rounded-2xl bg-white/70 backdrop-blur-md border border-[#E9EEF8] shadow-sm space-y-3.5">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
                        <span className="text-xs font-bold uppercase tracking-wider text-[#7E8B9B]">Calibrated ATS Score Breakdown</span>
                        <span className="text-[11px] text-[#6C4BE8] font-semibold">{auditData.score_breakdown.justification}</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                        
                        <div className="p-3 rounded-xl bg-white/60 border border-[#E6EAF5]">
                          <div className="flex justify-between text-xs font-semibold mb-1.5">
                            <span className="text-[#475569]">Core Skills (50%)</span>
                            <span className="font-extrabold text-[#1E2235]">{auditData.score_breakdown.core_skills_score}%</span>
                          </div>
                          <div className="w-full h-1.5 bg-[#EEF2FA] rounded-full overflow-hidden">
                            <div className="h-full bg-[#6C4BE8] rounded-full transition-all duration-500" style={{ width: `${auditData.score_breakdown.core_skills_score}%` }}></div>
                          </div>
                        </div>

                        <div className="p-3 rounded-xl bg-white/60 border border-[#E6EAF5]">
                          <div className="flex justify-between text-xs font-semibold mb-1.5">
                            <span className="text-[#475569]">Experience Scope (30%)</span>
                            <span className="font-extrabold text-[#1E2235]">{auditData.score_breakdown.experience_alignment_score}%</span>
                          </div>
                          <div className="w-full h-1.5 bg-[#EEF2FA] rounded-full overflow-hidden">
                            <div className="h-full bg-[#8C6DF8] rounded-full transition-all duration-500" style={{ width: `${auditData.score_breakdown.experience_alignment_score}%` }}></div>
                          </div>
                        </div>

                        <div className="p-3 rounded-xl bg-white/60 border border-[#E6EAF5]">
                          <div className="flex justify-between text-xs font-semibold mb-1.5">
                            <span className="text-[#475569]">Supporting Fit (20%)</span>
                            <span className="font-extrabold text-[#1E2235]">{auditData.score_breakdown.supporting_skills_score}%</span>
                          </div>
                          <div className="w-full h-1.5 bg-[#EEF2FA] rounded-full overflow-hidden">
                            <div className="h-full bg-emerald-500 rounded-full transition-all duration-500" style={{ width: `${auditData.score_breakdown.supporting_skills_score}%` }}></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-[#7E8B9B] mb-3">Verified Candidate Strengths</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {auditData.verified_strengths.map((s, idx) => (
                        <div key={idx} className="p-3.5 rounded-2xl bg-[#EBFBF3]/90 backdrop-blur-md border border-emerald-200 text-emerald-800 text-xs sm:text-sm font-medium flex items-start gap-2.5 shadow-sm hover:scale-[1.01] transition-transform">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                          <span>{s}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-[#7E8B9B] mb-3">Technology Competency Match</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      
                      {/* Matched */}
                      <div className="p-4 sm:p-5 rounded-2xl bg-white/60 backdrop-blur-md border border-[#E6EAF5] shadow-sm">
                        <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider block mb-2.5">Matched On Resume</span>
                        {hybridMetrics.matched_skills.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {hybridMetrics.matched_skills.map((skill, i) => (
                              <span key={i} className="px-3 py-1 rounded-full bg-[#EBFBF3] border border-emerald-200 text-emerald-700 text-xs font-bold shadow-sm">
                                ✓ {skill}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-[#7E8B9B] italic">No direct required technology overlap detected.</span>
                        )}
                      </div>

                      {/* Missing */}
                      <div className="p-4 sm:p-5 rounded-2xl bg-white/60 backdrop-blur-md border border-[#E6EAF5] shadow-sm">
                        <span className="text-xs font-bold text-rose-500 uppercase tracking-wider block mb-2.5">Missing Required Technologies</span>
                        {hybridMetrics.missing_skills.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {hybridMetrics.missing_skills.map((skill, i) => (
                              <span key={i} className="px-3 py-1 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-xs font-bold shadow-sm">
                                ✕ {skill}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-emerald-600 font-bold">All required technologies satisfied!</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: WHAT TO ADD */}
              {activeTab === 'add' && (
                <div className="space-y-4 animate-fadeInUp">
                  <div className="mb-2">
                    <h3 className="text-base sm:text-lg font-extrabold text-[#1E2235] flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                      What to ADD to Your Resume
                    </h3>
                    <p className="text-xs sm:text-sm text-[#6B7280] mt-1">
                      Adding these specific technical keywords, quantifiable metrics, and links directly improves ATS ranking:
                    </p>
                  </div>
                  <div className="space-y-3">
                    {auditData.what_to_add.map((item, idx) => (
                      <div key={idx} className="p-4 rounded-2xl bg-[#FAF8FF]/90 backdrop-blur-md border border-[#E4DBFD] text-[#2D234D] text-xs sm:text-sm flex items-start gap-3 shadow-sm hover:scale-[1.008] transition-transform">
                        <span className="w-5 h-5 rounded-full bg-[#6C4BE8] text-white flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 shadow-sm">
                          +
                        </span>
                        <span className="leading-relaxed font-medium">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 3: WHAT TO REMOVE */}
              {activeTab === 'remove' && (
                <div className="space-y-4 animate-fadeInUp">
                  <div className="mb-2">
                    <h3 className="text-base sm:text-lg font-extrabold text-[#1E2235] flex items-center gap-2">
                      <XCircle className="w-5 h-5 text-rose-500" />
                      What to REMOVE or REPHRASE
                    </h3>
                    <p className="text-xs sm:text-sm text-[#6B7280] mt-1">
                      Pruning subjective buzzwords, outdated entries, and passive language keeps your resume engineering-focused:
                    </p>
                  </div>
                  <div className="space-y-3">
                    {auditData.what_to_remove.map((item, idx) => (
                      <div key={idx} className="p-4 rounded-2xl bg-rose-50/70 backdrop-blur-md border border-rose-200 text-rose-900 text-xs sm:text-sm flex items-start gap-3 shadow-sm hover:scale-[1.008] transition-transform">
                        <span className="w-5 h-5 rounded-full bg-rose-500 text-white flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 shadow-sm">
                          -
                        </span>
                        <span className="leading-relaxed font-medium">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 4: UPSKILLING PLAN */}
              {activeTab === 'skillup' && (
                <div className="space-y-6 animate-fadeInUp">
                  <div className="mb-2">
                    <h3 className="text-base sm:text-lg font-extrabold text-[#1E2235] flex items-center gap-2">
                      <TrendingUp className="w-5 h-5 text-[#6C4BE8]" />
                      Targeted Upskilling Plan
                    </h3>
                    <p className="text-xs sm:text-sm text-[#6B7280] mt-1">
                      Step-by-step roadmap to bridge every detected requirement gap with proof-of-work portfolio projects:
                    </p>
                  </div>

                  <div className="space-y-4">
                    {auditData.what_to_skill_up.length > 0 ? (
                      auditData.what_to_skill_up.map((step, idx) => (
                        <div key={idx} className="p-5 sm:p-6 rounded-2xl bg-white/70 backdrop-blur-md border border-[#E6EAF5] hover:border-[#6C4BE8]/40 shadow-sm hover:shadow-md transition-all space-y-3.5">
                          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#F0F3FA] pb-3">
                            <div className="flex items-center gap-3">
                              <span className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#6C4BE8] to-[#8C6DF8] text-white font-extrabold text-xs flex items-center justify-center shadow-purple-btn">
                                0{idx + 1}
                              </span>
                              <span className="font-extrabold text-base sm:text-lg text-[#1E2235]">{step.skill}</span>
                            </div>
                            <span className={`px-3 py-1 rounded-full text-[11px] sm:text-xs font-bold ${
                              step.priority.toLowerCase().includes('high')
                                ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                : 'bg-amber-50 text-amber-700 border border-amber-200'
                            }`}>
                              {step.priority}
                            </span>
                          </div>

                          <div className="text-xs sm:text-sm text-[#475569] space-y-2.5">
                            <div className="flex items-start gap-2">
                              <span className="font-bold text-[#1E2235] min-w-[110px] flex-shrink-0">Why Needed:</span>
                              <span className="text-[#333A4D]">{step.why_needed}</span>
                            </div>

                            <div className="p-3.5 rounded-xl bg-[#FAF8FF] border border-[#E9E2FC] flex items-start gap-2.5">
                              <Zap className="w-4 h-4 text-[#6C4BE8] flex-shrink-0 mt-0.5" />
                              <div>
                                <span className="font-bold text-[#6C4BE8] block text-xs uppercase tracking-wider mb-0.5">Proof-of-Work Project</span>
                                <span className="text-xs sm:text-sm text-[#2D234D] font-medium leading-relaxed">{step.action_plan}</span>
                              </div>
                            </div>

                            <div className="flex items-start gap-2 pt-1 text-xs">
                              <BookOpen className="w-4 h-4 text-[#7E8B9B] flex-shrink-0 mt-0.5" />
                              <div>
                                <strong className="text-[#1E2235]">Recommended Resources: </strong>
                                <span className="text-[#6B7280]">{step.recommended_resources}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="p-8 rounded-2xl bg-[#EBFBF3] border border-emerald-200 text-center space-y-2">
                        <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
                        <h4 className="font-extrabold text-emerald-900 text-base">All Core Competencies Satisfied</h4>
                        <p className="text-xs sm:text-sm text-emerald-700 max-w-md mx-auto">
                          Your resume directly matches all primary technical qualifications requested for this role. Review the bullet rewrites to maximize recruiter impact.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 5: BULLET REWRITES */}
              {activeTab === 'rewrites' && (
                <div className="space-y-6 animate-fadeInUp">
                  <div className="mb-2">
                    <h3 className="text-base sm:text-lg font-extrabold text-[#1E2235] flex items-center gap-2">
                      <Zap className="w-5 h-5 text-amber-500" />
                      Resume Bullet Transformations
                    </h3>
                    <p className="text-xs sm:text-sm text-[#6B7280] mt-1">
                      Convert descriptive tasks into metric-driven engineering bullets tailored for ATS parsing:
                    </p>
                  </div>

                  <div className="space-y-4 sm:space-y-5">
                    {auditData.resume_rewrites.map((rw, idx) => (
                      <div key={idx} className="p-4 sm:p-5 rounded-2xl bg-white/60 backdrop-blur-md border border-[#E6EAF5] shadow-sm space-y-3">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 sm:gap-4">
                          
                          {/* Before */}
                          <div className="p-3.5 sm:p-4 rounded-xl bg-rose-50/70 border border-rose-200">
                            <span className="text-[10px] sm:text-[11px] font-bold text-rose-600 uppercase tracking-wider block mb-1">
                              Current Phrasing (Before)
                            </span>
                            <p className="text-xs sm:text-sm text-slate-700 italic">
                              "{rw.original}"
                            </p>
                          </div>

                          {/* After */}
                          <div className="p-3.5 sm:p-4 rounded-xl bg-[#EBFBF3] border border-emerald-200">
                            <span className="text-[10px] sm:text-[11px] font-bold text-emerald-700 uppercase tracking-wider block mb-1">
                              ATS-Optimized Phrasing (After)
                            </span>
                            <p className="text-xs sm:text-sm text-emerald-950 font-semibold">
                              "{rw.optimized}"
                            </p>
                          </div>
                        </div>

                        <div className="text-xs text-[#6B7280] pl-2 border-l-2 border-[#6C4BE8]">
                          <strong className="text-[#1E2235]">Recruiter Rationale:</strong> {rw.why_this_works}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* DOWNLOAD REPORT BUTTON */}
            <div>
              <button
                onClick={downloadReport}
                className="w-full py-3.5 sm:py-4 px-6 glossy-btn-outline font-bold text-xs sm:text-sm flex items-center justify-center gap-2.5 cursor-pointer"
              >
                <Download className="w-4 h-4 text-[#6C4BE8]" />
                <span>Download Full Audit Report (.txt)</span>
              </button>
            </div>

            {/* 7. INTERACTIVE CAREER COACH CHATBOT */}
            <div className="glossy-card p-6 sm:p-8 space-y-6">
              
              {/* Chat Header */}
              <div className="flex items-center justify-between pb-4 border-b border-[#EEF2FA]">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6C4BE8] to-[#8C6DF8] flex items-center justify-center text-white shadow-purple-btn">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <span className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-emerald-500 border-2 border-white"></span>
                  </div>
                  <div>
                    <h3 className="font-extrabold text-sm sm:text-base text-[#1E2235]">Career Advisor</h3>
                    <p className="text-[11px] sm:text-xs text-[#7E8B9B]">Online &bull; Strategy &amp; Interview Guidance</p>
                  </div>
                </div>
                <div className="text-xs text-[#7E8B9B] hidden sm:block">Live Session</div>
              </div>

              {/* Quick Prompt Pills */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-2.5">
                {[
                  { text: '🎯 5 Technical Interview Qs', prompt: 'Provide 5 technical interview questions targeting my identified missing skills along with model answers in clean text without HTML tags or asterisks.' },
                  { text: '✉️ Draft Custom Cover Letter', prompt: 'Write a professional, persuasive cover letter tailored to this role that highlights my strengths and bridges skill gaps in clean text without HTML tags or asterisks.' },
                  { text: '🛠️ Project Architecture Blueprint', prompt: 'Give me a technical architecture blueprint and folder structure for the recommended proof-of-work project in clean text without HTML tags or asterisks.' }
                ].map((item, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendMessage(item.prompt)}
                    disabled={chatLoading}
                    className="p-3 rounded-2xl bg-white/70 hover:bg-[#F0EDFD] border border-[#E6EAF5] hover:border-[#6C4BE8] text-left text-xs text-[#1E2235] font-semibold transition-all hover:scale-[1.01] duration-200 cursor-pointer flex items-center justify-between shadow-sm"
                  >
                    <span>{item.text}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#6C4BE8]" />
                  </button>
                ))}
              </div>

              {/* Messages Container */}
              <div className="space-y-3.5 max-h-96 overflow-y-auto pr-1 sm:pr-2">
                {messages.map((msg, i) => (
                  <div 
                    key={i} 
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeInUp`}
                  >
                    <div 
                      className={`max-w-[90%] sm:max-w-[75%] p-3.5 sm:p-4 text-xs sm:text-sm leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-r from-[#6C4BE8] via-[#7B56F7] to-[#8C6DF8] text-white rounded-3xl rounded-br-sm shadow-purple-btn font-medium'
                          : 'bg-white/90 backdrop-blur-md border border-[#E6EAF5] text-[#1E2235] rounded-3xl rounded-bl-sm shadow-sm'
                      }`}
                    >
                      <div className="whitespace-pre-line font-sans">
                        {msg.content}
                      </div>
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex justify-start animate-fadeInUp">
                    <div className="p-3.5 rounded-2xl bg-white/80 backdrop-blur-md border border-[#E6EAF5] text-xs text-[#7E8B9B] flex items-center gap-2.5 shadow-sm">
                      <div className="w-3.5 h-3.5 border-2 border-[#6C4BE8] border-t-transparent rounded-full animate-spin"></div>
                      <span>Career Advisor is thinking...</span>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Chat Input Bar */}
              <form 
                onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
                className="flex items-center gap-2 sm:gap-3 pt-2"
              >
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask about your roadmap, interview prep, or resume bullet rewrites..."
                  className="flex-1 rounded-full glossy-input px-4 sm:px-5 py-3 sm:py-3.5 text-xs sm:text-sm text-[#1E2235] placeholder-[#9CA3AF] outline-none"
                />
                <button
                  type="submit"
                  disabled={chatLoading || !chatInput.trim()}
                  className="w-11 h-11 sm:w-12 sm:h-12 rounded-full glossy-btn flex items-center justify-center flex-shrink-0 cursor-pointer disabled:opacity-50"
                  title="Send Message"
                >
                  <Send className="w-4 h-4 ml-0.5" />
                </button>
              </form>
            </div>
          </div>
        )}
      </main>

      {/* 8. FOOTER */}
      <footer className="max-w-7xl mx-auto w-full px-4 sm:px-6 pt-8 pb-8 relative z-10">
        <div className="glossy-card px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#7E8B9B]">
          <div>
            &copy; 2026 <strong className="text-[#1E2235]">TalentBridge AI</strong> &bull; All rights reserved.
          </div>
          <div className="text-[#475569] font-medium text-center">
            Made with <span className="text-[#EC4899]">&hearts;</span> by <span className="text-[#6C4BE8] font-bold">Suyash Singh &amp; Shubhada Shingane</span>
          </div>
          <div>
            AI Agent Development &bull; CSE Department
          </div>
        </div>
      </footer>
    </div>
  );
}
