import React from 'react';
import { render, screen } from '@testing-library/react';
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), prefetch: jest.fn() })
}));
import SubmissionForm from './submission-form';

describe('SubmissionForm initial render', () => {
  beforeEach(() => {
    render(<SubmissionForm />);
  });

  it('renders First/Last Name inputs', () => {
    expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument();
    expect((screen.getByLabelText(/First Name/i) as HTMLInputElement).value).toBe('');
    expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument();
  });

  it('renders Student Email input', () => {
    expect(screen.getByLabelText(/Student Email/i)).toBeInTheDocument();
    expect((screen.getByLabelText(/Student Email/i) as HTMLInputElement).value).toBe('');
  });

  it('renders Discipline dropdown', () => {
    expect(screen.getByLabelText(/Discipline/i)).toBeInTheDocument();
  });

  it('renders Class Number input', () => {
    expect(screen.getByLabelText(/Class Number/i)).toBeInTheDocument();
  });

  it('renders Print Method dropdown', () => {
    expect(screen.getByLabelText(/Print Method/i)).toBeInTheDocument();
  });

  it('renders Color Preference dropdown disabled initially', () => {
    const colorSelect = screen.getByLabelText(/Color Preference/i) as HTMLSelectElement;
    expect(colorSelect).toBeInTheDocument();
    expect(colorSelect).toBeDisabled();
  });

  it('renders Printer Selection dropdown', () => {
    expect(screen.getByLabelText(/Which printer/i)).toBeInTheDocument();
  });

  it('renders Minimum Charge Consent checkbox unchecked', () => {
    const checkbox = screen.getByLabelText(/minimum \$3\.00 charge/i) as HTMLInputElement;
    expect(checkbox).toBeInTheDocument();
    expect(checkbox.checked).toBe(false);
  });

  it('renders File Upload input', () => {
    expect(screen.getByLabelText(/Upload 3D Model File/i)).toBeInTheDocument();
  });
});