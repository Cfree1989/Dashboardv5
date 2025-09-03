"use client";
import React, { useState, useRef, useEffect } from 'react';
import { apiClient } from '../../lib/unified-api-client';
import { createErrorState, updateErrorState, clearErrorState } from '../../lib/error-handling';
import { InlineError } from '../ui/error-display';
import { Job } from '../../types';

interface Staff {
  name: string;
  is_active: boolean;
}

interface JobCardNotesProps {
  job: Job;
  jobNotes: string;
  onNotesUpdated: (newNotes: string) => void;
  staff: Staff[];
  loadingStaff: boolean;
}

export function JobCardNotes({ 
  job, 
  jobNotes, 
  onNotesUpdated, 
  staff, 
  loadingStaff 
}: JobCardNotesProps) {
  const MAX_NOTES_LEN = 5000;
  const MAX_ENTRY_LEN = 1000;
  
  // Local notes editing state
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [notesDraft, setNotesDraft] = useState<string>("");
  const [notesStaffName, setNotesStaffName] = useState<string>("");
  const [savingNotes, setSavingNotes] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string>("");
  const [saveError, setSaveError] = useState(createErrorState());
  
  const notesTextareaRef = useRef<HTMLTextAreaElement | null>(null);
  const notesSectionId = `notes-section-${job.id}`;

  // Focus the textarea when entering edit mode for quick typing
  useEffect(() => {
    if (isEditingNotes) {
      setTimeout(() => notesTextareaRef.current?.focus(), 0);
    }
  }, [isEditingNotes]);

  const beginEditNotes = async () => {
    setIsEditingNotes(true);
    setNotesDraft("");
    setSaveMessage("");
    setSaveError(clearErrorState());
  };

  const cancelEditNotes = () => {
    setIsEditingNotes(false);
    setNotesDraft("");
    setNotesStaffName("");
    setSaveMessage("");
    setSaveError(clearErrorState());
  };

  const saveNotes = async () => {
    if (!notesStaffName) {
      setSaveError(updateErrorState(saveError, new Error('Please select your name before saving.')));
      return;
    }
    
    if (notesDraft.length === 0) {
      setSaveError(updateErrorState(saveError, new Error('Please enter a note.')));
      return;
    }
    
    if (notesDraft.length > MAX_ENTRY_LEN) {
      setSaveError(updateErrorState(saveError, new Error(`Note must be at most ${MAX_ENTRY_LEN} characters.`)));
      return;
    }
    
    try {
      setSavingNotes(true);
      setSaveError(clearErrorState());
      setSaveMessage("Saving...");
      
      const data = await apiClient.post<{ notes?: string }>(`/api/v1/jobs/${job.id}/notes`, { 
        text: notesDraft, 
        staff_name: notesStaffName 
      });
      
      const newNotes = data?.notes || (jobNotes ? `${jobNotes}\n${notesDraft}` : notesDraft);
      onNotesUpdated(newNotes);
      
      setSaveMessage('Saved');
      setIsEditingNotes(false);
      setNotesDraft("");
    } catch (e) {
      setSaveError(updateErrorState(saveError, e));
    } finally {
      setSavingNotes(false);
      setTimeout(() => setSaveMessage(""), 1500);
    }
  };

  return (
    <div id={notesSectionId}>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-900">Staff Notes</h4>
      </div>
      
      {/* No notes state */}
      {!isEditingNotes && !jobNotes && (
        <div
          className="text-sm text-gray-500 italic mb-3 cursor-pointer focus-ring"
          role="button"
          tabIndex={0}
          onClick={beginEditNotes}
          onKeyDown={(e) => { 
            if (e.key === 'Enter' || e.key === ' ') { 
              e.preventDefault(); 
              beginEditNotes(); 
            } 
          }}
          aria-label="Click to add a note"
        >
          No notes added yet — click to add
        </div>
      )}
      
      {/* Existing notes display */}
      {jobNotes && !isEditingNotes && (
        <div className="mb-4">
          <div
            className="bg-gray-50 p-2 rounded border cursor-pointer focus-ring"
            role="button"
            tabIndex={0}
            onClick={beginEditNotes}
            onKeyDown={(e) => { 
              if (e.key === 'Enter' || e.key === ' ') { 
                e.preventDefault(); 
                beginEditNotes(); 
              } 
            }}
            aria-label="Click to add or edit note"
          >
            <ul className="list-disc ml-5 space-y-1 text-sm text-gray-900">
              {(jobNotes.split('\n').filter(Boolean).reverse()).map((line, idx) => (
                <li key={idx}>{line}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
      
      {/* Notes editing interface */}
      {isEditingNotes && (
        <div className="mt-1 space-y-3">
          {/* Show existing notes while editing */}
          {jobNotes && (
            <div>
              <span className="text-gray-500 text-sm">Existing notes:</span>
              <div className="bg-gray-50 p-2 rounded border mt-1">
                <ul className="list-disc ml-5 space-y-1 text-sm text-gray-900">
                  {(jobNotes.split('\n').filter(Boolean).reverse()).map((line, idx) => (
                    <li key={idx}>{line}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}
          
          {/* New note input */}
          <div className="px-1">
            <label htmlFor={`notes-${job.id}`} className="text-gray-500 text-sm block mb-1">
              Add a new note
            </label>
            <textarea
              id={`notes-${job.id}`}
              className="w-full min-h-[100px] border rounded-lg px-3 py-2 focus-ring text-sm"
              value={notesDraft}
              onChange={(e) => setNotesDraft(e.target.value)}
              aria-describedby={`notes-status-${job.id}`}
              placeholder="Type your note to append…"
              ref={notesTextareaRef}
            />
            <div className="mt-1 text-xs text-gray-500">{notesDraft.length}/{MAX_NOTES_LEN}</div>
          </div>
          
          {/* Staff selection and action buttons */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div>
              <label htmlFor={`notesStaff-${job.id}`} className="block text-sm text-gray-700 mb-1">
                Performing Action As
              </label>
              <select
                id={`notesStaff-${job.id}`}
                className="w-full border rounded-lg px-3 py-2 focus-ring text-sm"
                value={notesStaffName}
                onChange={(e) => setNotesStaffName(e.target.value)}
                disabled={loadingStaff}
              >
                <option value="" disabled>
                  {loadingStaff ? 'Loading staff...' : 'Select your name'}
                </option>
                {staff.map(s => (
                  <option key={s.name} value={s.name}>{s.name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-end justify-end space-x-2">
              <button 
                onClick={cancelEditNotes} 
                type="button" 
                className="px-3 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition"
              >
                Cancel
              </button>
              <button 
                onClick={saveNotes} 
                type="button" 
                disabled={savingNotes || !notesStaffName || notesDraft.length > MAX_NOTES_LEN} 
                className="px-3 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 focus-ring btn-transition"
              >
                {savingNotes ? 'Saving...' : 'Save Notes'}
              </button>
            </div>
          </div>
          
          {/* Status messages and errors */}
          <div id={`notes-status-${job.id}`} className="mt-1 text-sm" aria-live="polite">
            {saveMessage && <span className="text-green-600">{saveMessage}</span>}
            {saveError.hasError && (
              <InlineError
                error={saveError}
                className="mt-1"
              />
            )}
            {notesDraft.length > MAX_NOTES_LEN && (
              <div className="text-red-600" role="alert">
                Notes must be at most {MAX_NOTES_LEN} characters.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
