import React from 'react';
import { render, screen } from '@testing-library/react';
import SubmissionForm from './submission-form';

describe('SubmissionForm initial render', () => {
  beforeEach(() => {
    render(<SubmissionForm />);
  });

  it('renders Student Name input', () => {
    expect(screen.getByLabelText(/Student Name/i)).toBeInTheDocument();
    expect((screen.getByLabelText(/Student Name/i) as HTMLInputElement).value).toBe('');
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
    expect(screen.getByLabelText(/Printer Selection/i)).toBeInTheDocument();
  });

  it('renders Minimum Charge Consent checkbox unchecked', () => {
    const checkbox = screen.getByLabelText(/I acknowledge the minimum/i) as HTMLInputElement;
    expect(checkbox).toBeInTheDocument();
    expect(checkbox.checked).toBe(false);
  });

  it('renders File Upload input', () => {
    expect(screen.getByLabelText(/File Upload/i)).toBeInTheDocument();
  });
});