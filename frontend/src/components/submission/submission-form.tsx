"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

const disciplineOptions = ['Art', 'Architecture', 'Landscape Architecture', 'Interior Design', 'Engineering', 'Hobby/Personal', 'Other'];
const printMethodOptions = ['Filament', 'Resin'];
const colorOptions: Record<string, string[]> = {
  Filament: [
    'True Red','True Orange','Light Orange','True Yellow','Dark Yellow','Lime Green','Green','Forest Green','Blue','Electric Blue','Midnight Purple','Light Purple','Clear','True White','Gray','True Black','Brown','Copper','Bronze','True Silver','True Gold','Glow in the Dark','Color Changing'
  ],
  Resin: ['Black','White','Gray','Clear']
};
const printerOptions: Record<string, string[]> = {
  Filament: ['Prusa MK4S', 'Prusa XL', 'Raise3D Pro 2 Plus'],
  Resin: ['Formlabs Form 3']
};

export default function SubmissionForm() {
  const router = useRouter();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [studentEmail, setStudentEmail] = useState('');
  const [discipline, setDiscipline] = useState('');
  const [classNumber, setClassNumber] = useState('');
  const [printMethod, setPrintMethod] = useState('');
  const [color, setColor] = useState('');
  const [printer, setPrinter] = useState('');
  const [availablePrinters, setAvailablePrinters] = useState<string[]>([]);
  const [minChargeConsent, setMinChargeConsent] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [emailError, setEmailError] = useState('');
  const [fileError, setFileError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  // Validation error states
  const [firstNameError, setFirstNameError] = useState('');
  const [lastNameError, setLastNameError] = useState('');
  const [disciplineError, setDisciplineError] = useState('');
  const [classNumberError, setClassNumberError] = useState('');
  const [printMethodError, setPrintMethodError] = useState('');
  const [colorError, setColorError] = useState('');
  const [printerError, setPrinterError] = useState('');
  const [minChargeError, setMinChargeError] = useState('');
  const [scalingConfirmed, setScalingConfirmed] = useState(false);
  const [scalingError, setScalingError] = useState('');

  React.useEffect(() => {
    if (printMethod) {
      setAvailablePrinters(printerOptions[printMethod] || []);
      setPrinter(''); // Reset printer selection when method changes
    } else {
      setAvailablePrinters([]);
      setPrinter('');
    }
  }, [printMethod]);

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

    // Clear previous errors
    setFirstNameError(''); setLastNameError(''); setDisciplineError('');
    setClassNumberError(''); setPrintMethodError(''); setColorError('');
    setPrinterError(''); setMinChargeError(''); setScalingError('');
    setEmailError(''); // reuse existing state
    setSubmitError('');
    let firstErrorField: string | null = null;

    // Validate first name
    if (firstName.trim().length < 2 || firstName.trim().length > 100) {
      setFirstNameError('First name must be between 2 and 100 characters');
      if (!firstErrorField) firstErrorField = 'firstName';
    }
    // Validate last name
    if (lastName.trim().length < 2 || lastName.trim().length > 100) {
      setLastNameError('Last name must be between 2 and 100 characters');
      if (!firstErrorField) firstErrorField = 'lastName';
    }
    // Validate email
    if (!studentEmail.trim()) {
      setEmailError('Email is required');
      if (!firstErrorField) firstErrorField = 'studentEmail';
    } else if (!/^\S+@\S+\.\S+$/.test(studentEmail) || studentEmail.length > 100) {
      setEmailError('Please enter a valid email under 100 characters');
      if (!firstErrorField) firstErrorField = 'studentEmail';
    }
    // Validate discipline
    if (!discipline) {
      setDisciplineError('Please select a discipline');
      if (!firstErrorField) firstErrorField = 'discipline';
    }
    // Validate class number
    if (!classNumber.trim()) {
      setClassNumberError('Class number is required');
      if (!firstErrorField) firstErrorField = 'classNumber';
    } else if (classNumber.length > 50) {
      setClassNumberError('Class number cannot exceed 50 characters');
      if (!firstErrorField) firstErrorField = 'classNumber';
    }
    // Validate print method
    if (!printMethod) {
      setPrintMethodError('Please select a print method');
      if (!firstErrorField) firstErrorField = 'printMethod';
    }
    // Validate color
    if (!color) {
      setColorError('Please select a color');
      if (!firstErrorField) firstErrorField = 'color';
    }
    // Validate printer
    if (!printer) {
      setPrinterError('Please select a printer');
      if (!firstErrorField) firstErrorField = 'printer';
    }
    // Validate minimum charge consent
    if (!minChargeConsent) {
      setMinChargeError('You must acknowledge the minimum charge');
      if (!firstErrorField) firstErrorField = 'minChargeConsent';
    }
    // Validate scaling confirmation
    if (!scalingConfirmed) {
      setScalingError('You must confirm that you have scaled your model correctly');
      if (!firstErrorField) firstErrorField = 'scalingConfirmed';
    }
    // Validate file
    if (!file) {
      setFileError('Please upload a model file');
      if (!firstErrorField) firstErrorField = 'file';
    }
    // If any errors, scroll to first and abort
    if (firstErrorField) {
      const el = document.getElementById(firstErrorField);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('student_first_name', firstName);
      formData.append('student_last_name', lastName);
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
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="firstName" className="block text-sm font-medium text-gray-700">First Name</label>
        <input
          id="firstName"
          type="text"
          value={firstName}
          onChange={e => setFirstName(e.target.value)}
          className={`mt-1 block w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground ${firstNameError ? 'border-red-600' : ''}`}
        />
        {firstNameError && <p className="text-red-600 text-sm mt-1">{firstNameError}</p>}
      </div>
      <div>
        <label htmlFor="lastName" className="block text-sm font-medium text-gray-700">Last Name</label>
        <input
          id="lastName"
          type="text"
          value={lastName}
          onChange={e => setLastName(e.target.value)}
          className={`mt-1 block w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground ${lastNameError ? 'border-red-600' : ''}`}
        />
        {lastNameError && <p className="text-red-600 text-sm mt-1">{lastNameError}</p>}
      </div>
      
      <div>
        <label htmlFor="studentEmail" className="block text-sm font-medium text-gray-700">Student Email</label>
        <input
          id="studentEmail"
          type="email"
          value={studentEmail}
          onChange={e => setStudentEmail(e.target.value)}
          onBlur={() => {
            const isValid = /^\S+@\S+\.\S+$/.test(studentEmail);
            setEmailError(isValid ? '' : 'Please enter a valid email address');
          }}
          className={`mt-1 block w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground ${emailError ? 'border-red-600' : ''}`}
        />
        {emailError && (
          <p className="text-red-600 text-sm mt-1">{emailError}</p>
        )}
      </div>

      <div>
        <label htmlFor="discipline" className="block text-sm font-medium text-gray-700">Discipline/Major</label>
        <select
          id="discipline"
          value={discipline}
          onChange={e => setDiscipline(e.target.value)}
          className="mt-1 block w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground"
        >
          <option value="">Select discipline</option>
          {disciplineOptions.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        {disciplineError && <p className="text-red-600 text-sm mt-1">{disciplineError}</p>}
      </div>

      <div>
        <label htmlFor="classNumber" className="block text-sm font-medium text-gray-700">Class Number (e.g., ARCH 4000 or N/A)</label>
        <input
          id="classNumber"
          type="text"
          value={classNumber}
          onChange={e => setClassNumber(e.target.value)}
          className={`mt-1 block w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground ${classNumberError ? 'border-red-600' : ''}`}
        />
        {classNumberError && <p className="text-red-600 text-sm mt-1">{classNumberError}</p>}
      </div>

      <div>
        <label htmlFor="printMethod" className="block text-sm font-medium text-gray-700">Print Method</label>
        <select
          id="printMethod"
          value={printMethod}
          onChange={e => setPrintMethod(e.target.value)}
          className={`mt-1 block w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground ${printMethodError ? 'border-red-600' : ''}`}
        >
          <option value="">Select print method</option>
          {printMethodOptions.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        {printMethod && (
          <p className="text-gray-500 text-sm mt-1">
            {printMethod === 'Filament'
              ? 'Good resolution, suitable for simpler models. Fast. Best For: Medium items. Cost: Least expensive.'
              : 'Super high resolution and detail. Slow. Best For: Small items. Cost: More expensive.'
            }
          </p>
        )}
        {printMethodError && <p className="text-red-600 text-sm mt-1">{printMethodError}</p>}
      </div>

      <div>
        <label htmlFor="color" className="block text-sm font-medium text-gray-700">Color Preference</label>
        <select
          id="color"
          value={color}
          onChange={e => setColor(e.target.value)}
          disabled={!printMethod}
          className={`mt-1 block w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground disabled:opacity-50 ${colorError ? 'border-red-600' : ''}`}
        >
          <option value="">Select color</option>
          {printMethod && colorOptions[printMethod].map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        {colorError && <p className="text-red-600 text-sm mt-1">{colorError}</p>}
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded p-4 text-sm text-gray-600 mb-6">
        <p className="font-medium mb-2">Will your model fit on our printers? Please check the dimensions (W × D × H):</p>
        <ul className="list-disc ml-5 space-y-1">
          <li>Filament:
            <ul className="list-disc ml-5">
              <li>Prusa MK4S: 9.84" × 8.3" × 8.6" (250 × 210 × 220 mm)</li>
              <li>Prusa XL: 14.17" × 14.17" × 14.17" (360 × 360 × 360 mm)</li>
              <li>Raise3D Pro 2 Plus: 12" × 12" × 23.8" (305 × 305 × 605 mm)</li>
            </ul>
          </li>
          <li>Resin:
            <ul className="list-disc ml-5">
              <li>Formlabs Form 3: 5.7" × 5.7" × 7.3" (145 × 145 × 175 mm)</li>
            </ul>
          </li>
        </ul>
        <p className="mt-2">
          Ensure your model's dimensions are within the specified limits for the printer you plan to use.
        </p>
        <div className="flex items-start mt-3" id="scalingConfirmed">
          <input
            id="scalingConfirmed"
            type="checkbox"
            checked={scalingConfirmed}
            onChange={e => setScalingConfirmed(e.target.checked)}
            className="h-4 w-4 text-blue-600 border-gray-300 rounded mt-0.5"
          />
          <label htmlFor="scalingConfirmed" className="ml-2 block text-sm text-gray-700">
            If exporting as .STL or .OBJ you MUST scale it down in millimeters BEFORE exporting. If you do not the scale will not work correctly. Have you done this?
          </label>
        </div>
        {scalingError && <p className="text-red-600 text-sm mt-1 ml-6">{scalingError}</p>}
        </div>
      <div>
        <label htmlFor="printer" className="block text-sm font-medium text-gray-700">Which printer do you think your model fits on?</label>
        <select
          id="printer"
          value={printer}
          onChange={e => setPrinter(e.target.value)}
          disabled={!printMethod}
          className={`mt-1 block w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground disabled:opacity-50 ${printerError ? 'border-red-600' : ''}`}
        >
          <option value="">Select printer</option>
          {availablePrinters.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
        {printerError && <p className="text-red-600 text-sm mt-1">{printerError}</p>}
      </div>

      <div className="flex items-center" id="minChargeConsent">
        <input
          id="minChargeConsent"
          type="checkbox"
          checked={minChargeConsent}
          onChange={e => setMinChargeConsent(e.target.checked)}
          className="h-4 w-4 text-blue-600 border-gray-300 rounded"
        />
        <label htmlFor="minChargeConsent" className="ml-2 block text-sm text-gray-700">
          I acknowledge the minimum $3.00 charge
        </label>
      </div>
      {minChargeError && <p className="text-red-600 text-sm mt-1 ml-6">{minChargeError}</p>}

      <div>
        <label htmlFor="file" className="block text-sm font-medium text-gray-700">Upload 3D Model File (.stl, .obj, .3mf)</label>
        <input
          id="file"
          type="file"
          accept=".stl,.obj,.3mf"
          onChange={handleFileChange}
          className="mt-1 block w-full border border-input p-2 rounded transition-all duration-200 focus-ring text-sm text-foreground"
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
        className="w-full flex items-center justify-center bg-primary text-primary-foreground px-4 py-3 rounded-lg btn-transition focus-ring disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSubmitting && <Loader2 className="animate-spin mr-2 h-4 w-4" />}
        {isSubmitting ? 'Submitting...' : 'Submit Print Job'}
      </button>
    </form>
  );
}