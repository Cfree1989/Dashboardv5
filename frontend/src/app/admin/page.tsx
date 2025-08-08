"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Settings, Users, Shield, Database, Activity, Mail } from "lucide-react";
import { DiagPanel } from "../../components/dashboard/diag-panel";
import { StaffPanel } from "../../components/admin/staff-panel";

type AdminSection = "settings" | "staff" | "overrides" | "data" | "health" | "email";

export default function AdminPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  const [activeSection, setActiveSection] = useState<AdminSection>("settings");

  const sections: Array<{ id: AdminSection; label: string; icon: React.ComponentType<any> }> = [
    { id: "settings", label: "Settings", icon: Settings },
    { id: "staff", label: "Staff Management", icon: Users },
    { id: "overrides", label: "Admin Overrides", icon: Shield },
    { id: "data", label: "Data Management", icon: Database },
    { id: "health", label: "System Health", icon: Activity },
    { id: "email", label: "Email Tools", icon: Mail },
  ];

  const renderSection = () => {
    switch (activeSection) {
      case "settings":
        return (
          <div className="space-y-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <h2 className="text-sm font-semibold text-gray-700 mb-2">Settings</h2>
              <p className="text-sm text-gray-500">Background sound and environment banner configuration (coming soon).</p>
            </div>
          </div>
        );
      case "staff":
        return <StaffPanel />;
      case "overrides":
        return (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-1">Admin Overrides</h3>
            <p className="text-sm text-gray-500">Force unlock/confirm, change status, mark failed. Pending backend.</p>
          </div>
        );
      case "data":
        return (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-1">Data Management</h3>
            <p className="text-sm text-gray-500">Archive and prune controls. Pending backend.</p>
          </div>
        );
      case "health":
        return (
          <div className="space-y-4">
            <DiagPanel />
          </div>
        );
      case "email":
        return (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-1">Email Tools</h3>
            <p className="text-sm text-gray-500">Resend emails with cooldowns. Pending backend.</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-gray-900 mb-4 md:mb-0">Admin Dashboard</h1>
          <div className="flex items-center space-x-4">
            <Link href="/dashboard" className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
              Dashboard
            </Link>
            <Link href="/analytics" className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
              Analytics
            </Link>
            <button
              onClick={() => {
                localStorage.removeItem("token");
                router.push("/login");
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Navigation */}
          <div className="lg:w-64 flex-shrink-0">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <nav className="space-y-2">
                {sections.map((section) => {
                  const Icon = section.icon as any;
                  const active = activeSection === section.id;
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors ${
                        active ? "bg-blue-100 text-blue-700 border border-blue-200" : "text-gray-600 hover:bg-gray-100"
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-3" />
                      {section.label}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">{renderSection()}</div>
        </div>
      </div>
    </div>
  );
}


