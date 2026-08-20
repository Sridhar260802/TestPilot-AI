// src/pages/MobileAppTest.jsx
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import { getStoredUser } from "../services/authService";
import { runMobileTest, downloadMobileReport, detectPlatform } from "../services/mobileTestService";

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
    headline: "Quick Android security check",
    sub: "Upload an .apk and we'll flag the essentials — debuggable builds, backup exposure, and any sensitive permissions requested.",
    platforms: ["android"],
    accept: ".apk",
  },
  standard: {
    label: "Standard",
    headline: "Android & iOS app testing",
    sub: "Upload an .apk or .ipa. We check exported components, transport-security settings, permission usage descriptions and more.",
    platforms: ["android", "ios"],
    accept: ".apk,.ipa",
  },
  premium: {
    label: "Premium",
    headline: "Full mobile security audit",
    sub: "Everything in Standard, plus hardcoded-secret scanning, weak-crypto detection, certificate/provisioning inspection — the deep pass.",
    platforms: ["android", "ios"],
    accept: ".apk,.ipa",
  },
};

const SEVERITY_STYLE = {
  Critical: { bg: "bg-[#B00020]/10", text: "text-[#B00020]", ring: "border-[#B00020]/30" },
  High: { bg: "bg-[#E65100]/10", text: "text-[#E65100]", ring: "border-[#E65100]/30" },
  Medium: { bg: "bg-[#F9A825]/10", text: "text-[#946200]", ring: "border-[#F9A825]/40" },
  Low: { bg: "bg-[#2E7D32]/10", text: "text-[#2E7D32]", ring: "border-[#2E7D32]/30" },
  Info: { bg: "bg-[#1565C0]/10", text: "text-[#1565C0]", ring: "border-[#1565C0]/30" },
};

export default function MobileAppTest() {
  useReportFonts();
  const navigate = useNavigate();

  const user = getStoredUser();
  const rawPlan = user?.plan || null;
  const plan = rawPlan && PLAN_COPY[rawPlan] ? rawPlan : null;
  const copy = plan ? PLAN_COPY[plan] : null;

  const fileInputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | running | done | error
  const [errorMessage, setErrorMessage] = useState("");
  const [result, setResult] = useState(null);
  const [downloadState, setDownloadState] = useState("idle"); // idle | downloading | done | error

  function handleFileChange(e) {
    const chosen = e.target.files?.[0] || null;
    setFile(chosen);
    setErrorMessage("");
  }

  function platformAllowed(fileName) {
    if (!copy) return false;
    const platform = detectPlatform(fileName);
    return platform && copy.platforms.includes(platform);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file || !plan) return;

    if (!platformAllowed(file.name)) {
      const isIpa = file.name.toLowerCase().endsWith(".ipa");
      setStatus("error");
      setErrorMessage(
        isIpa
          ? "iOS (.ipa) testing needs the Standard or Premium plan. Your current plan only covers Android (.apk)."
          : "Please upload a valid .apk (Android) or .ipa (iOS) file."
      );
      return;
    }

    setStatus("running");
    setErrorMessage("");
    setResult(null);

    try {
      const analysis = await runMobileTest(file);
      setResult(analysis);
      setStatus("done");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err.message || "Something went wrong analyzing this file.");
    }
  }

  function handleRetry() {
    setStatus("idle");
    setErrorMessage("");
  }

  function handleReset() {
    setStatus("idle");
    setFile(null);
    setResult(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleDownload() {
    if (!result?.id || downloadState !== "idle") return;
    setDownloadState("downloading");
    try {
      const blob = await downloadMobileReport(result.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Crosby Tech_Mobile_${(plan || "app")}_Report_${result.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setDownloadState("done");
      setTimeout(() => setDownloadState("idle"), 2500);
    } catch (err) {
      setDownloadState("error");
      setTimeout(() => setDownloadState("idle"), 2500);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#F1ECDF] text-[#14181B]">
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-0 overflow-hidden">
        <div className="absolute -left-24 top-24 h-96 w-96 rounded-full bg-[#E4572E]/[0.07] blur-[90px]" />
        <div className="absolute -right-32 top-1/2 h-[28rem] w-[28rem] rounded-full bg-[#1F5C45]/[0.06] blur-[100px]" />
      </div>

      <div className="relative z-10">
        <Navbar />
      </div>

      {!plan ? (
        <div className="relative z-10 mx-auto max-w-xl px-4 py-24 text-center sm:px-6">
          <h1 className="text-3xl font-semibold" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            You don't have an active plan
          </h1>
          <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-[#14181B]/60">
            Subscribe to Basic, Standard, or Premium to run mobile app scans.
          </p>
          <button
            type="button"
            onClick={() => navigate("/pricing")}
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-[#14181B] px-7 py-3.5 text-sm font-semibold text-white transition-all duration-200 hover:bg-[#E4572E] active:scale-[0.97]"
          >
            View pricing
          </button>
        </div>
      ) : (
        <div className="relative z-10 mx-auto max-w-2xl px-4 py-14 sm:px-6">
          <div className="flex items-center gap-2">
            <span
              className="inline-flex items-center gap-2 rounded-full border border-[#14181B]/15 bg-white px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[#14181B]/60"
              style={{ fontFamily: "'IBM Plex Mono', monospace" }}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-[#1F5C45]" />
              {copy.label} plan
            </span>
            <span
              className="rounded-full bg-[#14181B]/[0.05] px-2.5 py-1 text-[10px] font-semibold text-[#14181B]/50"
              style={{ fontFamily: "'IBM Plex Mono', monospace" }}
            >
              {copy.platforms.includes("ios") ? "Android + iOS" : "Android only"}
            </span>
          </div>

          <h1
            className="mt-4 text-3xl font-semibold leading-tight tracking-tight sm:text-[2.2rem]"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            {copy.headline}
          </h1>
          <p className="mt-3 max-w-md text-sm leading-relaxed text-[#14181B]/60">{copy.sub}</p>

          {status !== "done" && (
            <form onSubmit={handleSubmit} className="mt-8">
              <label
                htmlFor="app-file"
                className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.2em] text-[#14181B]/45"
                style={{ fontFamily: "'IBM Plex Mono', monospace" }}
              >
                App file ({copy.accept.replaceAll(",", " / ")})
              </label>

              <div
                className={`flex flex-col gap-3 rounded-sm border bg-white px-4 py-4 transition-all duration-300 sm:flex-row sm:items-center ${
                  status === "running"
                    ? "border-[#1F5C45]/50 shadow-[0_0_0_3px_rgba(31,92,69,0.12)]"
                    : "border-[#14181B]/15 hover:border-[#14181B]/30"
                }`}
              >
                <input
                  ref={fileInputRef}
                  id="app-file"
                  type="file"
                  accept={copy.accept}
                  onChange={handleFileChange}
                  disabled={status === "running"}
                  className="w-full text-sm text-[#14181B]/70 file:mr-3 file:rounded-sm file:border-0 file:bg-[#14181B] file:px-4 file:py-2 file:text-xs file:font-semibold file:text-white file:transition-colors hover:file:bg-[#E4572E] disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={status === "running" || !file}
                  className="shrink-0 rounded-sm bg-[#14181B] px-5 py-2.5 text-sm font-semibold text-white transition-all duration-200 hover:bg-[#E4572E] disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.97]"
                >
                  {status === "running" ? "Scanning…" : "Run scan"}
                </button>
              </div>

              {file && (
                <p className="mt-2 truncate text-xs text-[#14181B]/45" style={{ fontFamily: "'IBM Plex Mono', monospace" }}>
                  {file.name} · {(file.size / (1024 * 1024)).toFixed(1)} MB
                </p>
              )}

              <p className="mt-2 text-xs text-[#14181B]/40">
                We unpack and statically analyze the file — no install, no device or emulator needed.
              </p>
            </form>
          )}

          {status === "running" && (
            <div className="mt-6 flex items-center gap-3 rounded-sm border border-[#1F5C45]/25 bg-white px-5 py-4 text-sm">
              <span className="relative flex h-3 w-3 shrink-0">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#1F5C45]/60" />
                <span className="relative inline-flex h-3 w-3 rounded-full bg-[#1F5C45]" />
              </span>
              <div>
                <p className="font-semibold text-[#14181B]">Unpacking and analyzing your app…</p>
                <p className="mt-0.5 text-xs text-[#14181B]/45">
                  Reading manifest / Info.plist, permissions, security flags{plan === "premium" ? ", secrets & crypto usage" : ""}.
                </p>
              </div>
            </div>
          )}

          {status === "error" && (
            <div role="alert" className="mt-6 rounded-sm border border-[#E4572E]/35 bg-white px-5 py-4 text-sm">
              <div className="flex items-start gap-3">
                <span
                  className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 border-[#E4572E] text-[13px] font-bold text-[#E4572E]"
                  style={{ fontFamily: "'IBM Plex Mono', monospace" }}
                >
                  !
                </span>
                <div className="flex-1">
                  <p className="font-semibold text-[#14181B]">We couldn't finish this scan</p>
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

          {status === "done" && result && (
            <div className="mt-8">
              <ResultCard result={result} downloadState={downloadState} onDownload={handleDownload} />
              <button
                type="button"
                onClick={handleReset}
                className="mt-4 block w-full text-xs font-semibold text-[#14181B]/40 transition-colors duration-200 hover:text-[#14181B]"
              >
                Scan another app
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ScoreRing({ score, severity }) {
  const size = 76;
  const stroke = 6;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.max(0, Math.min(100, score)) / 100) * circumference;
  const style = SEVERITY_STYLE[severity] || SEVERITY_STYLE.Low;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="rgba(20,24,27,0.08)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          className={style.text}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-lg font-bold text-[#14181B]" style={{ fontFamily: "'IBM Plex Mono', monospace" }}>
          {score}
        </span>
        <span className="text-[9px] text-[#14181B]/40">/ 100</span>
      </div>
    </div>
  );
}

function ResultCard({ result, downloadState, onDownload }) {
  const overview = result.overview || {};
  const issues = result.issues || [];
  const permissions = result.permissions?.dangerous || [];
  const exported = result.exported_components;
  const secretScan = result.secret_scan;
  const cryptoScan = result.weak_crypto_scan;
  const style = SEVERITY_STYLE[result.severity] || SEVERITY_STYLE.Low;

  return (
    <div className="overflow-hidden rounded-xl border border-[#14181B]/10 bg-white shadow-[0_1px_0_rgba(20,24,27,0.03)]">
      <div className="flex items-center gap-4 border-b border-[#14181B]/8 bg-[#14181B]/[0.02] px-6 py-5">
        <ScoreRing score={result.security_score ?? 0} severity={result.severity} />
        <div className="flex-1">
          <p
            className="text-xs font-semibold uppercase tracking-[0.2em] text-[#14181B]/40"
            style={{ fontFamily: "'IBM Plex Mono', monospace" }}
          >
            {result.platform === "ios" ? "iOS" : "Android"} · {result.scan_depth} scan
          </p>
          <p className="mt-1 text-lg font-semibold" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            {overview.package || overview.bundle_id || "App scanned"}
          </p>
          <span className={`mt-1 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold ${style.bg} ${style.text} ${style.ring}`}>
            {result.severity} severity
          </span>
        </div>
        {result.id && (
          <button
            type="button"
            onClick={onDownload}
            disabled={downloadState !== "idle"}
            className="shrink-0 rounded-sm bg-[#E4572E] px-4 py-2 text-xs font-semibold text-white transition-all duration-200 hover:bg-[#F16A40] disabled:opacity-60 active:scale-[0.97]"
          >
            {downloadState === "downloading" ? "Preparing…" : downloadState === "done" ? "Downloaded ✓" : "Download PDF"}
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-2 px-6 py-4 text-xs sm:grid-cols-3">
        {Object.entries(overview).slice(0, 6).map(([key, value]) => (
          <div key={key} className="truncate">
            <p className="text-[10px] uppercase tracking-wide text-[#14181B]/35">{key.replaceAll("_", " ")}</p>
            <p className="truncate font-medium text-[#14181B]/80" style={{ fontFamily: "'IBM Plex Mono', monospace" }}>
              {String(value)}
            </p>
          </div>
        ))}
      </div>

      <div className="border-t border-dashed border-[#14181B]/10 px-6 py-5">
        <p
          className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#14181B]/40"
          style={{ fontFamily: "'IBM Plex Mono', monospace" }}
        >
          Findings ({issues.length})
        </p>
        {issues.length === 0 ? (
          <p className="mt-2 text-sm text-[#14181B]/50">No issues flagged at this scan depth.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {issues.map((issue, i) => {
              const s = SEVERITY_STYLE[issue.severity] || SEVERITY_STYLE.Info;
              return (
                <li key={i} className={`rounded-sm border ${s.ring} ${s.bg} px-3.5 py-2.5`}>
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wide ${s.text}`}>{issue.severity}</span>
                    <span className="text-sm font-semibold text-[#14181B]">{issue.title}</span>
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-[#14181B]/60">{issue.detail}</p>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {permissions.length > 0 && (
        <div className="border-t border-dashed border-[#14181B]/10 px-6 py-5">
          <p
            className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#14181B]/40"
            style={{ fontFamily: "'IBM Plex Mono', monospace" }}
          >
            Sensitive permissions ({permissions.length})
          </p>
          <ul className="mt-3 flex flex-wrap gap-2">
            {permissions.map((p) => (
              <li key={p.permission} className="rounded-sm border border-[#14181B]/12 px-3 py-1.5 text-xs font-medium text-[#14181B]/70">
                {p.description}
              </li>
            ))}
          </ul>
        </div>
      )}

      {exported && (
        <div className="border-t border-dashed border-[#14181B]/10 px-6 py-5">
          <p
            className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#14181B]/40"
            style={{ fontFamily: "'IBM Plex Mono', monospace" }}
          >
            Exported components
          </p>
          <ul className="mt-3 space-y-1.5 text-xs">
            {Object.entries(exported).flatMap(([type, items]) =>
              items.map((c) => (
                <li key={`${type}-${c.name}`} className="flex items-center justify-between rounded-sm border border-[#14181B]/10 px-3 py-1.5">
                  <span className="truncate font-medium text-[#14181B]/75">{c.name}</span>
                  <span
                    className={`ml-2 shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                      c.protected_by_permission ? "bg-[#2E7D32]/10 text-[#2E7D32]" : "bg-[#E65100]/10 text-[#E65100]"
                    }`}
                  >
                    {c.protected_by_permission ? "Protected" : "Unprotected"}
                  </span>
                </li>
              ))
            )}
          </ul>
        </div>
      )}

      {(secretScan || cryptoScan) && (
        <div className="border-t border-dashed border-[#14181B]/10 px-6 py-5">
          <p
            className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#14181B]/40"
            style={{ fontFamily: "'IBM Plex Mono', monospace" }}
          >
            Deep security scan (Premium)
          </p>
          {secretScan && Object.keys(secretScan).length > 0 ? (
            <div className="mt-3">
              <p className="text-xs font-semibold text-[#B00020]">Possible hardcoded secrets</p>
              <ul className="mt-1 space-y-1 text-xs text-[#14181B]/60">
                {Object.entries(secretScan).map(([label, hits]) => (
                  <li key={label}>
                    <span className="font-medium text-[#14181B]/80">{label}:</span> {hits.join("; ")}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="mt-2 text-xs text-[#2E7D32]">No hardcoded secret patterns detected.</p>
          )}
          {cryptoScan && Object.keys(cryptoScan).length > 0 ? (
            <div className="mt-3">
              <p className="text-xs font-semibold text-[#946200]">Weak cryptography references</p>
              <ul className="mt-1 space-y-1 text-xs text-[#14181B]/60">
                {Object.entries(cryptoScan).map(([label, hits]) => (
                  <li key={label}>
                    <span className="font-medium text-[#14181B]/80">{label}:</span> {hits.join("; ")}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="mt-2 text-xs text-[#2E7D32]">No weak-crypto references detected.</p>
          )}
        </div>
      )}
    </div>
  );
}