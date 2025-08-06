"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

const disciplineOptions = ['Art', 'Architecture', 'Landscape Architecture', 'Interior Design', 'Engineering', 'Hobby/Personal', 'Other'];
const printMethodOptions = ['Filament', 'Resin'];
const colorOptions: Record<string, string[]> = {
  Filament: [
    'True Red','True Orange','Light Orange','True Yellow','Dark Yellow','Lime Green','Green','Forest Green','Blue','Electric Blue','Midnight Purple','Light Purple','Clear','True White','Gray','True Black','Brown','Copper','Bronze','True Silver','True Gold','Glow in the Dark','Color Changing'
  ],
  Resin: ['Black','White','Gray','Clear']
};
const printerOptions = ['Prusa MK4S', 'Prusa XL', 'Raise3D Pro 2 Plus', 'Formlabs Form 3'];

export default function SubmissionForm() {
  const router = useRouter();
  const [studentName, setStudentName] = useState('');
  const [studentEmail, setStudentEmail] = useState('');
  const [discipline, setDiscipline] = useState('');
  const [classNumber, setClassNumber] = useState('');
  const [printMethod, setPrintMethod] = useState('');
  const [color, setColor] = useState('');
  const [printer, setPrinter] = useState('');
  const [minChargeConsent, setMinChargeConsent] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [emailError, setEmailError] = useState('');
  const [fileError, setFileError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    if (selected) {
      const ext = selected.name.slice(selected.name.lastIndexOf('.')).toLowerCase();
      const validExts = ['.stl', '.obj', '.3mf'];
      if (!validExts.includes(ext)) {
        setFileError('Invalid file type. Only .stl, .obj, .3mf allowed.');
        setFile(null);
        return;
      }
      if (selected.size > 50 * 1024 * 1024) {
        setFileError('File too large. Maximum size is 50MB.');
        setFile(null);
        return;
      }
      setFileError('');
      setFile(selected);
    } else {
      setFile(null);
      setFileError('');
    }
    setUploadProgress(0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Prevent submission if validation errors
    if (emailError || fileError) return;
    setIsSubmitting(true);
    setSubmitError('');
    try {
      const formData = new FormData();
      formData.append('student_name', studentName);
      formData.append('student_email', studentEmail);
      formData.append('discipline', discipline);
      formData.append('class_number', classNumber);
      formData.append('print_method', printMethod);
      formData.append('color', color);
      formData.append('printer', printer);
      formData.append('min_charge_consent', String(minChargeConsent));
      if (file) formData.append('file', file);
      const res = await fetch('/api/v1/submit', { method: 'POST', body: formData });
      const data = await res.json();
      if (res.ok) {
        router.push(`/submit/success?job=${data.id}`);
      } else {
        setSubmitError(data.message || 'Submission failed');
      }
    } catch (err) {
      setSubmitError('Network error, please try again');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-lg mx-auto">
      <div>
        <label htmlFor="studentName" className="block text-sm font-medium">Student Name</label>
        <input
          id="studentName"
          type="text"
          value={studentName}
          onChange={e => setStudentName(e.target.value)}
          className="mt-1 block w-full border rounded p-2"
        />
      </div>

      <div>
        <label htmlFor="studentEmail" className="block text-sm font-medium">Student Email</label>
        <input
          id="studentEmail"
          type="email"
          value={studentEmail}
          onChange={e => setStudentEmail(e.target.value)}
          onBlur={() => {
            const isValid = /^\S+@\S+\.\S+$/.test(studentEmail);
            setEmailError(isValid ? '' : 'Please enter a valid email address');
          }}
          className="mt-1 block w-full border rounded p-2"
        />
        {emailError && (
          <p className="text-red-600 text-sm mt-1">{emailError}</p>
        )}
      </div>

      <div>
        <label htmlFor="discipline" className="block text-sm font-medium">Discipline</label>
        <select
          id="discipline"
          value={discipline}
          onChange={e => setDiscipline(e.target.value)}
          className="mt-1 block w-full border rounded p-2"
        >
          <option value="">Select discipline</option>
          {disciplineOptions.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="classNumber" className="block text-sm font-medium">Class Number</label>
        <input
          id="classNumber"
          type="text"
          value={classNumber}
          onChange={e => setClassNumber(e.target.value)}
          className="mt-1 block w-full border rounded p-2"
        />
      </div>

      <div>
        <label htmlFor="printMethod" className="block text-sm font-medium">Print Method</label>
        <select
          id="printMethod"
          value={printMethod}
          onChange={e => setPrintMethod(e.target.value)}
          className="mt-1 block w-full border rounded p-2"
        >
          <option value="">Select print method</option>
          {printMethodOptions.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="color" className="block text-sm font-medium">Color Preference</label>
        <select
          id="color"
          value={color}
          onChange={e => setColor(e.target.value)}
          disabled={!printMethod}
          className="mt-1 block w-full border rounded p-2 disabled:opacity-50"
        >
          <option value="">Select color</option>
          {printMethod && colorOptions[printMethod].map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="printer" className="block text-sm font-medium">Printer Selection</label>
        <select
          id="printer"
          value={printer}
          onChange={e => setPrinter(e.target.value)}
          className="mt-1 block w-full border rounded p-2"
        >
          <option value="">Select printer</option>
          {printerOptions.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </div>

      <div className="flex items-center">
        <input
          id="minChargeConsent"
          type="checkbox"
          checked={minChargeConsent}
          onChange={e => setMinChargeConsent(e.target.checked)}
          className="h-4 w-4 text-blue-600 border-gray-300 rounded"
        />
        <label htmlFor="minChargeConsent" className="ml-2 block text-sm">
          I acknowledge the minimum $3.00 charge
        </label>
      </div>

      <div>
        <label htmlFor="file" className="block text-sm font-medium">File Upload</label>
        <input
          id="file"
          type="file"
          accept=".stl,.obj,.3mf"
          onChange={handleFileChange}
          className="mt-1 block w-full"
        />
        {uploadProgress > 0 && (
          <progress value={uploadProgress} max={100} className="mt-2 w-full" />
        )}
        {fileError && (
          <p className="text-red-600 text-sm mt-1">{fileError}</p>
        )}
      </div>

      {submitError && (
        <p className="text-red-600 text-center mb-4">{submitError}</p>
      )}
      <button
        type="submit"
        disabled={isSubmitting || !!emailError || !!fileError}
        className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        {isSubmitting ? 'Submitting...' : 'Submit'}
      </button>
    </form>
  );
}