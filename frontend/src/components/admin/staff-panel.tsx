"use client";
import React, { useEffect, useState } from "react";

interface StaffMember {
  name: string;
  is_active: boolean;
  added_at?: string | null;
  deactivated_at?: string | null;
}

export function StaffPanel() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [includeInactive, setIncludeInactive] = useState(false);
  const [newName, setNewName] = useState("");

  const fetchStaff = async () => {
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        window.location.href = "/login";
        return;
      }
      const params = new URLSearchParams();
      if (includeInactive) params.set("include_inactive", "true");
      const res = await fetch(`/api/v1/staff?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        return;
      }
      if (!res.ok) throw new Error(`Failed: ${res.status}`);
      const data = await res.json();
      setStaff(data.staff || []);
    } catch (e) {
      setError("Failed to load staff");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStaff();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [includeInactive]);

  const addStaff = async () => {
    setError("");
    const trimmed = newName.trim();
    if (!trimmed) return;
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        window.location.href = "/login";
        return;
      }
      const res = await fetch(`/api/v1/staff`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name: trimmed }),
      });
      if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        return;
      }
      if (res.status === 409) {
        setError("That name already exists");
        return;
      }
      if (!res.ok) throw new Error("Add failed");
      setNewName("");
      fetchStaff();
    } catch (e) {
      setError("Failed to add staff");
    }
  };

  const toggleActive = async (name: string, isActive: boolean) => {
    setError("");
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        window.location.href = "/login";
        return;
      }
      const res = await fetch(`/api/v1/staff/${encodeURIComponent(name)}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ is_active: !isActive }),
      });
      if (res.status === 401) {
        localStorage.removeItem("token");
        window.location.href = "/login";
        return;
      }
      if (!res.ok) throw new Error("Update failed");
      fetchStaff();
    } catch (e) {
      setError("Failed to update staff");
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mt-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-700">Staff Management</h2>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          />
          Show inactive
        </label>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="Add staff name"
          className="border border-gray-300 rounded px-3 py-2 text-sm flex-1"
        />
        <button
          onClick={addStaff}
          disabled={!newName.trim()}
          className="px-3 py-2 text-sm bg-blue-600 text-white rounded disabled:opacity-50"
        >
          Add
        </button>
      </div>

      {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
      {loading ? (
        <p className="text-sm text-gray-500">Loading staff…</p>
      ) : staff.length === 0 ? (
        <p className="text-sm text-gray-500">No staff found.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="py-2">Name</th>
              <th className="py-2">Status</th>
              <th className="py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {staff.map((s) => (
              <tr key={s.name} className="border-b last:border-b-0">
                <td className="py-2">{s.name}</td>
                <td className="py-2">
                  {s.is_active ? (
                    <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-800">Active</span>
                  ) : (
                    <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">Inactive</span>
                  )}
                </td>
                <td className="py-2">
                  <button
                    onClick={() => toggleActive(s.name, s.is_active)}
                    className="px-2 py-1 text-xs rounded bg-gray-800 text-white hover:bg-black"
                  >
                    {s.is_active ? "Deactivate" : "Reactivate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}


