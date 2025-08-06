import SubmissionForm from '../../components/submission/submission-form';

export default function SubmitPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-2xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-8">3D Print Submission</h1>
          <SubmissionForm />
        </div>
      </div>
    </div>
  );
}