import SubmissionForm from '../../components/submission/submission-form';
import { AlertTriangle } from 'lucide-react';

export default function SubmitPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-blue-50 to-white">
      <div className="max-w-2xl mx-auto px-4">
        <div className="bg-card p-8 rounded-xl shadow-md">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">3D Print Submission</h1>
          <p className="text-base text-foreground mb-6">
            Submit your 3D model for printing. Please ensure you've reviewed our guidelines before proceeding.
          </p>
          <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-lg p-4 mb-8">
            <div className="flex items-start">
              <AlertTriangle className="h-5 w-5 text-yellow-400 flex-shrink-0" />
              <p className="ml-3 text-sm text-yellow-700">
                Before submitting your model for 3D printing, please ensure you have thoroughly reviewed our Additive Manufacturing Moodle page, read all the guides, and checked the checklist. If necessary, revisit and fix your model before submission. Your model must be scaled and simplified appropriately, often requiring a second version specifically optimized for 3D printing. We will not print models that are broken, messy, or too large. Your model must follow the rules and constraints of the machine. We will not fix or scale your model as we do not know your specific needs or project requirements. We print exactly what you send us; if the scale is wrong or you are unsatisfied with the product, it is your responsibility. We will gladly print another model for you at an additional cost. We are only responsible for print failures due to issues under our control.
              </p>
            </div>
          </div>
          <SubmissionForm />
        </div>
      </div>
    </div>
  );
}