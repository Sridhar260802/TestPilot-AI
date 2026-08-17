// src/pages/WebsiteTest.jsx
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import { getStoredUser, getToken } from "../services/authService";

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || "http://localhost:8000";

/* Same token system as Dashboard.jsx — ink / paper / flag / pass */
function useReportFonts() {
  useEffect(() => {
    if (document.getElementById("report-fonts")) return;
    const link = document.createElement("link");
    link.id = "report-fonts";
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap";
    document.head.appendChild(link);
  }, []);
}

const PLAN_COPY = {
  basic: {
    label: "Basic",
    headline: "Give your site a quick health check",
    sub: "We'll scan your page for SEO, performance and content issues, then file a clean PDF report you can act on today.",
  },
  standard: {
    label: "Standard",
    headline: "Run a deeper diagnostic on your site",
    sub: "Functional checks, advanced SEO & accessibility, plus AI-written recommendations — packaged into one downloadable report.",
  },
  premium: {
    label: "Premium",
    headline: "Put your site through the full audit",
    sub: "Functional tests, a full security sweep, and a content & UX review — everything you need before you ship changes with confidence.",
  },
};

export default function WebsiteTest() {
  useReportFonts();

  const user = getStoredUser();
  const rawPlan = user?.plan || null;
  // Only treat it as an active plan if it actually matches a known tier —
  // guards against "", "null" (string), or any unexpected value crashing the page.
  const plan = rawPlan && PLAN_COPY[rawPlan] ? rawPlan : null;
  const copy = plan ? PLAN_COPY[plan] : null;

  const [url, setUrl] = useState("");
  const [status, setStatus] = useState("idle"); // idle | running | done | error
  const [errorMessage, setErrorMessage] = useState("");
  const [reportBlobUrl, setReportBlobUrl] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!url.trim() || !plan) return;

    setStatus("running");
    setErrorMessage("");
    setReportBlobUrl(null);

    try {
      const response = await fetch(`${API_BASE_URL}/plans/${plan}/report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ url: url.trim() }),
      });

      if (!response.ok) {
        let message = "Could not generate the report. Please try again.";
        try {
          const data = await response.json();
          message = data.detail || message;
        } catch {
          /* non-JSON error body */
        }
        throw new Error(message);
      }

      const blob = await response.blob();
      setReportBlobUrl(URL.createObjectURL(blob));
      setStatus("done");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err.message || "Something went wrong running this test.");
    }
  }

  function handleRetry() {
    setStatus("idle");
    setErrorMessage("");
  }

  const [downloadPhase, setDownloadPhase] = useState("idle"); // idle | downloading | done

  function handleDownloadClick() {
    // Purely a visual beat — the actual download happens via the <a href download>.
    if (downloadPhase !== "idle") return;
    setDownloadPhase("downloading");

    setTimeout(() => setDownloadPhase("done"), 1300);
    setTimeout(() => setDownloadPhase("idle"), 3000);
  }

  return (
    <div className="min-h-screen bg-[#F1ECDF] text-[#14181B]">
      <Navbar />

      {!plan ? (
        <NoPlanState />
      ) : (
        <div className="mx-auto max-w-xl px-4 py-14 sm:px-6">
          {/* Plan badge */}
          <div className="flex items-center gap-2 animate-[fadeSlideUp_0.5s_cubic-bezier(0.22,1,0.36,1)_both]">
            <span
              className="inline-flex items-center gap-2 rounded-full border border-[#14181B]/15 bg-white px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#14181B]/60"
              style={{ fontFamily: "'IBM Plex Mono', monospace" }}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-[#1F5C45]" />
              {copy.label} plan
            </span>
          </div>

          {/* Heading */}
          <h1
            className="mt-4 text-3xl font-semibold leading-tight tracking-tight sm:text-[2.2rem] animate-[fadeSlideUp_0.5s_cubic-bezier(0.22,1,0.36,1)_0.06s_both]"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            {copy.headline}
          </h1>
          <p className="mt-3 max-w-md text-sm leading-relaxed text-[#14181B]/60 animate-[fadeSlideUp_0.5s_cubic-bezier(0.22,1,0.36,1)_0.12s_both]">
            {copy.sub}
          </p>

          {/* URL form */}
          <form onSubmit={handleSubmit} className="mt-8 animate-[fadeSlideUp_0.5s_cubic-bezier(0.22,1,0.36,1)_0.18s_both]">
            <label
              htmlFor="site-url"
              className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.2em] text-[#14181B]/45"
              style={{ fontFamily: "'IBM Plex Mono', monospace" }}
            >
              Website URL
            </label>
            <div
              className={`flex items-center gap-2 rounded-sm border bg-white px-4 py-3 transition-all duration-300 ${
                status === "running"
                  ? "border-[#1F5C45]/50 shadow-[0_0_0_3px_rgba(31,92,69,0.12)]"
                  : "border-[#14181B]/15 hover:border-[#14181B]/30 focus-within:border-[#14181B] focus-within:shadow-[0_0_0_3px_rgba(20,24,27,0.06)]"
              }`}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="shrink-0 text-[#14181B]/30">
                <path
                  d="M12 2a10 10 0 100 20 10 10 0 000-20zM2 12h20M12 2c2.5 2.7 4 6.2 4 10s-1.5 7.3-4 10c-2.5-2.7-4-6.2-4-10s1.5-7.3 4-10z"
                  stroke="currentColor"
                  strokeWidth="1.6"
                />
              </svg>
              <input
                id="site-url"
                type="url"
                required
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={status === "running"}
                className="w-full border-0 bg-transparent p-0 text-sm text-[#14181B] outline-none placeholder:text-[#14181B]/35 disabled:opacity-50"
                style={{ fontFamily: "'IBM Plex Mono', monospace" }}
              />
              <button
                type="submit"
                disabled={status === "running"}
                className="group shrink-0 rounded-sm bg-[#14181B] px-5 py-2 text-sm font-semibold text-white transition-all duration-200 hover:bg-[#E4572E] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:bg-[#14181B] active:scale-[0.97]"
              >
                <span className="flex items-center gap-1.5">
                  {status === "running" ? "Running…" : "Run test"}
                  {status !== "running" && (
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" className="transition-transform duration-200 group-hover:translate-x-0.5">
                      <path d="M5 12h14m0 0l-6-6m6 6l-6 6" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </span>
              </button>
            </div>
            <p className="mt-2 text-xs text-[#14181B]/40">
              Takes about a minute. We'll check the page live — no crawling your whole site.
            </p>
          </form>

          <div className="mt-6 grid" style={{ gridTemplateAreas: "stack" }}>
            {status === "idle" && (
              <div style={{ gridArea: "stack" }} className="animate-[fadeIn_0.4s_ease-out_0.24s_both]">
                <IdleHint plan={plan} />
              </div>
            )}

            {status === "running" && (
              <div style={{ gridArea: "stack" }}>
                <RunningState plan={plan} />
              </div>
            )}

            {status === "error" && (
              <div
                role="alert"
                style={{ gridArea: "stack" }}
                className="animate-[shakeIn_0.4s_cubic-bezier(0.22,1,0.36,1)_both] rounded-sm border border-[#E4572E]/35 bg-white px-5 py-4 text-sm"
              >
                <div className="flex items-start gap-3">
                  <span
                    className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-[#E4572E] text-[13px] font-bold text-[#E4572E]"
                    style={{ fontFamily: "'IBM Plex Mono', monospace" }}
                  >
                    !
                  </span>
                  <div className="flex-1">
                    <p className="font-semibold text-[#14181B]">We couldn't finish this test</p>
                    <p className="mt-0.5 text-[#14181B]/60">{errorMessage}</p>
                    <button
                      type="button"
                      onClick={handleRetry}
                      className="mt-3 inline-flex items-center gap-1.5 rounded-sm border border-[#14181B]/20 bg-white px-3.5 py-1.5 text-xs font-semibold text-[#14181B] transition-all duration-200 hover:border-[#E4572E] hover:text-[#E4572E] active:scale-[0.97]"
                    >
                      Try again
                    </button>
                  </div>
                </div>
              </div>
            )}

            {status === "done" && reportBlobUrl && (
              <div
                style={{ gridArea: "stack" }}
                className="relative animate-[cardIn_0.5s_cubic-bezier(0.22,1,0.36,1)_both] overflow-hidden rounded-sm border border-[#14181B]/12 bg-white p-6 text-center"
              >
                {/* perforation edge, echoing the pricing tickets on the dashboard */}
                <div className="pointer-events-none absolute -top-[7px] left-0 right-0 flex justify-between px-2" aria-hidden="true">
                  {Array.from({ length: 12 }).map((_, i) => (
                    <span key={i} className="h-3.5 w-3.5 rounded-full bg-[#F1ECDF]" />
                  ))}
                </div>

                <div
                  className="mx-auto mb-3 mt-2 flex h-14 w-14 items-center justify-center rounded-full border-2 border-[#1F5C45] animate-[stampPop_0.45s_cubic-bezier(0.22,1,0.36,1)_0.1s_both]"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M5 13l4 4L19 7"
                      stroke="#1F5C45"
                      strokeWidth="2.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      style={{ strokeDasharray: 24, strokeDashoffset: 24, animation: "drawCheck 0.4s ease-out 0.32s forwards" }}
                    />
                  </svg>
                </div>

                <p
                  className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#1F5C45] animate-[fadeIn_0.35s_ease-out_0.26s_both]"
                  style={{ fontFamily: "'IBM Plex Mono', monospace" }}
                >
                  Report filed
                </p>
                <h2
                  className="mt-1 text-lg font-semibold text-[#14181B] animate-[fadeIn_0.35s_ease-out_0.3s_both]"
                  style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                >
                  Your report is ready
                </h2>
                <p
                  className="mt-1 truncate text-xs text-[#14181B]/45 animate-[fadeIn_0.35s_ease-out_0.34s_both]"
                  style={{ fontFamily: "'IBM Plex Mono', monospace" }}
                >
                  {url}
                </p>

                <div className="mt-5 inline-block animate-[fadeIn_0.35s_ease-out_0.38s_both]">
                  <a
                    href={reportBlobUrl}
                    download={`Crosbytech_${plan}_report.pdf`}
                    onClick={handleDownloadClick}
                    aria-disabled={downloadPhase !== "idle"}
                    className={`relative inline-flex items-center gap-2 overflow-hidden rounded-sm px-6 py-3 text-sm font-semibold text-white transition-all duration-200 ${
                      downloadPhase === "idle" ? "hover:bg-[#F16A40] active:scale-[0.97]" : ""
                    } ${downloadPhase === "done" ? "bg-[#1F5C45]" : "bg-[#E4572E]"}`}
                  >
                    {downloadPhase === "downloading" && (
                      <span className="absolute inset-y-0 left-0 bg-white/15" style={{ animation: "fillBar 1.2s ease-out forwards" }} />
                    )}

                    <span className="relative flex items-center gap-2">
                      {downloadPhase === "downloading" && (
                        <>
                          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                          Preparing…
                        </>
                      )}
                      {downloadPhase === "done" && (
                        <>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                            <path d="M5 13l4 4L19 7" stroke="white" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          Downloaded
                        </>
                      )}
                      {downloadPhase === "idle" && (
                        <>
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                            <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 21h16" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          Download PDF report
                        </>
                      )}
                    </span>
                  </a>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setStatus("idle");
                    setUrl("");
                    setReportBlobUrl(null);
                  }}
                  className="mt-4 block w-full text-xs font-semibold text-[#14181B]/40 transition-colors duration-200 hover:text-[#14181B]"
                >
                  Test another URL
                </button>
              </div>
            )}
          </div>

          <style>{`
            @keyframes fadeIn {
              from { opacity: 0; transform: translateY(8px); }
              to { opacity: 1; transform: translateY(0); }
            }
            @keyframes fadeSlideUp {
              from { opacity: 0; transform: translateY(12px); }
              to { opacity: 1; transform: translateY(0); }
            }
            @keyframes cardIn {
              from { opacity: 0; transform: translateY(12px) scale(0.98); }
              to { opacity: 1; transform: translateY(0) scale(1); }
            }
            @keyframes stampPop {
              0% { opacity: 0; transform: scale(0.5) rotate(-8deg); }
              70% { opacity: 1; transform: scale(1.06) rotate(0deg); }
              100% { opacity: 1; transform: scale(1) rotate(0deg); }
            }
            @keyframes drawCheck {
              to { stroke-dashoffset: 0; }
            }
            @keyframes fillBar {
              from { width: 0%; }
              to { width: 100%; }
            }
            @keyframes shakeIn {
              0% { opacity: 0; transform: translateX(0); }
              30% { opacity: 1; transform: translateX(-6px); }
              50% { transform: translateX(5px); }
              70% { transform: translateX(-3px); }
              100% { transform: translateX(0); }
            }
            @media (prefers-reduced-motion: reduce) {
              *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
              }
            }
          `}</style>
        </div>
      )}
    </div>
  );
}

function NoPlanState() {
  const navigate = useNavigate();

  return (
    <div className="relative mx-auto max-w-xl overflow-hidden px-4 py-24 text-center sm:px-6">
      {/* soft ambient glow, drifts in behind the content */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-10 h-64 w-64 -translate-x-1/2 rounded-full bg-[#E4572E]/10 blur-3xl animate-[glowPulse_3.5s_ease-in-out_infinite]"
      />

      <div className="relative animate-[popIn_0.55s_cubic-bezier(0.22,1,0.36,1)_both]">
        <span
          className="inline-flex items-center gap-2 rounded-full border border-[#E4572E]/30 bg-white px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#E4572E]"
          style={{ fontFamily: "'IBM Plex Mono', monospace" }}
        >
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#E4572E]/60" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[#E4572E]" />
          </span>
          No active plan
        </span>
      </div>

      {/* lock icon, draws itself in */}
      <div className="relative mx-auto mt-7 flex h-16 w-16 items-center justify-center rounded-full border-2 border-[#14181B]/15 bg-white animate-[popIn_0.55s_cubic-bezier(0.22,1,0.36,1)_0.08s_both]">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect
            x="5" y="11" width="14" height="9" rx="2"
            stroke="#14181B" strokeWidth="1.8"
            style={{ strokeDasharray: 46, strokeDashoffset: 46, animation: "drawCheck 0.5s ease-out 0.35s forwards" }}
          />
          <path
            d="M8 11V7a4 4 0 118 0v4"
            stroke="#14181B" strokeWidth="1.8" strokeLinecap="round"
            style={{ strokeDasharray: 20, strokeDashoffset: 20, animation: "drawCheck 0.4s ease-out 0.55s forwards" }}
          />
        </svg>
      </div>

      <h1
        className="relative mt-6 text-3xl font-semibold leading-tight tracking-tight sm:text-[2.2rem] animate-[fadeSlideUp_0.5s_cubic-bezier(0.22,1,0.36,1)_0.12s_both]"
        style={{ fontFamily: "'Space Grotesk', sans-serif" }}
      >
        You don't have an active plan
      </h1>
      <p className="relative mx-auto mt-3 max-w-md text-sm leading-relaxed text-[#14181B]/60 animate-[fadeSlideUp_0.5s_cubic-bezier(0.22,1,0.36,1)_0.18s_both]">
        Recharge with Basic, Standard, or Premium to run a live test and get your PDF report.
      </p>

      <div className="relative mt-8 animate-[fadeSlideUp_0.5s_cubic-bezier(0.22,1,0.36,1)_0.26s_both]">
        <button
          type="button"
          onClick={() => navigate("/pricing")}
          className="group relative inline-flex items-center gap-2 overflow-hidden rounded-full bg-[#14181B] px-7 py-3.5 text-sm font-semibold text-white transition-all duration-300 hover:shadow-[0_0_0_6px_rgba(228,87,46,0.15)] active:scale-[0.97]"
        >
          <span className="absolute inset-0 -translate-x-full bg-[#E4572E] transition-transform duration-300 group-hover:translate-x-0" />
          <span className="relative flex items-center gap-2">
            Recharge — view pricing
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="transition-transform duration-200 group-hover:translate-x-1">
              <path d="M5 12h14m0 0l-6-6m6 6l-6 6" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
        </button>
      </div>

      {/* tiny plan chips, staggered in, purely decorative hint of what's on offer */}
      <ul className="relative mt-8 flex flex-wrap items-center justify-center gap-2">
        {["Basic", "Standard", "Premium"].map((p, i) => (
          <li
            key={p}
            style={{ animationDelay: `${0.32 + i * 0.06}s` }}
            className="animate-[fadeSlideUp_0.4s_cubic-bezier(0.22,1,0.36,1)_both] rounded-full border border-[#14181B]/12 bg-white px-3.5 py-1.5 text-xs font-medium text-[#14181B]/60 transition-all duration-200 hover:-translate-y-0.5 hover:border-[#14181B]/25 hover:text-[#14181B]"
          >
            {p}
          </li>
        ))}
      </ul>

      <style>{`
        @keyframes popIn {
          0% { opacity: 0; transform: scale(0.85); }
          70% { opacity: 1; transform: scale(1.03); }
          100% { opacity: 1; transform: scale(1); }
        }
        @keyframes fadeSlideUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes drawCheck {
          to { stroke-dashoffset: 0; }
        }
        @keyframes glowPulse {
          0%, 100% { opacity: 0.5; transform: translate(-50%, 0) scale(1); }
          50% { opacity: 0.9; transform: translate(-50%, 0) scale(1.15); }
        }
        @media (prefers-reduced-motion: reduce) {
          *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
        }
      `}</style>
    </div>
  );
}

function IdleHint({ plan }) {
  const items =
    plan === "premium"
      ? ["Functional tests", "Security audit", "SEO & accessibility", "Content, UX & CRO"]
      : plan === "standard"
      ? ["Functional tests", "SEO & accessibility", "AI recommendations"]
      : ["SEO & accessibility", "Performance", "Content & images"];

  return (
    <div className="rounded-sm border border-dashed border-[#14181B]/20 bg-white p-6">
      <p
        className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#14181B]/40"
        style={{ fontFamily: "'IBM Plex Mono', monospace" }}
      >
        What we'll check
      </p>
      <ul className="mt-3 flex flex-wrap gap-2">
        {items.map((item, i) => (
          <li
            key={item}
            className="animate-[fadeSlideUp_0.35s_ease-out_both] rounded-sm border border-[#14181B]/12 px-3 py-1.5 text-xs font-medium text-[#14181B]/70"
            style={{ animationDelay: `${0.05 * i}s` }}
          >
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function RunningState({ plan }) {
  const steps =
    plan === "premium"
      ? ["Running functional tests", "Checking SEO & accessibility", "Full security audit", "Content, UX & CRO audit", "Building your PDF"]
      : plan === "standard"
      ? ["Running functional tests", "Advanced SEO & accessibility", "Generating AI recommendations", "Building your PDF"]
      : ["Checking SEO & accessibility", "Checking performance", "Validating content & images", "Building your PDF"];

  // Simulated progress — real completion time is unknown, so we advance through
  // steps on a timer and simply hold at the last step until the API responds.
  const [activeIndex, setActiveIndex] = useState(0);
  const intervalRef = useRef(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setActiveIndex((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 1900);
    return () => clearInterval(intervalRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const targetPct = Math.round(((activeIndex + 0.5) / steps.length) * 100);
  const displayPct = Math.min(96, targetPct);

  const size = 44;
  const stroke = 3.5;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (displayPct / 100) * circumference;

  return (
    <div className="rounded-sm border border-[#14181B]/12 bg-white p-6 animate-[fadeIn_0.3s_ease-out]">
      <div className="flex items-center gap-4">
        <div className="relative shrink-0" style={{ width: size, height: size }}>
          <svg width={size} height={size} className="-rotate-90">
            <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(20,24,27,0.08)" strokeWidth={stroke} />
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="#E4572E"
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              style={{ transition: "stroke-dashoffset 0.6s ease-out" }}
            />
          </svg>
          <div
            className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-[#14181B]"
            style={{ fontFamily: "'IBM Plex Mono', monospace" }}
          >
            {displayPct}%
          </div>
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold text-[#14181B]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            Analyzing your site…
          </p>
          <p className="text-xs text-[#14181B]/45">This can take a minute — running real checks against your site.</p>
        </div>
      </div>

      <div className="mt-5 h-1 w-full overflow-hidden rounded-full bg-[#14181B]/10">
        <div
          className="h-full rounded-full bg-[#E4572E] transition-[width] duration-700 ease-out"
          style={{ width: `${displayPct}%` }}
        />
      </div>

      <ul className="mt-5 divide-y divide-[#14181B]/8 border-t border-[#14181B]/8 text-xs" style={{ fontFamily: "'IBM Plex Mono', monospace" }}>
        {steps.map((step, i) => {
          const isDone = i < activeIndex;
          const isActive = i === activeIndex;
          return (
            <li
              key={step}
              className={`flex items-center gap-2.5 px-1 py-2.5 transition-colors duration-300 ${
                isActive ? "bg-[#1F5C45]/[0.04]" : ""
              } ${isDone ? "text-[#14181B]/35" : isActive ? "text-[#14181B]" : "text-[#14181B]/30"}`}
            >
              <span className="flex h-5 w-5 shrink-0 items-center justify-center">
                {isDone ? (
                  <span className="flex h-5 w-5 items-center justify-center rounded-full border border-[#1F5C45] text-[#1F5C45]">✓</span>
                ) : isActive ? (
                  <span className="relative flex h-2.5 w-2.5">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#E4572E]/60" />
                    <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[#E4572E]" />
                  </span>
                ) : (
                  <span className="h-1.5 w-1.5 rounded-full bg-[#14181B]/20" />
                )}
              </span>
              <span className={isActive ? "font-semibold" : ""}>{step}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}