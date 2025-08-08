"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, CheckCircle, Clock, Trash2 } from 'lucide-react'
import type { AuditReport } from "@/types/admin"

export function SystemHealth() {
  const [currentAudit, setCurrentAudit] = useState<AuditReport | null>(null)
  const [lastReport, setLastReport] = useState<AuditReport | null>(null)
  const [isStartingAudit, setIsStartingAudit] = useState(false)

  useEffect(() => {
    loadAuditStatus()
  }, [])

  const loadAuditStatus = async () => {
    try {
      // Mock data - replace with actual API calls
      setLastReport({
        id: "audit-123",
        startedAt: "2023-09-15T10:00:00Z",
        completedAt: "2023-09-15T10:15:00Z",
        status: "completed",
        orphanedFiles: 3,
        brokenFiles: 1,
        staleFiles: 5,
        totalScanned: 1247,
      })
    } catch (error) {
      console.error("Error loading audit status:", error)
    }
  }

  const startAudit = async () => {
    try {
      setIsStartingAudit(true)
      // API call to start audit
      console.log("Starting system audit...")
      
      // Simulate audit start
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setCurrentAudit({
        id: "audit-" + Date.now(),
        startedAt: new Date().toISOString(),
        completedAt: null,
        status: "running",
        orphanedFiles: 0,
        brokenFiles: 0,
        staleFiles: 0,
        totalScanned: 0,
      })
    } catch (error) {
      console.error("Error starting audit:", error)
    } finally {
      setIsStartingAudit(false)
    }
  }

  const deleteOrphanedFiles = async () => {
    try {
      // API call to delete orphaned files
      console.log("Deleting orphaned files...")
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
      // Refresh audit status
      loadAuditStatus()
    } catch (error) {
      console.error("Error deleting orphaned files:", error)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>System Integrity Audit</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">Run System Audit</h3>
              <p className="text-sm text-gray-500">
                Scan for orphaned, broken, and stale files in the system
              </p>
            </div>
            <Button
              onClick={startAudit}
              disabled={isStartingAudit || currentAudit?.status === "running"}
            >
              {isStartingAudit ? "Starting..." : "Start Audit"}
            </Button>
          </div>

          {currentAudit?.status === "running" && (
            <div className="flex items-center space-x-2 p-3 bg-blue-50 rounded-lg">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-blue-800">
                Audit in progress... Started at {new Date(currentAudit.startedAt).toLocaleTimeString()}
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {lastReport && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Last Audit Report
              <Badge variant={lastReport.status === "completed" ? "default" : "destructive"}>
                {lastReport.status}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
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

            {lastReport.orphanedFiles > 0 && (
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-orange-600" />
                  <span className="text-sm text-orange-800">
                    {lastReport.orphanedFiles} orphaned files found
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={deleteOrphanedFiles}
                >
                  <Trash2 className="w-4 h-4 mr-1" />
                  Clean Up
                </Button>
              </div>
            )}

            {lastReport.orphanedFiles === 0 && lastReport.brokenFiles === 0 && lastReport.staleFiles === 0 && (
              <div className="flex items-center space-x-2 p-3 bg-green-50 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-800">
                  System integrity check passed - no issues found
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
