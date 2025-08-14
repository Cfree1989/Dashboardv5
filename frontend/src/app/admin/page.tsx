"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Settings, Users, Shield, Database, Activity, Mail, AlertTriangle } from "lucide-react";
import { StaffPanel } from "../../components/admin/staff-panel";
import { SystemHealthPanel } from "../../components/admin/system-health";
import { AdminSettingsPanel } from "../../components/admin/admin-settings";
import { AdminOverridesPanel } from "../../components/admin/admin-overrides";
import { DataManagementPanel } from "../../components/admin/data-management";
import { EmailToolsPanel } from "../../components/admin/email-tools";

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
  const envLabel = typeof process !== "undefined" && process.env.NODE_ENV === "development" ? "DEV" : "PROD";
  const isDevelopment = typeof process !== "undefined" && process.env.NODE_ENV === "development";

  const sections: Array<{ id: AdminSection; label: string; icon: React.ComponentType<any>; devOnly?: boolean }> = [
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
        return <AdminSettingsPanel />;
      case "staff":
        return <StaffPanel />;
      case "overrides":
        return <AdminOverridesPanel />;
      case "data":
        return <DataManagementPanel />;
      case "health":
        return <SystemHealthPanel />;
      case "email":
        return <EmailToolsPanel />;
      default:
        return null;
    }
  };

  // Filter sections based on environment
  const visibleSections = sections.filter(section => !section.devOnly || isDevelopment);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header moved to global layout; keep page title for accessibility if needed */}
        <h1 className="sr-only">Admin Dashboard</h1>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Navigation */}
          <div className="lg:w-64 flex-shrink-0">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <nav className="space-y-2">
                {visibleSections.map((section) => {
                  const Icon = section.icon as any;
                  const active = activeSection === section.id;
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors ${
                        active ? "bg-blue-100 text-blue-700 border border-blue-200" : "text-gray-600 hover:bg-gray-100"
                      } ${section.devOnly ? "border-l-4 border-l-orange-400" : ""}`}
                    >
                      <Icon className="w-4 h-4 mr-3" />
                      {section.label}
                      {section.devOnly && (
                        <span className="ml-auto text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">
                          DEV
                        </span>
                      )}
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


