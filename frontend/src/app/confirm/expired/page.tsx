"use client";
import React, { useState } from "react";

export default function ExpiredConfirmPage() {
  const [jobId, setJobId] = useState("");
  const [token, setToken] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState<string>("");

  async function onResend(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setMessage("");
    try {
      const res = await fetch("/api/v1/submit/resend-confirmation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(token ? { token } : { job_id: jobId }),
      });
      if (res.ok) {
        setStatus("success");
        setMessage("A new confirmation email has been sent if the job exists and isn't already confirmed.");
      } else {
        const data = await res.json().catch(() => ({}));
        setStatus("error");
        setMessage(data.message || "Failed to resend confirmation.");
      }
    } catch (err) {
      setStatus("error");
      setMessage("Network error. Please try again.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-yellow-50 to-white py-12">
      <div className="bg-card p-8 rounded-xl shadow-md max-w-lg w-full">
        <h1 className="text-2xl font-bold mb-4 text-yellow-700">Confirmation Link Expired</h1>
        <p className="text-sm text-foreground mb-6">Enter your Job ID or paste the expired token to receive a new confirmation link.</p>

        <form onSubmit={onResend} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Job ID (preferred)</label>
            <input
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              className="w-full border rounded-md px-3 py-2"
              placeholder="e.g., 9f1c2a..."
            />
          </div>
          <div className="text-center text-sm text-muted">or</div>
          <div>
            <label className="block text-sm font-medium mb-1">Expired Token</label>
            <textarea
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="w-full border rounded-md px-3 py-2 h-24"
              placeholder="Paste the link token here"
            />
          </div>

        {status === "success" && (
          <div className="bg-green-50 border border-green-200 rounded p-3 text-green-800 text-sm">{message}</div>
        )}
        {status === "error" && (
          <div className="bg-red-50 border border-red-200 rounded p-3 text-red-800 text-sm">{message}</div>
        )}

          <div className="mt-4 flex gap-3">
            <button
              type="submit"
              disabled={status === "loading" || (!jobId && !token)}
              className="bg-primary text-primary-foreground px-4 py-2 rounded-lg btn-transition focus-ring disabled:opacity-50"
            >
              {status === "loading" ? "Sending..." : "Resend Confirmation"}
            </button>
            <a href="/submit" className="px-4 py-2 rounded-lg border">Back to Submit</a>
          </div>
        </form>
      </div>
    </div>
  );
}
