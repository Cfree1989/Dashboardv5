"use client";
import React, { useState } from "react";
import { Mail, Clock, AlertCircle, Edit3, Save, X } from "lucide-react";
import { apiRequest } from "../../lib/auth";

export function EmailToolsPanel() {
  const [jobId, setJobId] = useState("");
  const [emailType, setEmailType] = useState("");
  const [isResending, setIsResending] = useState(false);
  const [lastSent, setLastSent] = useState<Date | null>(null);
  const [rateLimit, setRateLimit] = useState<{ remaining: number; resetTime: Date | null }>({ remaining: 10, resetTime: null });
  const [templates, setTemplates] = useState<{ approval: string; rejection: string; completion: string }>({ approval: '', rejection: '', completion: '' });
  const [editing, setEditing] = useState<{ key: 'approval'|'rejection'|'completion'|null }>({ key: null });

  const handleResend = async () => {
    if (!jobId.trim() || !emailType) return;
    setIsResending(true);
    try {
      await apiRequest(`/api/v1/jobs/${encodeURIComponent(jobId.trim())}/admin/resend-email`, {
        method: 'POST',
        body: JSON.stringify({ staff_name: 'Admin User' }),
      });
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

    {/* Email Templates Editor (Lightweight UI; persistence TBD) */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <Edit3 className="w-5 h-5 text-purple-500" />
            Email Templates
          </h2>
          <p className="text-sm text-gray-600">Edit the default text used when sending emails. HTML is derived from templates; these fields are for quick text updates.</p>
        </div>
        <div className="p-5 space-y-5">
          {(['approval','rejection','completion'] as const).map((k) => (
            <div key={k} className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-800 capitalize">{k} template (text)</label>
                {editing.key === k ? (
                  <div className="flex items-center gap-2">
                    <button
                      className="inline-flex items-center px-2 py-1 text-xs rounded bg-gray-800 text-white hover:bg-black"
                      onClick={() => setEditing({ key: null })}
                    >
                      <Save className="w-3 h-3 mr-1" /> Save
                    </button>
                    <button
                      className="inline-flex items-center px-2 py-1 text-xs rounded border hover:bg-gray-50"
                      onClick={() => setEditing({ key: null })}
                    >
                      <X className="w-3 h-3 mr-1" /> Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    className="inline-flex items-center px-2 py-1 text-xs rounded border hover:bg-gray-50"
                    onClick={() => setEditing({ key: k })}
                  >
                    <Edit3 className="w-3 h-3 mr-1" /> Edit
                  </button>
                )}
              </div>
              <textarea
                value={templates[k]}
                onChange={(e) => setTemplates((prev) => ({ ...prev, [k]: e.target.value }))}
                disabled={editing.key !== k}
                placeholder={`Custom ${k} text (optional)`}
                className="w-full min-h-[80px] border border-gray-300 rounded px-3 py-2 text-sm disabled:opacity-60"
              />
              <p className="text-xs text-gray-500">Note: These text fields are local to this session. Persisting templates to the server can be added next.</p>
            </div>
          ))}
        </div>
      </div>
      </div>
  );
}


