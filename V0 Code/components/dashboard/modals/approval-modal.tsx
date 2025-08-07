"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface ApprovalModalProps {
  isOpen: boolean
  onClose: () => void
  jobId: string
}

export function ApprovalModal({ isOpen, onClose, jobId }: ApprovalModalProps) {
  const [weight, setWeight] = useState("")
  const [time, setTime] = useState("")
  const [material, setMaterial] = useState("PLA")
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Calculate cost based on weight and material
  const calculateCost = () => {
    const weightNum = Number.parseFloat(weight)
    if (isNaN(weightNum)) return 0

    const rate = material.toLowerCase().includes("resin") ? 0.2 : 0.1
    const calculatedCost = weightNum * rate

    // Apply $3.00 minimum
    return Math.max(calculatedCost, 3.0)
  }

  const cost = calculateCost()

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true)

      // In a real implementation, this would make an API call
      // await approveJob(jobId, { weight, time, material, cost })

      console.log("Approving job:", { jobId, weight, time, material, cost })

      // Close the modal after successful submission
      onClose()
    } catch (error) {
      console.error("Error approving job:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Approve Print Job</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="weight" className="text-right">
              Weight (g)
            </Label>
            <Input
              id="weight"
              type="number"
              min="0"
              step="0.1"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              className="col-span-3"
              placeholder="Enter weight in grams"
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="time" className="text-right">
              Time (hours)
            </Label>
            <Input
              id="time"
              type="number"
              min="0"
              step="0.5"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="col-span-3"
              placeholder="Enter time in hours"
            />
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="material" className="text-right">
              Material
            </Label>
            <select
              id="material"
              value={material}
              onChange={(e) => setMaterial(e.target.value)}
              className="col-span-3 flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="PLA">PLA Filament</option>
              <option value="PETG">PETG Filament</option>
              <option value="ABS">ABS Filament</option>
              <option value="TPU">TPU Filament</option>
              <option value="Resin">Standard Resin</option>
              <option value="Tough Resin">Tough Resin</option>
            </select>
          </div>

          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right">Cost</Label>
            <div className="col-span-3 font-medium">
              ${cost.toFixed(2)}
              {cost === 3.0 && <span className="text-sm text-gray-500 ml-2">(Minimum charge applied)</span>}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!weight || !time || isSubmitting}>
            {isSubmitting ? "Approving..." : "Approve Job"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
