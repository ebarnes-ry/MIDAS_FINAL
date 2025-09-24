import React from 'react';
import { ProcessingStage } from '../../types/api';

interface PipelineLoadingProps {
  stage: ProcessingStage;
  message?: string;
}

const stageMessages: Record<ProcessingStage, string> = {
  idle: 'Ready to start',
  uploading: 'Uploading document...',
  validating: 'Validating document...',
  processing: 'Processing document with Marker...',
  analyzing: 'Analyzing visual content...',
  thinking: 'AI is thinking about the problem...',
  solving: 'AI is solving the problem...',
  writing_code: 'Generating SymPy code...',
  complete: 'Processing complete!',
  error: 'An error occurred',
};

const stageIcons: Record<ProcessingStage, string> = {
  idle: '...',
  uploading: 'uploading',
  validating: 'validating',
  processing: 'processing',
  analyzing: 'looking',
  thinking: 'thinking',
  solving: 'solving',
  writing_code: 'coding',
  complete: 'Done!',
  error: 'yikes',
};

export const PipelineLoading: React.FC<PipelineLoadingProps> = ({ stage, message }) => {
  const displayMessage = message || stageMessages[stage];
  const icon = stageIcons[stage];

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center max-w-md mx-auto px-4">
        <div className="mb-8">
          <div className="text-6xl mb-4">{icon}</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {displayMessage}
          </h2>
          <p className="text-gray-600">
            {stage === 'thinking' && 'The AI is analyzing the problem and planning its approach...'}
            {stage === 'validating' && 'Checking if the document contains a mathematical problem...'}
            {stage === 'solving' && 'The AI is working through the mathematical solution step by step...'}
            {stage === 'writing_code' && 'The AI is converting the solution into executable SymPy code...'}
            {stage === 'processing' && 'Processing your document with advanced OCR and layout analysis...'}
            {stage === 'analyzing' && 'Analyzing visual elements and mathematical content...'}
            {stage === 'uploading' && 'Uploading and preparing your document for processing...'}
            {stage === 'complete' && 'All processing stages have been completed successfully!'}
            {stage === 'error' && 'Something went wrong during processing. Please try again.'}
          </p>
        </div>

        {/* Progress indicator */}
        <div className="mb-8">
          <div className="flex justify-center space-x-2 mb-4">
            {['uploading', 'processing', 'analyzing', 'thinking', 'solving', 'writing_code', 'complete'].map((stageName, index) => {
              const isActive = stage === stageName;
              const isCompleted = ['uploading', 'processing', 'analyzing', 'thinking', 'solving', 'writing_code', 'complete'].indexOf(stage) > index;
              
              return (
                <div
                  key={stageName}
                  className={`w-3 h-3 rounded-full transition-colors ${
                    isActive 
                      ? 'bg-blue-500 animate-pulse' 
                      : isCompleted 
                        ? 'bg-green-500' 
                        : 'bg-gray-300'
                  }`}
                />
              );
            })}
          </div>
          <div className="text-xs text-gray-500 space-y-1">
            <div className="flex justify-between">
              <span className={stage === 'uploading' ? 'text-blue-600 font-medium' : ''}>Upload</span>
              <span className={stage === 'processing' ? 'text-blue-600 font-medium' : ''}>Process</span>
              <span className={stage === 'analyzing' ? 'text-blue-600 font-medium' : ''}>Analyze</span>
              <span className={stage === 'thinking' ? 'text-blue-600 font-medium' : ''}>Think</span>
              <span className={stage === 'solving' ? 'text-blue-600 font-medium' : ''}>Solve</span>
              <span className={stage === 'writing_code' ? 'text-blue-600 font-medium' : ''}>Code</span>
              <span className={stage === 'complete' ? 'text-green-600 font-medium' : ''}>Done</span>
            </div>
          </div>
        </div>

        {/* Spinner for active stages */}
        {(stage === 'uploading' || stage === 'processing' || stage === 'analyzing' || 
          stage === 'thinking' || stage === 'solving' || stage === 'writing_code') && (
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>
    </div>
  );
};
