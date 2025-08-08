"use client";
import React, { useEffect, useState } from "react";

type Staff = { name: string; is_active: boolean };

export interface PaymentModalProps {
  jobId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function PaymentModal({ jobId, onClose, onSuccess }: PaymentModalProps) {
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [staffName, setStaffName] = useState("");
  const [grams, setGrams] = useState<string>("");
  const [txnNo, setTxnNo] = useState("");
  const [pickedUpBy, setPickedUpBy] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>("");
  const [confirmOpen, setConfirmOpen] = useState(false);

  useEffect(() => {
    async function fetchStaff() {
      try {
        setLoadingStaff(true);
        setError("");
        const token = localStorage.getItem("token");
        const res = await fetch("/api/v1/staff", { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) throw new Error("Failed to load staff");
        const data = await res.json();
        const list: Staff[] = (data?.staff || []).filter((s: Staff) => s.is_active);
        setStaff(list);
      } catch (e) {
        setError("Failed to load staff list");
      } finally {
        setLoadingStaff(false);
      }
    }
    fetchStaff();
  }, []);

  const isValid = staffName.trim().length > 0 && !!grams && parseFloat(grams) > 0 && txnNo.trim().length > 0 && pickedUpBy.trim().length > 0;

  async function doSubmit() {
    try {
      setSubmitting(true);
      setError("");
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/v1/jobs/${jobId}/payment`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ staff_name: staffName, grams: parseFloat(grams), txn_no: txnNo, picked_up_by: pickedUpBy }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || "Payment failed");
      }
      onSuccess();
      onClose();
    } catch (e) {
      setError("Payment failed. Please check inputs and try again.");
    } finally {
      setSubmitting(false);
      setConfirmOpen(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid) return;
    setConfirmOpen(true);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white w-full max-w-md rounded-xl shadow-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Record Payment & Pickup</h3>
        {error && <div className="mb-3 text-sm text-red-600" role="alert">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="paymentStaff" className="block text-sm font-medium text-gray-700 mb-1">Performing Action As</label>
            <select
              id="paymentStaff"
              className="w-full border rounded-lg px-3 py-2 focus-ring"
              value={staffName}
              onChange={(e) => setStaffName(e.target.value)}
              disabled={loadingStaff}
              required
            >
              <option value="" disabled>{loadingStaff ? "Loading staff..." : "Select your name"}</option>
              {staff.map((s) => (
                <option key={s.name} value={s.name}>{s.name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="grams" className="block text-sm font-medium text-gray-700 mb-1">Weight (grams)</label>
              <input id="grams" type="number" min="0" step="0.1" className="w-full border rounded-lg px-3 py-2 focus-ring" value={grams} onChange={(e) => setGrams(e.target.value)} required />
            </div>
            <div>
              <label htmlFor="txnNo" className="block text-sm font-medium text-gray-700 mb-1">Txn Number</label>
              <input id="txnNo" className="w-full border rounded-lg px-3 py-2 focus-ring" value={txnNo} onChange={(e) => setTxnNo(e.target.value)} required />
            </div>
          </div>
          <div>
            <label htmlFor="pickedUpBy" className="block text-sm font-medium text-gray-700 mb-1">Picked up by</label>
            <input id="pickedUpBy" className="w-full border rounded-lg px-3 py-2 focus-ring" value={pickedUpBy} onChange={(e) => setPickedUpBy(e.target.value)} required />
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">Cancel</button>
            <button type="submit" disabled={!isValid || submitting} className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 focus-ring btn-transition">{submitting ? "Submitting..." : "Record & Mark Picked Up"}</button>
          </div>
          <p className="text-xs text-gray-500 mt-2">You will be asked to confirm on the next step.</p>
        </form>
      </div>

      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setConfirmOpen(false)} />
          <div className="relative bg-white w-full max-w-sm rounded-xl shadow-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Confirm Payment</h3>
            <p className="text-sm text-gray-600 mb-4">This will record payment and move the job to Paid & Picked Up.</p>
            <div className="flex justify-end space-x-2">
              <button onClick={() => setConfirmOpen(false)} className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">Cancel</button>
              <button onClick={doSubmit} className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 focus-ring btn-transition">Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


