"use client";
import React, { useState } from "react";
import { Mail, Clock, AlertCircle } from "lucide-react";

export function EmailToolsPanel() {
  const [jobId, setJobId] = useState("");
  const [emailType, setEmailType] = useState("");
  const [isResending, setIsResending] = useState(false);
  const [lastSent, setLastSent] = useState<Date | null>(null);
  const [rateLimit, setRateLimit] = useState<{ remaining: number; resetTime: Date | null }>({ remaining: 10, resetTime: null });

  const handleResend = async () => {
    if (!jobId.trim() || !emailType) return;
    setIsResending(true);
    try {
      // TODO: call POST /jobs/:id/admin/resend-email when backend exists
      await new Promise((r) => setTimeout(r, 1200));
      setLastSent(new Date());
      setRateLimit((prev) => ({ remaining: Math.max(0, prev.remaining - 1), resetTime: new Date(Date.now() + 60000) }));
      setJobId("");
      setEmailType("");
    } finally {
      setIsResending(false);
    }
  };

  const canSend = rateLimit.remaining > 0 && !isResending;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <Mail className="w-5 h-5 text-blue-500" />
            Resend Email Notifications
          </h2>
          <p className="text-sm text-gray-600">Manually resend email notifications to students for specific jobs.</p>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label htmlFor="email-job-id" className="text-sm text-gray-700">Job ID</label>
            <input id="email-job-id" value={jobId} onChange={(e) => setJobId(e.target.value)} placeholder="Enter the job ID" className="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>

          <div>
            <label htmlFor="email-type" className="text-sm text-gray-700">Email Type</label>
            <select id="email-type" value={emailType} onChange={(e) => setEmailType(e.target.value)} className="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm">
              <option value="">Select email type</option>
              <option value="approval">Approval Notification</option>
              <option value="rejection">Rejection Notification</option>
              <option value="ready">Ready for Pickup</option>
              <option value="reminder">Pickup Reminder</option>
            </select>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Rate limit: {rateLimit.remaining} emails remaining</span>
            </div>
            {rateLimit.resetTime && (
              <span className="text-xs text-gray-500">Resets at {rateLimit.resetTime.toLocaleTimeString()}</span>
            )}
          </div>

          {!canSend && rateLimit.remaining === 0 && (
            <div className="flex items-center gap-2 p-3 bg-orange-50 border border-orange-200 rounded-lg">
              <AlertCircle className="w-4 h-4 text-orange-600" />
              <span className="text-sm text-orange-800">Rate limit reached. Please wait before sending more emails.</span>
            </div>
          )}

          <button onClick={handleResend} disabled={!jobId.trim() || !emailType || !canSend} className="w-full px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-black disabled:opacity-50">
            {isResending ? "Sending…" : "Resend Email"}
          </button>

          {lastSent && (
            <div className="text-sm text-green-600 text-center">Email sent successfully at {lastSent.toLocaleTimeString()}</div>
          )}
        </div>
      </div>
    </div>
  );
}


