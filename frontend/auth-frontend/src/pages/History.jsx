// src/pages/History.jsx
import { useEffect, useMemo, useState } from "react";
import Navbar from "../components/Navbar";
import { getToken } from "../services/authService";
import { getMobileHistory, downloadMobileReport } from "../services/mobileTestService";

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || "http://localhost:8000";

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

function shortUrl(url) {
  try {
    const u = new URL(url);
    return u.hostname.replace(/^www\./, "") + (u.pathname !== "/" ? u.pathname : "");
  } catch {
    return url;
  }
}

// Mobile history entries describe an app, not a URL — fall back across
// whatever field the backend happens to name it (package/app_name/etc).
function appLabel(entry) {
  return (
    entry.app_name ||
    entry.package ||
    entry.bundle_id ||
    entry.overview?.package ||
    entry.overview?.bundle_id ||
    entry.file_name ||
    "App scan"
  );
}

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Pulls the PDF for one website-history row and saves it to the user's disk.
// Uses fetch + blob (not a plain <a href>) because the endpoint needs
// the Authorization header — a normal link can't attach that.
async function downloadHistoryReport(entryId, plan) {
  const token = getToken();
  if (!token) return { ok: false, message: "Please log in again." };

  const res = await fetch(`${API_BASE_URL}/dashboard/history/${entryId}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    if (res.status === 404) {
      return {
        ok: false,
        message: "No saved report for this scan — it predates report downloads, or wasn't found.",
      };
    }
    return { ok: false, message: "Couldn't download the report right now." };
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `Crosby Tech_${plan ? plan[0].toUpperCase() + plan.slice(1) : "Website"}_Report_${entryId}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);

  return { ok: true };
}

// Same idea, but for a past mobile (.apk/.ipa) scan — reuses the
// mobileTestService helper that already hits /mobile/history/{id}/download.
async function downloadMobileHistoryReport(entryId, plan) {
  try {
    const blob = await downloadMobileReport(entryId);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Crosby Tech_Mobile_${plan ? plan[0].toUpperCase() + plan.slice(1) : "App"}_Report_${entryId}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    return { ok: true };
  } catch (err) {
    return { ok: false, message: err.message || "Couldn't download the report right now." };
  }
}

const TABS = [
  { key: "website", label: "Website" },
  { key: "mobile", label: "Mobile App" },
];

export default function History() {
  useReportFonts();

  const [tab, setTab] = useState("website");

  // Each tab keeps its own entries/loading/error/loaded-once state so
  // switching back and forth doesn't re-fetch every time.
  const [siteState, setSiteState] = useState({ entries: [], loading: true, errored: false, loaded: false });
  const [mobileState, setMobileState] = useState({ entries: [], loading: true, errored: false, loaded: false });

  const [query, setQuery] = useState("");
  const [planFilter, setPlanFilter] = useState("all");

  // Website history
  useEffect(() => {
    if (tab !== "website" || siteState.loaded) return;
    let cancelled = false;

    async function loadHistory() {
      try {
        const token = getToken();
        if (!token) {
          if (!cancelled) setSiteState({ entries: [], loading: false, errored: false, loaded: true });
          return;
        }
        const res = await fetch(`${API_BASE_URL}/dashboard/history?limit=200`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("history request failed");
        const data = await res.json();
        if (!cancelled) {
          setSiteState({ entries: Array.isArray(data) ? data : [], loading: false, errored: false, loaded: true });
        }
      } catch {
        if (!cancelled) setSiteState({ entries: [], loading: false, errored: true, loaded: true });
      }
    }

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [tab, siteState.loaded]);

  // Mobile app history
  useEffect(() => {
    if (tab !== "mobile" || mobileState.loaded) return;
    let cancelled = false;

    async function loadHistory() {
      try {
        const token = getToken();
        if (!token) {
          if (!cancelled) setMobileState({ entries: [], loading: false, errored: false, loaded: true });
          return;
        }
        const data = await getMobileHistory(200);
        if (!cancelled) {
          setMobileState({ entries: Array.isArray(data) ? data : [], loading: false, errored: false, loaded: true });
        }
      } catch {
        if (!cancelled) setMobileState({ entries: [], loading: false, errored: true, loaded: true });
      }
    }

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [tab, mobileState.loaded]);

  const activeState = tab === "website" ? siteState : mobileState;
  const entries = activeState.entries;

  // Reset the search/filter controls whenever the tab changes so a
  // website-only filter doesn't silently hide every mobile row.
  function handleTabChange(nextTab) {
    if (nextTab === tab) return;
    setTab(nextTab);
    setQuery("");
    setPlanFilter("all");
  }

  const plans = useMemo(() => {
    const set = new Set(entries.map((e) => e.plan).filter(Boolean));
    return ["all", ...Array.from(set)];
  }, [entries]);

  const filtered = useMemo(() => {
    return entries.filter((e) => {
      const label = tab === "website" ? e.url || "" : appLabel(e);
      const matchesQuery = query.trim() === "" || label.toLowerCase().includes(query.trim().toLowerCase());
      const matchesPlan = planFilter === "all" || e.plan === planFilter;
      return matchesQuery && matchesPlan;
    });
  }, [entries, query, planFilter, tab]);

  return (
    <div className="min-h-screen bg-[#F1ECDF] text-[#14181B]">
      <div className="pointer-events-none fixed inset-0 -z-0" aria-hidden="true">
        <div
          className="absolute inset-0 opacity-[0.05]"
          style={{
            backgroundImage:
              "linear-gradient(#14181B 1px, transparent 1px), linear-gradient(90deg, #14181B 1px, transparent 1px)",
            backgroundSize: "36px 36px",
          }}
        />
      </div>

      <Navbar />

      <div className="relative mx-auto max-w-4xl px-4 py-12 sm:px-6">
        <p
          className="text-[11px] font-semibold uppercase tracking-[0.25em] text-[#E4572E]"
          style={{ fontFamily: "'IBM Plex Mono', monospace" }}
        >
          Case file
        </p>
        <h1
          className="mt-1.5 text-3xl font-semibold tracking-tight sm:text-4xl"
          style={{ fontFamily: "'Space Grotesk', sans-serif" }}
        >
          Test history
        </h1>
        <p className="mt-2 text-sm text-[#14181B]/55">
          Every scan you've run through Crosbytech, most recent first.
        </p>

        {/* Website / Mobile App tabs */}
        <div className="mt-6 flex gap-2 border-b border-[#14181B]/12">
          {TABS.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => handleTabChange(t.key)}
              className={`-mb-px border-b-2 px-4 py-2.5 text-sm font-semibold transition-colors duration-200 ${
                tab === t.key
                  ? "border-[#14181B] text-[#14181B]"
                  : "border-transparent text-[#14181B]/45 hover:text-[#14181B]/70"
              }`}
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Controls */}
        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="flex flex-1 items-center gap-2 rounded-sm border border-[#14181B]/15 bg-white px-4 py-2.5">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" className="shrink-0 text-[#14181B]/35">
              <path d="M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.3-4.3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={tab === "website" ? "Search by URL…" : "Search by app / package…"}
              className="w-full border-0 bg-transparent p-0 text-sm outline-none placeholder:text-[#14181B]/35"
              style={{ fontFamily: "'IBM Plex Mono', monospace" }}
            />
          </div>

          {plans.length > 1 && (
            <div className="flex flex-wrap gap-2">
              {plans.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPlanFilter(p)}
                  className={`rounded-full border px-3.5 py-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] transition-colors duration-200 ${
                    planFilter === p
                      ? "border-[#14181B] bg-[#14181B] text-white"
                      : "border-[#14181B]/20 text-[#14181B]/60 hover:border-[#14181B]/40"
                  }`}
                  style={{ fontFamily: "'IBM Plex Mono', monospace" }}
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Results */}
        <div className="mt-6 overflow-hidden rounded-md border border-[#14181B]/12 bg-white">
          {activeState.loading && (
            <div className="p-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4 border-b border-[#14181B]/8 py-4 last:border-0">
                  <span className="h-2 w-2 rounded-full bg-[#14181B]/10" />
                  <span className="h-4 flex-1 animate-pulse rounded bg-[#14181B]/8" />
                  <span className="h-4 w-10 animate-pulse rounded bg-[#14181B]/8" />
                </div>
              ))}
            </div>
          )}

          {!activeState.loading && activeState.errored && (
            <div className="p-8 text-center text-sm text-[#14181B]/50">
              Couldn't load your history right now — try refreshing the page.
            </div>
          )}

          {!activeState.loading && !activeState.errored && filtered.length === 0 && (
            <div className="p-10 text-center">
              <p className="text-sm font-semibold text-[#14181B]">
                {entries.length === 0 ? "No audits filed yet" : "No matches"}
              </p>
              <p className="mt-1 text-xs text-[#14181B]/50">
                {entries.length === 0
                  ? tab === "website"
                    ? "Run your first website test and it'll show up here."
                    : "Run your first .apk / .ipa test and it'll show up here."
                  : "Try a different search or plan filter."}
              </p>
            </div>
          )}

          {!activeState.loading && !activeState.errored && filtered.length > 0 && (
            <div className="divide-y divide-[#14181B]/10">
              {filtered.map((entry) =>
                tab === "website" ? (
                  <HistoryRow key={entry.id} entry={entry} />
                ) : (
                  <MobileHistoryRow key={entry.id} entry={entry} />
                )
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function HistoryRow({ entry }) {
  const score = entry.health_score ?? 0;
  const passed = score >= 70;
  const color = passed ? "#1F5C45" : "#E4572E";

  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");

  async function handleDownload() {
    if (downloading) return;
    setDownloading(true);
    setDownloadError("");
    const result = await downloadHistoryReport(entry.id, entry.plan);
    if (!result.ok) setDownloadError(result.message);
    setDownloading(false);
  }

  return (
    <div className="flex flex-col gap-2 p-4 transition-colors duration-200 hover:bg-[#1F5C45]/[0.03] sm:flex-row sm:items-center sm:gap-4 sm:p-5">
      <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: color }} aria-hidden="true" />

      <div className="min-w-0 flex-1">
        <a
          href={entry.url}
          target="_blank"
          rel="noreferrer"
          className="truncate text-sm font-semibold text-[#14181B] hover:text-[#E4572E]"
          style={{ fontFamily: "'IBM Plex Mono', monospace" }}
          title={entry.url}
        >
          {shortUrl(entry.url)}
        </a>
        <p className="mt-0.5 text-xs text-[#14181B]/45">{formatDate(entry.created_at)}</p>
        {downloadError && (
          <p className="mt-0.5 text-xs text-[#E4572E]">{downloadError}</p>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-3 sm:justify-end">
        {entry.plan && (
          <span
            className="rounded-full border border-[#14181B]/15 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-[#14181B]/60"
            style={{ fontFamily: "'IBM Plex Mono', monospace" }}
          >
            {entry.plan}
          </span>
        )}
        <span
          className="rounded-sm border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.1em]"
          style={{
            fontFamily: "'IBM Plex Mono', monospace",
            color,
            borderColor: color,
          }}
        >
          {entry.severity || (passed ? "Pass" : "Flagged")}
        </span>
        <span className="w-8 text-right text-sm font-semibold" style={{ fontFamily: "'IBM Plex Mono', monospace", color }}>
          {score}
        </span>

        {entry.report_available && (
          <button
            type="button"
            onClick={handleDownload}
            disabled={downloading}
            title="Download report"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-sm border border-[#14181B]/15 text-[#14181B]/60 transition-colors duration-200 hover:border-[#1F5C45] hover:text-[#1F5C45] disabled:opacity-40"
          >
            {downloading ? (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" className="animate-spin">
                <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" strokeOpacity="0.25" />
                <path d="M21 12a9 9 0 00-9-9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

// Mirrors HistoryRow, but for a past .apk/.ipa scan: shows the app/package
// and platform instead of a URL, and downloads via /mobile/history/{id}/download.
function MobileHistoryRow({ entry }) {
  const score = entry.security_score ?? entry.health_score ?? 0;
  const passed = score >= 70;
  const color = passed ? "#1F5C45" : "#E4572E";
  const platform = entry.platform === "ios" ? "iOS" : "Android";

  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");

  async function handleDownload() {
    if (downloading) return;
    setDownloading(true);
    setDownloadError("");
    const result = await downloadMobileHistoryReport(entry.id, entry.plan);
    if (!result.ok) setDownloadError(result.message);
    setDownloading(false);
  }

  return (
    <div className="flex flex-col gap-2 p-4 transition-colors duration-200 hover:bg-[#1F5C45]/[0.03] sm:flex-row sm:items-center sm:gap-4 sm:p-5">
      <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: color }} aria-hidden="true" />

      <div className="min-w-0 flex-1">
        <p
          className="truncate text-sm font-semibold text-[#14181B]"
          style={{ fontFamily: "'IBM Plex Mono', monospace" }}
          title={appLabel(entry)}
        >
          {appLabel(entry)}
        </p>
        <p className="mt-0.5 text-xs text-[#14181B]/45">
          {platform} · {formatDate(entry.created_at)}
        </p>
        {downloadError && (
          <p className="mt-0.5 text-xs text-[#E4572E]">{downloadError}</p>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-3 sm:justify-end">
        {entry.plan && (
          <span
            className="rounded-full border border-[#14181B]/15 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.15em] text-[#14181B]/60"
            style={{ fontFamily: "'IBM Plex Mono', monospace" }}
          >
            {entry.plan}
          </span>
        )}
        <span
          className="rounded-sm border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.1em]"
          style={{
            fontFamily: "'IBM Plex Mono', monospace",
            color,
            borderColor: color,
          }}
        >
          {entry.severity || (passed ? "Pass" : "Flagged")}
        </span>
        <span className="w-8 text-right text-sm font-semibold" style={{ fontFamily: "'IBM Plex Mono', monospace", color }}>
          {score}
        </span>

        {entry.report_available && (
          <button
            type="button"
            onClick={handleDownload}
            disabled={downloading}
            title="Download report"
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-sm border border-[#14181B]/15 text-[#14181B]/60 transition-colors duration-200 hover:border-[#1F5C45] hover:text-[#1F5C45] disabled:opacity-40"
          >
            {downloading ? (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" className="animate-spin">
                <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2" strokeOpacity="0.25" />
                <path d="M21 12a9 9 0 00-9-9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            )}
          </button>
        )}
      </div>
    </div>
  );
}