"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { AlertTriangle, Unlock, CheckCircle, RotateCcw, XCircle } from 'lucide-react'

export function AdminOverrides() {
  const [jobId, setJobId] = useState("")
  const [selectedAction, setSelectedAction] = useState("")
  const [reason, setReason] = useState("")
  const [newStatus, setNewStatus] = useState("")
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)

  const actions = [
    { value: "unlock", label: "Force Unlock", icon: Unlock, description: "Remove any locks on the job" },
    { value: "confirm", label: "Force Confirm", icon: CheckCircle, description: "Mark job as confirmed without normal checks" },
    { value: "change_status", label: "Change Status", icon: RotateCcw, description: "Manually change job status" },
    { value: "mark_failed", label: "Mark Failed", icon: XCircle, description: "Mark job as failed with reason" },
  ]

  const statusOptions = [
    "UPLOADED",
    "PENDING", 
    "READYTOPRINT",
    "PRINTING",
    "COMPLETED",
    "PAIDPICKEDUP",
    "REJECTED"
  ]

  const handleSubmit = () => {
    if (!jobId.trim() || !selectedAction || !reason.trim()) return
    if (selectedAction === "change_status" && !newStatus) return
    
    setIsConfirmModalOpen(true)
  }

  const executeOverride = async () => {
    try {
      setIsProcessing(true)
      
      const overrideData = {
        jobId: jobId.trim(),
        action: selectedAction,
        reason: reason.trim(),
        ...(selectedAction === "change_status" && { newStatus }),
      }

      console.log("Executing admin override:", overrideData)
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      // Reset form
      setJobId("")
      setSelectedAction("")
      setReason("")
      setNewStatus("")
      setIsConfirmModalOpen(false)
      
    } catch (error) {
      console.error("Error executing override:", error)
    } finally {
      setIsProcessing(false)
    }
  }

  const selectedActionData = actions.find(a => a.value === selectedAction)

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            <span>Admin Overrides</span>
          </CardTitle>
          <p className="text-sm text-gray-600">
            Use these tools carefully. All actions are logged and require confirmation.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="job-id">Job ID</Label>
            <Input
              id="job-id"
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              placeholder="Enter the job ID to modify"
            />
          </div>

          <div>
            <Label htmlFor="action">Action</Label>
            <Select value={selectedAction} onValueChange={setSelectedAction}>
              <SelectTrigger>
                <SelectValue placeholder="Select an action" />
              </SelectTrigger>
              <SelectContent>
                {actions.map((action) => {
                  const Icon = action.icon
                  return (
                    <SelectItem key={action.value} value={action.value}>
                      <div className="flex items-center space-x-2">
                        <Icon className="w-4 h-4" />
                        <span>{action.label}</span>
                      </div>
                    </SelectItem>
                  )
                })}
              </SelectContent>
            </Select>
            {selectedActionData && (
              <p className="text-sm text-gray-500 mt-1">{selectedActionData.description}</p>
            )}
          </div>

          {selectedAction === "change_status" && (
            <div>
              <Label htmlFor="new-status">New Status</Label>
              <Select value={newStatus} onValueChange={setNewStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="Select new status" />
                </SelectTrigger>
                <SelectContent>
                  {statusOptions.map((status) => (
                    <SelectItem key={status} value={status}>
                      {status}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div>
            <Label htmlFor="reason">Reason (Required)</Label>
            <Textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why this override is necessary..."
              rows={3}
            />
          </div>

          <Button
            onClick={handleSubmit}
            disabled={!jobId.trim() || !selectedAction || !reason.trim() || (selectedAction === "change_status" && !newStatus)}
            className="w-full"
          >
            Execute Override
          </Button>
        </CardContent>
      </Card>

      <Dialog open={isConfirmModalOpen} onOpenChange={setIsConfirmModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <span>Confirm Admin Override</span>
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">
                <strong>Warning:</strong> This action will be logged and attributed to your account.
                Make sure this override is necessary and justified.
              </p>
            </div>
            <div className="space-y-2">
              <div><strong>Job ID:</strong> {jobId}</div>
              <div><strong>Action:</strong> {selectedActionData?.label}</div>
              {selectedAction === "change_status" && (
                <div><strong>New Status:</strong> {newStatus}</div>
              )}
              <div><strong>Reason:</strong> {reason}</div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsConfirmModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={executeOverride}
              disabled={isProcessing}
            >
              {isProcessing ? "Processing..." : "Confirm Override"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
