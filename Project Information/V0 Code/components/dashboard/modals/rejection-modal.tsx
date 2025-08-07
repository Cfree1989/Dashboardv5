"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

interface RejectionModalProps {
  isOpen: boolean
  onClose: () => void
  jobId: string
}

const REJECTION_REASONS = [
  { id: "broken_mesh", label: "Broken/non-manifold mesh" },
  { id: "too_large", label: "Model too large for printer" },
  { id: "too_complex", label: "Model too complex/detailed" },
  { id: "thin_walls", label: "Walls too thin for printing" },
  { id: "unsupported", label: "Insufficient supports for overhangs" },
  { id: "wrong_format", label: "Incorrect file format" },
  { id: "policy_violation", label: "Violates lab policies" },
]

export function RejectionModal({ isOpen, onClose, jobId }: RejectionModalProps) {
  const [selectedReasons, setSelectedReasons] = useState<string[]>([])
  const [customReason, setCustomReason] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleReasonToggle = (reasonId: string) => {
    setSelectedReasons((prev) => (prev.includes(reasonId) ? prev.filter((id) => id !== reasonId) : [...prev, reasonId]))
  }

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true)

      const reasons = {
        selected: selectedReasons,
        custom: customReason,
      }

      // In a real implementation, this would make an API call
      // await rejectJob(jobId, reasons)

      console.log("Rejecting job:", { jobId, reasons })

      // Close the modal after successful submission
      onClose()
    } catch (error) {
      console.error("Error rejecting job:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const isValid = selectedReasons.length > 0 || customReason.trim().length > 0

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Reject Print Job</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div>
            <h3 className="mb-3 text-sm font-medium">Select rejection reasons:</h3>
            <div className="space-y-2">
              {REJECTION_REASONS.map((reason) => (
                <div key={reason.id} className="flex items-center space-x-2">
                  <Checkbox
                    id={reason.id}
                    checked={selectedReasons.includes(reason.id)}
                    onCheckedChange={() => handleReasonToggle(reason.id)}
                  />
                  <Label htmlFor={reason.id}>{reason.label}</Label>
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="custom-reason">Custom reason (optional):</Label>
            <Textarea
              id="custom-reason"
              value={customReason}
              onChange={(e) => setCustomReason(e.target.value)}
              placeholder="Enter additional details about why this job is being rejected..."
              className="min-h-[100px]"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={handleSubmit} disabled={!isValid || isSubmitting}>
            {isSubmitting ? "Rejecting..." : "Reject Job"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
