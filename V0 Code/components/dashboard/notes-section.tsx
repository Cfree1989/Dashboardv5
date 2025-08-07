"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Edit3, Save, X, FileText } from "lucide-react"
import { useDashboard } from "./dashboard-context"

interface NotesSectionProps {
  jobId: string
  notes: string | null
  isExpanded: boolean
}

export function NotesSection({ jobId, notes, isExpanded }: NotesSectionProps) {
  const { updateNotes } = useDashboard()
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState(notes || "")
  const [isSaving, setIsSaving] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Focus textarea when editing starts
  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus()
      textareaRef.current.setSelectionRange(textareaRef.current.value.length, textareaRef.current.value.length)
    }
  }, [isEditing])

  const handleEdit = () => {
    setEditValue(notes || "")
    setIsEditing(true)
  }

  const handleCancel = () => {
    setEditValue(notes || "")
    setIsEditing(false)
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const success = await updateNotes(jobId, editValue.trim())
      if (success) {
        setIsEditing(false)
      } else {
        // Handle error - could show a toast notification
        console.error("Failed to save notes")
      }
    } catch (error) {
      console.error("Error saving notes:", error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      handleCancel()
    } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      handleSave()
    }
  }

  if (!isExpanded) {
    // Show compact notes indicator when collapsed
    if (notes && notes.trim()) {
      return (
        <div className="flex items-center text-xs text-gray-500 mt-2">
          <FileText className="w-3 h-3 mr-1" />
          <span className="truncate">Has notes</span>
        </div>
      )
    }
    return null
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-900 flex items-center">
          <FileText className="w-4 h-4 mr-1" />
          Staff Notes
        </h4>
        {!isEditing && (
          <button
            onClick={handleEdit}
            className="flex items-center text-xs text-blue-600 hover:text-blue-800 transition-colors"
          >
            <Edit3 className="w-3 h-3 mr-1" />
            {notes ? "Edit" : "Add Note"}
          </button>
        )}
      </div>

      {isEditing ? (
        <div className="space-y-2">
          <textarea
            ref={textareaRef}
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add internal notes about this job..."
            className="w-full p-2 text-sm border border-gray-300 rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={3}
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">Press Ctrl+Enter to save, Esc to cancel</span>
            <div className="flex space-x-2">
              <button
                onClick={handleCancel}
                className="flex items-center px-2 py-1 text-xs text-gray-600 hover:text-gray-800 transition-colors"
                disabled={isSaving}
              >
                <X className="w-3 h-3 mr-1" />
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                <Save className="w-3 h-3 mr-1" />
                {isSaving ? "Saving..." : "Save"}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-sm text-gray-700">
          {notes && notes.trim() ? (
            <div className="bg-gray-50 p-2 rounded border">
              <p className="whitespace-pre-wrap">{notes}</p>
            </div>
          ) : (
            <p className="text-gray-500 italic">No notes added yet</p>
          )}
        </div>
      )}
    </div>
  )
}
