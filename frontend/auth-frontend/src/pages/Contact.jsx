// src/pages/Contact.jsx
import { useState } from "react";
import Navbar from "../components/Navbar";

// idle -> sending -> sent
export default function Contact() {
  const [status, setStatus] = useState("idle");
  const [form, setForm] = useState({ name: "", email: "", message: "" });

  function handleSubmit(e) {
    e.preventDefault();
    // No backend endpoint for this yet — this just simulates a send so
    // the page isn't a dead end. Wire this up to a real /contact
    // endpoint (or an email service) when you're ready.
    setStatus("sending");
    setTimeout(() => setStatus("sent"), 1100);
  }

  return (
    <div className="min-h-screen bg-[#F7F1E1]">
      <Navbar />

      <div className="mx-auto max-w-3xl px-4 py-14 sm:px-6">
        <p className="text-center text-xs font-semibold uppercase tracking-[0.25em] text-[#0b3327]/50">
          Get in touch
        </p>
        <h1 className="mt-2 text-center font-serif text-3xl font-medium text-[#0b3327]">Contact us</h1>
        <p className="mx-auto mt-3 max-w-sm text-center text-sm text-[#0b3327]/60">
          Questions about a plan or a report? Send us a message and we'll get back to you.
        </p>

        {/* Card */}
        <div className="relative mt-10">
          {/* Floating side decorations, peeking out from the card edges */}
          <span className="pointer-events-none absolute -left-3 top-16 h-6 w-6 rounded-full bg-white shadow-sm animate-[floatY_4s_ease-in-out_infinite]" />
          <span className="pointer-events-none absolute -left-3 top-28 h-3 w-3 rounded-full bg-white/70 shadow-sm animate-[floatY_5s_ease-in-out_infinite_0.4s]" />
          <span className="pointer-events-none absolute -right-3 top-20 h-5 w-5 rounded-full bg-[#d4af37] shadow-sm animate-[floatY_4.5s_ease-in-out_infinite_0.2s]" />

          <div className="relative overflow-hidden rounded-3xl bg-white p-6 shadow-sm sm:p-10">
            {/* Decorative blurred circles */}
            <span className="pointer-events-none absolute -left-10 top-10 h-40 w-40 rounded-full bg-[#d4af37]/10 blur-2xl" />
            <span className="pointer-events-none absolute bottom-0 left-16 h-24 w-24 rounded-full bg-[#0b3327]/5 blur-2xl" />

            <div className="relative grid grid-cols-1 gap-8 sm:grid-cols-2 sm:items-center">
              {/* Left: illustration / status */}
              <div className="flex min-h-[260px] flex-col items-center justify-center">
                {status === "idle" && <PaperPlane />}
                {status === "sending" && <PaperPlane flying />}
                {status === "sent" && (
                  <div className="flex flex-col items-center text-center animate-[fadeIn_0.4s_ease-out]">
                    <div className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-green-500">
                      <svg
                        width="28"
                        height="28"
                        viewBox="0 0 24 24"
                        fill="none"
                        aria-hidden="true"
                        className="animate-[checkPop_0.5s_ease-out]"
                      >
                        <path d="M5 13l4 4L19 7" stroke="#16a34a" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                    <p className="mt-4 text-base font-semibold text-[#0b3327]">Sent successfully!</p>
                    <p className="mt-1 text-xs text-[#0b3327]/50">We'll be in touch soon.</p>
                  </div>
                )}
              </div>

              {/* Right: form */}
              <div>
                <h2 className="mb-5 text-right text-lg font-semibold text-[#0b3327] sm:text-left">Contact us</h2>

                {status !== "sent" ? (
                  <form onSubmit={handleSubmit} className="space-y-3">
                    <FieldWithIcon icon={<UserIcon />}>
                      <input
                        required
                        disabled={status === "sending"}
                        placeholder="Your name"
                        value={form.name}
                        onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                        className="w-full border-0 bg-transparent p-0 text-sm text-[#0b3327] outline-none placeholder:text-[#0b3327]/40 disabled:opacity-50"
                      />
                    </FieldWithIcon>

                    <FieldWithIcon icon={<MailIcon />}>
                      <input
                        required
                        type="email"
                        disabled={status === "sending"}
                        placeholder="Your email"
                        value={form.email}
                        onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                        className="w-full border-0 bg-transparent p-0 text-sm text-[#0b3327] outline-none placeholder:text-[#0b3327]/40 disabled:opacity-50"
                      />
                    </FieldWithIcon>

                    <FieldWithIcon icon={<MessageIcon />} alignTop>
                      <textarea
                        required
                        rows={3}
                        disabled={status === "sending"}
                        placeholder="Your message"
                        value={form.message}
                        onChange={(e) => setForm((f) => ({ ...f, message: e.target.value }))}
                        className="w-full resize-none border-0 bg-transparent p-0 text-sm text-[#0b3327] outline-none placeholder:text-[#0b3327]/40 disabled:opacity-50"
                      />
                    </FieldWithIcon>

                    <button
                      type="submit"
                      disabled={status === "sending"}
                      className="mt-2 flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-[#0f4436] to-[#061f17] py-3 text-sm font-semibold text-white shadow-md transition hover:scale-[1.01] hover:shadow-lg active:scale-[0.99] disabled:opacity-60"
                    >
                      {status === "sending" ? "Sending…" : "Submit"}
                      {status !== "sending" && (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                          <path d="M5 12h14M13 6l6 6-6 6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      )}
                    </button>
                  </form>
                ) : (
                  <div className="rounded-2xl bg-[#F7F1E1] p-4 text-left text-xs text-[#0b3327]/60">
                    <p className="font-medium text-[#0b3327]">{form.name}</p>
                    <p className="mt-0.5">{form.email}</p>
                    <p className="mt-2 leading-relaxed">{form.message}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Social row */}
            <div className="relative mt-8 flex items-center justify-center gap-3">
              <SocialIcon href="https://facebook.com" bg="#1877F2" label="Facebook">
                <path
                  d="M14 9h2V6h-2c-1.66 0-3 1.34-3 3v2H9v3h2v6h3v-6h2.1l.4-3H14V9z"
                  fill="white"
                />
              </SocialIcon>
              <SocialIcon href="https://twitter.com" bg="#1DA1F2" label="Twitter">
                <path
                  d="M20 7.4c-.5.2-1 .4-1.6.5.6-.3 1-.9 1.2-1.6-.5.3-1.1.6-1.8.7-.5-.6-1.3-1-2.1-1-1.6 0-2.9 1.3-2.9 2.9 0 .2 0 .4.1.7-2.4-.1-4.6-1.3-6-3.1-.3.4-.4.9-.4 1.5 0 1 .5 1.9 1.3 2.4-.5 0-.9-.1-1.3-.3v.1c0 1.4 1 2.6 2.3 2.9-.2.1-.5.1-.8.1-.2 0-.4 0-.5-.1.4 1.2 1.5 2 2.8 2.1-1 .8-2.3 1.3-3.7 1.3-.2 0-.5 0-.7-.1 1.3.9 2.9 1.4 4.6 1.4 5.5 0 8.6-4.6 8.6-8.6v-.4c.6-.4 1.1-1 1.5-1.5z"
                  fill="white"
                />
              </SocialIcon>
              <SocialIcon href="https://instagram.com" bg="linear-gradient(135deg,#f58529,#dd2a7b,#8134af,#515bd4)" label="Instagram">
                <path
                  d="M12 8.8a3.2 3.2 0 100 6.4 3.2 3.2 0 000-6.4zM12 14a2 2 0 110-4 2 2 0 010 4z"
                  fill="white"
                />
                <path
                  d="M15.5 6H8.5A2.5 2.5 0 006 8.5v7A2.5 2.5 0 008.5 18h7a2.5 2.5 0 002.5-2.5v-7A2.5 2.5 0 0015.5 6zm1.2 2.5a.8.8 0 11-1.6 0 .8.8 0 011.6 0zM12 16.2A4.2 4.2 0 1112 7.8a4.2 4.2 0 010 8.4z"
                  fill="white"
                />
              </SocialIcon>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes checkPop { 0% { transform: scale(0.5); opacity: 0; } 70% { transform: scale(1.1); } 100% { transform: scale(1); opacity: 1; } }
        @keyframes floatY { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
        @keyframes planeBob { 0%, 100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-10px) rotate(-2deg); } }
        @keyframes planeFly {
          0% { transform: translate(0, 0) rotate(0deg) scale(1); opacity: 1; }
          60% { transform: translate(60px, -50px) rotate(18deg) scale(0.85); opacity: 1; }
          100% { transform: translate(160px, -120px) rotate(24deg) scale(0.5); opacity: 0; }
        }
      `}</style>
    </div>
  );
}

function FieldWithIcon({ icon, children, alignTop = false }) {
  return (
    <div
      className={`flex gap-2.5 rounded-xl bg-[#F7F1E1] px-3.5 py-2.5 transition-colors focus-within:bg-[#F0E7CE] ${
        alignTop ? "items-start" : "items-center"
      }`}
    >
      <span className={`shrink-0 text-[#0b3327]/40 ${alignTop ? "mt-0.5" : ""}`}>{icon}</span>
      {children}
    </div>
  );
}

function PaperPlane({ flying = false }) {
  return (
    <div className="relative flex h-40 w-40 items-center justify-center">
      <span className="pointer-events-none absolute h-32 w-32 rounded-full bg-[#d4af37]/10 blur-xl" />
      <svg
        width="96"
        height="96"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
        className="relative"
        style={{
          animation: flying ? "planeFly 1.1s ease-in forwards" : "planeBob 3.5s ease-in-out infinite",
        }}
      >
        <path
          d="M21 3L2 10.5l7.5 2.5L13 20l3-7 5-10z"
          fill={flying ? "#1f9d55" : "#d4af37"}
          stroke="#0b3327"
          strokeWidth="1"
          strokeLinejoin="round"
        />
        <path d="M9.5 13L21 3l-7 10-4.5-1z" fill="#0b3327" opacity="0.15" />
      </svg>
    </div>
  );
}

function UserIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 12a4 4 0 100-8 4 4 0 000 8zM5 20a7 7 0 0114 0"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MailIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 5h16v14H4V5zm0 0l8 7 8-7"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MessageIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 5h16v12H8l-4 4V5z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SocialIcon({ href, bg, label, children }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      aria-label={label}
      style={{ background: bg }}
      className="flex h-9 w-9 items-center justify-center rounded-full shadow-sm transition-transform duration-200 hover:scale-110"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
        {children}
      </svg>
    </a>
  );
}