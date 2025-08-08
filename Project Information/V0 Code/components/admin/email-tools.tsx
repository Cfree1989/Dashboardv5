"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Mail, Clock, AlertCircle } from 'lucide-react'

export function EmailTools() {
  const [jobId, setJobId] = useState("")
  const [emailType, setEmailType] = useState("")
  const [isResending, setIsResending] = useState(false)
  const [lastSent, setLastSent] = useState<Date | null>(null)
  const [rateLimitInfo, setRateLimitInfo] = useState({ remaining: 10, resetTime: null as Date | null })

  const emailTypes = [
    { value: "approval", label: "Approval Notification" },
    { value: "rejection", label: "Rejection Notification" },
    { value: "ready", label: "Ready for Pickup" },
    { value: "reminder", label: "Pickup Reminder" },
  ]

  const handleResendEmail = async () => {
    if (!jobId.trim() || !emailType) return

    try {
      setIsResending(true)
      
      console.log("Resending email:", { jobId: jobId.trim(), emailType })
      
      // Simulate API call with rate limiting
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      setLastSent(new Date())
      setRateLimitInfo(prev => ({ 
        ...prev, 
        remaining: Math.max(0, prev.remaining - 1),
        resetTime: new Date(Date.now() + 60000) // Reset in 1 minute
      }))
      
      // Reset form
      setJobId("")
      setEmailType("")
      
    } catch (error) {
      console.error("Error resending email:", error)
    } finally {
      setIsResending(false)
    }
  }

  const canSendEmail = rateLimitInfo.remaining > 0 && !isResending

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Mail className="w-5 h-5 text-blue-500" />
            <span>Resend Email Notifications</span>
          </CardTitle>
          <p className="text-sm text-gray-600">
            Manually resend email notifications to students for specific jobs.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="email-job-id">Job ID</Label>
            <Input
              id="email-job-id"
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              placeholder="Enter the job ID"
            />
          </div>

          <div>
            <Label htmlFor="email-type">Email Type</Label>
            <Select value={emailType} onValueChange={setEmailType}>
              <SelectTrigger>
                <SelectValue placeholder="Select email type" />
              </SelectTrigger>
              <SelectContent>
                {emailTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">
                Rate limit: {rateLimitInfo.remaining} emails remaining
              </span>
            </div>
            {rateLimitInfo.resetTime && (
              <span className="text-xs text-gray-500">
                Resets at {rateLimitInfo.resetTime.toLocaleTimeString()}
              </span>
            )}
          </div>

          {!canSendEmail && rateLimitInfo.remaining === 0 && (
            <div className="flex items-center space-x-2 p-3 bg-orange-50 border border-orange-200 rounded-lg">
              <AlertCircle className="w-4 h-4 text-orange-600" />
              <span className="text-sm text-orange-800">
                Rate limit reached. Please wait before sending more emails.
              </span>
            </div>
          )}

          <Button
            onClick={handleResendEmail}
            disabled={!jobId.trim() || !emailType || !canSendEmail}
            className="w-full"
          >
            {isResending ? "Sending..." : "Resend Email"}
          </Button>

          {lastSent && (
            <div className="text-sm text-green-600 text-center">
              Email sent successfully at {lastSent.toLocaleTimeString()}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
