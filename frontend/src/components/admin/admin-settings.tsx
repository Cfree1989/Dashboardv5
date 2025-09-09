"use client";
import React, { useEffect, useState } from "react";
import { useSoundStore } from "../../store";
import type { SoundVariant } from "../../store/types";
import { initDashboardAudio, configureSound, testSound } from "../../lib/sound-utils";

type SystemInfo = {
  version: string;
  environment: string;
  uptime: string;
  storageUsed: number; // GB
  storageLimit: number; // GB
};

export function AdminSettingsPanel() {
  const { soundEnabled, volume, variant, setSoundEnabled, setVolume, setVariant } = useSoundStore();
  const [environmentBanner, setEnvironmentBanner] = useState("");
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    // Mock data to populate UI similar to V0. Replace with API later.
    setSystemInfo({
      version: "v3.1.2",
      environment: (typeof process !== "undefined" && process.env.NODE_ENV === "development") ? "Development" : "Production",
      uptime: "—",
      storageUsed: 45.2,
      storageLimit: 100,
    });
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // POST settings to backend
      const response = await fetch('/api/v1/admin/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          staff_name: 'admin', // This should come from auth context
          sound: {
            enabled: soundEnabled,
            volume: Math.round((volume || 0) * 100)
          },
          environment_banner: environmentBanner
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save settings');
      }

      const result = await response.json();
      console.log('Settings saved:', result);
      
    } catch (error) {
      console.error('Failed to save settings:', error);
      // In a real app, you'd show a toast notification here
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Sound Configuration */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">Sound Configuration</h2>
        </div>
        <div className="p-5 space-y-4">
          <label className="inline-flex items-center gap-2 text-sm text-gray-800">
            <input type="checkbox" checked={!!soundEnabled} onChange={(e) => setSoundEnabled(e.target.checked)} />
            Enable background sound notifications
          </label>
          {soundEnabled && (
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-700">Volume: {Math.round((volume || 0) * 100)}%</label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={Math.round((volume || 0) * 100)}
                  onChange={(e) => setVolume(Number(e.target.value) / 100)}
                  className="w-full"
                />
              </div>
              <div>
                <label className="text-sm text-gray-700 block mb-1">Sound Variant</label>
                <select
                  className="border border-gray-300 rounded px-2 py-1 text-sm"
                  value={variant}
                  onChange={(e) => setVariant(e.target.value as SoundVariant)}
                >
                  <option value="chime">Chime</option>
                  <option value="beep">Beep</option>
                  <option value="bell">Bell</option>
                  <option value="tone">Tone</option>
                  <option value="ping">Ping</option>
                  <option value="double">Double</option>
                  <option value="triad">Triad</option>
                  <option value="siren">Siren</option>
                </select>
              </div>
              <div>
                <button
                  type="button"
                  disabled={!soundEnabled}
                  onClick={async () => {
                    await initDashboardAudio();
                    configureSound({ volume, variant });
                    await testSound();
                  }}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  Test Sound
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Environment Banner */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">Environment Banner</h2>
        </div>
        <div className="p-5">
          <div className="space-y-2">
            <label htmlFor="banner" className="text-sm text-gray-700">Banner Message (optional)</label>
            <textarea
              id="banner"
              rows={3}
              value={environmentBanner}
              onChange={(e) => setEnvironmentBanner(e.target.value)}
              placeholder="Enter a message to display at the top of all pages (e.g., 'MAINTENANCE SCHEDULED - Sunday 2-4 PM')"
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>
        </div>
      </div>

      {/* System Information */}
      {systemInfo && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="px-5 py-4 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-900">System Information</h2>
          </div>
          <div className="p-5 grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Version:</span>
              <p className="font-medium">{systemInfo.version}</p>
            </div>
            <div>
              <span className="text-gray-500">Environment:</span>
              <p className="font-medium">{systemInfo.environment}</p>
            </div>
            <div>
              <span className="text-gray-500">Uptime:</span>
              <p className="font-medium">{systemInfo.uptime}</p>
            </div>
            <div>
              <span className="text-gray-500">Storage:</span>
              <p className="font-medium">
                {systemInfo.storageUsed.toFixed(1)} GB / {systemInfo.storageLimit} GB ({((systemInfo.storageUsed / systemInfo.storageLimit) * 100).toFixed(1)}%)
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-end">
        <button onClick={handleSave} disabled={isSaving} className="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-black disabled:opacity-50">
          {isSaving ? "Saving…" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}


