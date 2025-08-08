"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Archive, Trash2, AlertTriangle } from 'lucide-react'

export function DataManagement() {
  const [archiveRetentionDays, setArchiveRetentionDays] = useState(90)
  const [pruneOlderThanDays, setPruneOlderThanDays] = useState(365)
  const [isArchiveModalOpen, setIsArchiveModalOpen] = useState(false)
  const [isPruneModalOpen, setIsPruneModalOpen] = useState(false)
  const [previewCounts, setPreviewCounts] = useState({ archive: 0, prune: 0 })
  const [isProcessing, setIsProcessing] = useState(false)

  const getArchivePreview = async () => {
    try {
      // API call to get preview count
      console.log("Getting archive preview for", archiveRetentionDays, "days")
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500))
      setPreviewCounts(prev => ({ ...prev, archive: 45 }))
      setIsArchiveModalOpen(true)
    } catch (error) {
      console.error("Error getting archive preview:", error)
    }
  }

  const getPrunePreview = async () => {
    try {
      // API call to get preview count
      console.log("Getting prune preview for", pruneOlderThanDays, "days")
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 500))
      setPreviewCounts(prev => ({ ...prev, prune: 12 }))
      setIsPruneModalOpen(true)
    } catch (error) {
      console.error("Error getting prune preview:", error)
    }
  }

  const executeArchive = async () => {
    try {
      setIsProcessing(true)
      console.log("Archiving jobs older than", archiveRetentionDays, "days")
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      setIsArchiveModalOpen(false)
    } catch (error) {
      console.error("Error archiving jobs:", error)
    } finally {
      setIsProcessing(false)
    }
  }

  const executePrune = async () => {
    try {
      setIsProcessing(true)
      console.log("Pruning archived jobs older than", pruneOlderThanDays, "days")
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      setIsPruneModalOpen(false)
    } catch (error) {
      console.error("Error pruning jobs:", error)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Archive className="w-5 h-5 text-blue-500" />
            <span>Archive Jobs</span>
          </CardTitle>
          <p className="text-sm text-gray-600">
            Move completed jobs to archive storage to free up active database space.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="archive-retention">Archive jobs older than (days)</Label>
            <Input
              id="archive-retention"
              type="number"
              min="1"
              value={archiveRetentionDays}
              onChange={(e) => setArchiveRetentionDays(Number(e.target.value))}
            />
            <p className="text-sm text-gray-500 mt-1">
              Jobs in COMPLETED or PAIDPICKEDUP status older than this will be archived.
            </p>
          </div>
          <Button onClick={getArchivePreview} className="w-full">
            Preview Archive Operation
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Trash2 className="w-5 h-5 text-red-500" />
            <span>Prune Archived Jobs</span>
          </CardTitle>
          <p className="text-sm text-gray-600">
            Permanently delete old archived jobs to free up storage space.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="prune-retention">Delete archived jobs older than (days)</Label>
            <Input
              id="prune-retention"
              type="number"
              min="1"
              value={pruneOlderThanDays}
              onChange={(e) => setPruneOlderThanDays(Number(e.target.value))}
            />
            <p className="text-sm text-gray-500 mt-1">
              Archived jobs older than this will be permanently deleted.
            </p>
          </div>
          <Button onClick={getPrunePreview} variant="destructive" className="w-full">
            Preview Prune Operation
          </Button>
        </CardContent>
      </Card>

      {/* Archive Confirmation Modal */}
      <Dialog open={isArchiveModalOpen} onOpenChange={setIsArchiveModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Archive Operation</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>{previewCounts.archive} jobs</strong> will be moved to archive storage.
              </p>
            </div>
            <p className="text-sm text-gray-600">
              Jobs older than {archiveRetentionDays} days in COMPLETED or PAIDPICKEDUP status will be archived.
              This operation is reversible.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsArchiveModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={executeArchive} disabled={isProcessing}>
              {isProcessing ? "Archiving..." : "Archive Jobs"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Prune Confirmation Modal */}
      <Dialog open={isPruneModalOpen} onOpenChange={setIsPruneModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <span>Confirm Prune Operation</span>
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-800">
                <strong>Warning:</strong> {previewCounts.prune} archived jobs will be permanently deleted.
                This operation cannot be undone.
              </p>
            </div>
            <p className="text-sm text-gray-600">
              Archived jobs older than {pruneOlderThanDays} days will be permanently removed from the system.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsPruneModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={executePrune} disabled={isProcessing}>
              {isProcessing ? "Deleting..." : "Delete Jobs"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
