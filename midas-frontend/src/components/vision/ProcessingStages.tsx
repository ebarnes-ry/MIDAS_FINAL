import React from 'react';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export type ProcessingStage = 
  | 'uploading'
  | 'processing'
  | 'analyzing'
  | 'complete'
  | 'error';

interface ProcessingStagesProps {
  stage: ProcessingStage;
  error?: string | null;
}

export const ProcessingStages: React.FC<ProcessingStagesProps> = ({ 
  stage, 
  error 
}) => {
  const getStageMessage = (stage: ProcessingStage): string => {
    switch (stage) {
      case 'uploading':
        return 'Uploading document...';
      case 'processing':
        return 'Processing document with Marker...';
      case 'analyzing':
        return 'Analyzing content...';
      case 'complete':
        return 'Processing complete!';
      case 'error':
        return 'Error occurred during processing';
      default:
        return 'Loading...';
    }
  };

  if (stage === 'error') {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Processing Failed</h3>
        <p className="text-sm text-gray-600 text-center mb-4">
          {error || 'An error occurred while processing your document.'}
        </p>
      </div>
    );
  }

  if (stage === 'complete') {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Processing Complete!</h3>
        <p className="text-sm text-gray-600 text-center">
          Your document has been processed and is ready for analysis.
        </p>
      </div>
    );
  }

  return (
    <LoadingSpinner 
      message={getStageMessage(stage)}
      size="lg"
    />
  );
};
