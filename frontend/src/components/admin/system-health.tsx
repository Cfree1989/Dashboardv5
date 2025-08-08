"use client";
import React, { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle, Clock, Trash2 } from "lucide-react";

type AuditReport = {
  id: string;
  startedAt: string;
  completedAt: string | null;
  status: "running" | "completed";
  orphanedFiles: number;
  brokenFiles: number;
  staleFiles: number;
  totalScanned: number;
};

export function SystemHealthPanel() {
  const [currentAudit, setCurrentAudit] = useState<AuditReport | null>(null);
  const [lastReport, setLastReport] = useState<AuditReport | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  useEffect(() => {
    // Mock initial data to match screenshot layout; replace with API calls later
    setLastReport({
      id: "audit-123",
      startedAt: new Date().toISOString(),
      completedAt: new Date().toISOString(),
      status: "completed",
      orphanedFiles: 3,
      brokenFiles: 1,
      staleFiles: 5,
      totalScanned: 1247,
    });
  }, []);

  const startAudit = async () => {
    setIsStarting(true);
    try {
      // TODO: call POST /api/v1/admin/audit/start when backend exists
      await new Promise((r) => setTimeout(r, 800));
      setCurrentAudit({
        id: `audit-${Date.now()}`,
        startedAt: new Date().toISOString(),
        completedAt: null,
        status: "running",
        orphanedFiles: 0,
        brokenFiles: 0,
        staleFiles: 0,
        totalScanned: 0,
      });
    } finally {
      setIsStarting(false);
    }
  };

  const cleanUpOrphans = async () => {
    // TODO: call DELETE /api/v1/admin/audit/orphaned-file (batch when available)
    await new Promise((r) => setTimeout(r, 500));
  };

  return (
    <div className="space-y-6">
      {/* System Integrity Audit card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">System Integrity Audit</h2>
        </div>
        <div className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900">Run System Audit</h3>
              <p className="text-sm text-gray-500">Scan for orphaned, broken, and stale files in the system</p>
            </div>
            <button
              onClick={startAudit}
              disabled={isStarting || currentAudit?.status === "running"}
              className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-black disabled:opacity-50"
            >
              {isStarting ? "Starting…" : "Start Audit"}
            </button>
          </div>

          {currentAudit?.status === "running" && (
            <div className="mt-4 flex items-center space-x-2 p-3 bg-blue-50 rounded-lg">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-blue-800">
                Audit in progress… Started at {new Date(currentAudit.startedAt).toLocaleTimeString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Last Audit Report card */}
      {lastReport && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">Last Audit Report</h2>
            <span className="text-xs px-2 py-1 rounded-full bg-gray-900 text-white">{lastReport.status}</span>
          </div>
          <div className="p-5">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{lastReport.totalScanned}</div>
                <div className="text-sm text-gray-500">Files Scanned</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{lastReport.orphanedFiles}</div>
                <div className="text-sm text-gray-500">Orphaned Files</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{lastReport.brokenFiles}</div>
                <div className="text-sm text-gray-500">Broken Files</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{lastReport.staleFiles}</div>
                <div className="text-sm text-gray-500">Stale Files</div>
              </div>
            </div>

            <div className="text-sm text-gray-500 mb-4">
              Completed: {lastReport.completedAt ? new Date(lastReport.completedAt).toLocaleString() : "In progress"}
            </div>

            {lastReport.orphanedFiles > 0 ? (
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-orange-600" />
                  <span className="text-sm text-orange-800">{lastReport.orphanedFiles} orphaned files found</span>
                </div>
                <button
                  onClick={cleanUpOrphans}
                  className="px-3 py-1 text-xs rounded border border-gray-300 hover:bg-gray-50 flex items-center"
                >
                  <Trash2 className="w-4 h-4 mr-1" />
                  Clean Up
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2 p-3 bg-green-50 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-800">System integrity check passed — no issues found</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


