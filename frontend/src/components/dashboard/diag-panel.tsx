"use client";
import React, { useState } from "react";
import { apiClient } from "../../lib/unified-api-client";

type DiagInfo = {
  db_engine?: string | null;
  db_url_sanitized?: string | null;
  migration_head?: string | null;
  job_counts_by_status?: Record<string, number>;
  app_env?: string;
};

export function DiagPanel() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [info, setInfo] = useState<DiagInfo | null>(null);

  // Load diagnostics automatically on mount
  React.useEffect(() => {
    fetchDiag();
  }, []);

  const fetchDiag = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiClient.get<DiagInfo>("/api/v1/_diag");
      setInfo(data);
    } catch (e) {
      setError("Failed to fetch diagnostics");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mt-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-gray-700">Diagnostics</h2>
        {loading && <span className="text-sm text-gray-500">Loading...</span>}
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {info && (
        <div className="text-sm text-gray-800 space-y-1">
          <div>
            <span className="font-medium">DB Engine:</span> {info.db_engine || "-"}
          </div>
          <div>
            <span className="font-medium">DB URI:</span> {info.db_url_sanitized || "-"}
          </div>
          <div>
            <span className="font-medium">Migration Head:</span> {info.migration_head || "-"}
          </div>
          <div>
            <span className="font-medium">App Env:</span> {info.app_env || "-"}
          </div>
          <div>
            <span className="font-medium">Job Counts:</span>
            <ul className="list-disc ml-5">
              {Object.entries(info.job_counts_by_status || {}).map(([k, v]) => (
                <li key={k}>
                  <span className="font-mono">{k}</span>: {v}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
      {!info && !error && !loading && (
        <p className="text-sm text-gray-500">Loading system diagnostics...</p>
      )}
    </div>
  );
}


