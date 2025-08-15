"use client";
import React, { useEffect, useState, useMemo } from "react";
import { useToast } from "../../ui/toast";
import { apiRequest } from "../../../lib/auth";

type Staff = { name: string; is_active: boolean };

type JobDetails = {
  material: string;
  cost_usd: number;
};

export interface PaymentModalProps {
  jobId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function PaymentModal({ jobId, onClose, onSuccess }: PaymentModalProps) {
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [jobDetails, setJobDetails] = useState<JobDetails | null>(null);
  const [loadingJob, setLoadingJob] = useState(false);
  const [staffName, setStaffName] = useState("");
  const [grams, setGrams] = useState<string>("");
  const [txnNo, setTxnNo] = useState("");
  const [pickedUpBy, setPickedUpBy] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const { show } = useToast();

  useEffect(() => {
    async function fetchStaff() {
      try {
        setLoadingStaff(true);
        setError("");
        const data = await apiRequest<any>("/api/v1/staff");
        const list: Staff[] = (data?.staff || []).filter((s: Staff) => s.is_active);
        setStaff(list);
      } catch (e) {
        setError("Failed to load staff list");
      } finally {
        setLoadingStaff(false);
      }
    }

    async function fetchJobDetails() {
      try {
        setLoadingJob(true);
        setError("");
        const data = await apiRequest<any>(`/api/v1/jobs/${jobId}`);
        setJobDetails({
          material: data.material || 'filament',
          cost_usd: data.cost_usd || 0
        });
      } catch (e) {
        setError("Failed to load job details");
      } finally {
        setLoadingJob(false);
      }
    }

    // Explicitly clear form fields when modal opens
    setGrams("");
    setTxnNo("");
    setPickedUpBy("");
    setStaffName("");
    setConfirmOpen(false);
    setError("");

    fetchStaff();
    fetchJobDetails();
  }, [jobId]);

  // Calculate final price from grams with material-specific rate and $3 minimum
  const finalPrice = useMemo(() => {
    if (!grams || !jobDetails) return 0;
    const gramsNum = parseFloat(grams);
    if (isNaN(gramsNum) || gramsNum <= 0) return 0;
    
    const materialRate = (jobDetails.material || '').toLowerCase() === 'resin' ? 0.20 : 0.10;
    const rawCost = gramsNum * materialRate;
    return Math.max(3.0, rawCost); // $3.00 minimum charge
  }, [grams, jobDetails]);

  const materialRate = jobDetails ? ((jobDetails.material || '').toLowerCase() === 'resin' ? 0.20 : 0.10) : 0.10;
  const rateText = materialRate === 0.20 ? '$0.20/g (Resin)' : '$0.10/g (Filament)';

  const isValid = staffName.trim().length > 0 && !!grams && parseFloat(grams) > 0 && txnNo.trim().length > 0 && pickedUpBy.trim().length > 0;

  async function doSubmit() {
    try {
      setSubmitting(true);
      setError("");
      await apiRequest(`/api/v1/jobs/${jobId}/payment`, {
        method: "POST",
        body: JSON.stringify({ staff_name: staffName, grams: parseFloat(grams), txn_no: txnNo, picked_up_by: pickedUpBy }),
      });
      show('Payment recorded');
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

          {/* Material and Pricing Info */}
          {loadingJob ? (
            <div className="text-sm text-gray-500">Loading job details...</div>
          ) : jobDetails && (
            <div className="bg-gray-50 rounded-lg p-3 space-y-2">
              <div className="text-sm">
                <span className="font-medium">Material:</span> {jobDetails.material || 'Filament'}
              </div>
              <div className="text-sm">
                <span className="font-medium">Rate:</span> {rateText}
              </div>
              {jobDetails.cost_usd > 0 && (
                <div className="text-sm">
                  <span className="font-medium">Estimated Cost:</span> ${jobDetails.cost_usd.toFixed(2)}
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="grams" className="block text-sm font-medium text-gray-700 mb-1">Weight (grams)</label>
              <input 
                id="grams" 
                type="number" 
                min="0" 
                step="0.1" 
                className="w-full border rounded-lg px-3 py-2 focus-ring" 
                value={grams} 
                onChange={(e) => setGrams(e.target.value)} 
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
                placeholder="Enter weight"
                required 
              />
            </div>
            <div>
              <label htmlFor="txnNo" className="block text-sm font-medium text-gray-700 mb-1">Txn Number</label>
              <input 
                id="txnNo" 
                className="w-full border rounded-lg px-3 py-2 focus-ring" 
                value={txnNo} 
                onChange={(e) => setTxnNo(e.target.value)} 
                autoComplete="off"
                placeholder="Enter transaction number"
                required 
              />
            </div>
          </div>

          {/* Live Final Price Preview */}
          {grams && parseFloat(grams) > 0 && jobDetails && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="text-sm font-medium text-blue-900">Final Price Preview</div>
              <div className="text-lg font-semibold text-blue-900">${finalPrice.toFixed(2)}</div>
              {finalPrice === 3.0 && parseFloat(grams) * materialRate < 3.0 && (
                <div className="text-xs text-blue-700 mt-1">Minimum charge of $3.00 applied</div>
              )}
            </div>
          )}
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
            <p className="text-sm text-gray-600 mb-3">This will record payment and move the job to Paid & Picked Up.</p>
            
            {/* Final Price Confirmation */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
              <div className="text-sm font-medium text-blue-900">Final Amount to Charge</div>
              <div className="text-xl font-bold text-blue-900">${finalPrice.toFixed(2)}</div>
              <div className="text-xs text-blue-700 mt-1">
                {parseFloat(grams)}g × {rateText} = ${(parseFloat(grams) * materialRate).toFixed(2)}
                {finalPrice === 3.0 && parseFloat(grams) * materialRate < 3.0 && " (minimum charge applied)"}
              </div>
            </div>
            
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


