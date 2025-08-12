"use client";
import React, { useState } from "react";

export interface ConfirmDialogProps {
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  requireTextMatch?: {
    label: string; // e.g., "Type the Job short ID to confirm"
    expected: string; // expected text to match
    placeholder?: string;
  };
}

export default function ConfirmDialog({ title, description, confirmLabel = "Yes, I'm sure", cancelLabel = "Cancel", onConfirm, onCancel, requireTextMatch }: ConfirmDialogProps) {
  const [text, setText] = useState("");
  const disabled = !!requireTextMatch && text.trim() !== requireTextMatch.expected.trim();
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onCancel} />
      <div className="relative bg-white w-full max-w-sm rounded-xl shadow-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
        {description && <p className="text-sm text-gray-600 mb-4">{description}</p>}
        {requireTextMatch && (
          <div className="mb-4">
            <label className="block text-sm text-gray-700 mb-1">{requireTextMatch.label}</label>
            <input
              type="text"
              className="w-full border rounded-lg px-3 py-2 focus-ring text-sm"
              placeholder={requireTextMatch.placeholder || requireTextMatch.expected}
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>
        )}
        <div className="flex justify-end space-x-2">
          <button onClick={onCancel} className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition">{cancelLabel}</button>
          <button onClick={onConfirm} disabled={disabled} className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 focus-ring btn-transition">{confirmLabel}</button>
        </div>
      </div>
    </div>
  );
}


