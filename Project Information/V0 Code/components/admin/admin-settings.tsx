"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import type { SystemInfo } from "@/types/admin"

export function AdminSettings() {
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [soundVolume, setSoundVolume] = useState(50)
  const [environmentBanner, setEnvironmentBanner] = useState("")
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    // Load current settings and system info
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      // Mock data - replace with actual API calls
      setSystemInfo({
        version: "v3.1.2",
        environment: "Production",
        uptime: "15 days, 3 hours",
        storageUsed: 45.2, // GB
        storageLimit: 100, // GB
      })
    } catch (error) {
      console.error("Error loading settings:", error)
    }
  }

  const handleSave = async () => {
    try {
      setIsSaving(true)
      // Save settings via API
      console.log("Saving settings:", {
        soundEnabled,
        soundVolume,
        environmentBanner,
      })
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000))
    } catch (error) {
      console.error("Error saving settings:", error)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Sound Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="sound-enabled"
              checked={soundEnabled}
              onCheckedChange={setSoundEnabled}
            />
            <Label htmlFor="sound-enabled">Enable background sound notifications</Label>
          </div>
          
          {soundEnabled && (
            <div className="space-y-2">
              <Label htmlFor="volume">Volume: {soundVolume}%</Label>
              <Input
                id="volume"
                type="range"
                min="0"
                max="100"
                value={soundVolume}
                onChange={(e) => setSoundVolume(Number(e.target.value))}
                className="w-full"
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Environment Banner</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="banner">Banner Message (optional)</Label>
            <Textarea
              id="banner"
              value={environmentBanner}
              onChange={(e) => setEnvironmentBanner(e.target.value)}
              placeholder="Enter a message to display at the top of all pages (e.g., 'MAINTENANCE SCHEDULED - System will be down Sunday 2-4 PM')"
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {systemInfo && (
        <Card>
          <CardHeader>
            <CardTitle>System Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
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
                  {systemInfo.storageUsed.toFixed(1)} GB / {systemInfo.storageLimit} GB
                  ({((systemInfo.storageUsed / systemInfo.storageLimit) * 100).toFixed(1)}%)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? "Saving..." : "Save Settings"}
        </Button>
      </div>
    </div>
  )
}
