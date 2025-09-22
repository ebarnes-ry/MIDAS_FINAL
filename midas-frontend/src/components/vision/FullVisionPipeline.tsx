// midas-frontend/src/components/vision/FullVisionPipeline.tsx

import React from 'react';
import { FileUpload } from './FileUpload';
import { DocumentRenderer } from './DocumentRenderer';
import { SelectionPanel } from './SelectionPanel';
import { DocumentPreview } from './DocumentPreview';
import { Button } from '../ui/Button';
import { useDocumentState } from '../../hooks/useDocumentState';
import { SimpleAPIService } from '../../services/SimpleAPIService';
import { PipelineResults } from '../results/PipelineResults';
import { PipelineLoading } from '../ui/PipelineLoading';


/**
 * Linus's Note: This component was a "God Component". It did everything.
 * Now it's dumb. Its only job is to read the state from the `useDocumentState`
 * hook and render the correct child component. All the complex logic for
 * handling file uploads, API calls, and state transitions has been moved
 * into the hook itself. This is a much cleaner separation of concerns.
 */
export const FullVisionPipeline: React.FC = () => {
  const {
    document,
    originalImageBase64,
    uploadedFile,
    selectedProblem,
    selectedProblemId,
    selectedBlockIds,
    editedLatex,
    isLoading,
    error,
    processingStage,
    completePipelineResult,
    actions, // The new actions object from the hook
  } = useDocumentState();

  // This is a simple diagnostic tool, leave it for debugging.
  const handleHealthCheck = async () => {
    try {
        await SimpleAPIService.healthCheck();
        alert('SUCCESS: Frontend can communicate with the backend.');
    } catch (err) {
        alert('FAILURE: Frontend cannot communicate with the backend. See console for details.');
        console.error("Health check FAILED:", err);
    }
  };

  // --- RENDER LOGIC ---
  // This is a simple state machine for the UI. It's fine for it to be here.
  
  // State 1: Nothing has happened yet
  if (processingStage === 'idle') {
    return (
        <div>
            <FileUpload onFileSelect={actions.handleFileUpload} error={error} />
            <div className="text-center -mt-4">
                <p className="text-xs text-gray-500 mb-2">If uploads fail, test the server connection:</p>
                <Button variant="danger" size="sm" onClick={handleHealthCheck}>
                    Run Backend Connection Test
                </Button>
            </div>
        </div>
    );
  }

  // State 2: User has selected a file, showing preview
  if (processingStage === 'uploading' && uploadedFile && originalImageBase64) {
    return (
      <DocumentPreview
        imageBase64={originalImageBase64}
        fileName={uploadedFile.name}
        onProcess={actions.processUploadedFile}
        onCancel={actions.cancelUpload}
        isProcessing={isLoading}
      />
    );
  }
  
  // State 3: An error occurred that halts the pipeline
  if (processingStage === 'error') {
      return (
          <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-6">
              <div className="max-w-md w-full bg-white shadow-lg rounded-lg border-2 border-red-300 p-6">
                <h2 className="text-lg font-bold text-red-700 mb-2">An Error Occurred</h2>
                <p className="text-red-600 font-mono bg-red-50 p-3 rounded-md">{error}</p>
                <div className="mt-4 text-center">
                    <Button onClick={actions.startOver}>Try Again</Button>
                </div>
              </div>
          </div>
      );
  }

  // State 4: Any long-running process is happening
  if (isLoading && ['validating', 'processing', 'analyzing', 'thinking', 'solving', 'writing_code'].includes(processingStage)) {
      return <PipelineLoading stage={processingStage} />;
  }
  
  // State 5: The final results page is being displayed
  if (processingStage === 'complete' && completePipelineResult) {
    return <PipelineResults result={completePipelineResult} onStartOver={actions.startOver} />;
  }

  // State 6: The document is processed, waiting for user interaction
  if (processingStage === 'complete' && document) {
    return (
      <div className="flex h-screen bg-gray-100">
        <div className="flex-1 min-w-0">
          <DocumentRenderer
            document={document}
            selectedBlockIds={selectedBlockIds}
            onProblemSelect={actions.selectProblem}
          />
        </div>
        <div className="w-96 bg-white border-l-2 border-black flex flex-col">
          <SelectionPanel
            selectedProblem={selectedProblem}
            editedLatex={editedLatex}
            onLatexChange={actions.updateEditedLatex}
            onSubmit={actions.runCompletePipeline}
            onClearSelection={actions.clearSelection}
            isLoading={isLoading}
            error={error}
          />
        </div>
      </div>
    );
  }

  // Fallback state
  return <FileUpload onFileSelect={actions.handleFileUpload} error={"An unexpected state occurred. Please start over."} />;
};