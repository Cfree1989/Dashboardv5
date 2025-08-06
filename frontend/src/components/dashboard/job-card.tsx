"use client";
import React from 'react';

interface Job {
  id: string;
  display_name?: string;
}

export default function JobCard({ job }: { job: Job }) {
  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">{job.display_name || job.id}</h2>
    </div>
  );
}