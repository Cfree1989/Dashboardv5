"use client"

import { useState } from "react"
import { AdminSettings } from "@/components/admin/admin-settings"
import { StaffManagement } from "@/components/admin/staff-management"
import { AdminOverrides } from "@/components/admin/admin-overrides"
import { DataManagement } from "@/components/admin/data-management"
import { SystemHealth } from "@/components/admin/system-health"
import { EmailTools } from "@/components/admin/email-tools"
import { Settings, Users, Shield, Database, Activity, Mail } from 'lucide-react'

type AdminSection = "settings" | "staff" | "overrides" | "data" | "health" | "email"

export default function AdminPage() {
  const [activeSection, setActiveSection] = useState<AdminSection>("settings")

  const sections = [
    { id: "settings" as AdminSection, label: "Settings", icon: Settings },
    { id: "staff" as AdminSection, label: "Staff Management", icon: Users },
    { id: "overrides" as AdminSection, label: "Admin Overrides", icon: Shield },
    { id: "data" as AdminSection, label: "Data Management", icon: Database },
    { id: "health" as AdminSection, label: "System Health", icon: Activity },
    { id: "email" as AdminSection, label: "Email Tools", icon: Mail },
  ]

  const renderSection = () => {
    switch (activeSection) {
      case "settings":
        return <AdminSettings />
      case "staff":
        return <StaffManagement />
      case "overrides":
        return <AdminOverrides />
      case "data":
        return <DataManagement />
      case "health":
        return <SystemHealth />
      case "email":
        return <EmailTools />
      default:
        return <AdminSettings />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-gray-900 mb-4 md:mb-0">Admin Dashboard</h1>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => window.location.href = '/dashboard'}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Dashboard
            </button>
            <button
              onClick={() => window.location.href = '/analytics'}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Analytics
            </button>
            <button
              onClick={() => {
                if (typeof window !== "undefined") {
                  localStorage.removeItem("staffLoggedIn")
                  window.location.href = "/login"
                }
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
                  const Icon = section.icon
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`
                        w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors
                        ${
                          activeSection === section.id
                            ? "bg-blue-100 text-blue-700 border border-blue-200"
                            : "text-gray-600 hover:bg-gray-100"
                        }
                      `}
                    >
                      <Icon className="w-4 h-4 mr-3" />
                      {section.label}
                    </button>
                  )
                })}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {renderSection()}
          </div>
        </div>
      </div>
    </div>
  )
}
