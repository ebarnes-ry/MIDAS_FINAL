import React, { useEffect } from 'react';
import { APIProblem } from '../../types/api'; // <-- Changed import
import { Button } from '../ui/Button';
import { SmartMathRenderer } from '../ui/SmartMathRenderer';

interface SelectionPanelProps {
  // === CHANGED: We now receive the selected problem object ===
  selectedProblem: APIProblem | null;
  editedLatex: string;
  onLatexChange: (latex: string) => void;
  onSubmit: () => void;
  onClearSelection: () => void;
  isLoading?: boolean;
  error?: string | null;
}

export const SelectionPanel: React.FC<SelectionPanelProps> = ({
  selectedProblem,
  editedLatex,
  onLatexChange,
  onSubmit,
  onClearSelection,
  isLoading = false,
  error
}) => {

  // Automatically update the editor when the selected problem changes
  // useEffect(() => {
  //   if (selectedProblem) {
  //     onLatexChange(selectedProblem.combined_text);
  //   }
  // }, [selectedProblem, onLatexChange]);

  useEffect(() => {
    if (selectedProblem) {
      // === THE ONLY CHANGE IS HERE ===
      onLatexChange(selectedProblem.problem_text);
    }
  }, [selectedProblem, onLatexChange]);


  if (!selectedProblem) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="text-center text-gray-500">
          <h3 className="text-sm font-medium text-gray-900 mb-1">No Problem Selected</h3>
          <p className="text-xs text-gray-600">
            Click on a problem in the document to begin.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="flex-1 overflow-auto p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-black">Selected Problem ({selectedProblem.problem_id})</h3>
          <Button variant="secondary" size="sm" onClick={onClearSelection}>Clear</Button>
        </div>

        <div>
          <h3 className="text-sm font-bold text-black mb-2">Problem Statement LaTeX</h3>
          <textarea
            value={editedLatex}
            onChange={(e) => onLatexChange(e.target.value)}
            className="w-full h-40 p-2 border-2 border-black rounded-lg text-sm font-mono resize-y focus:outline-none bg-white text-black"
            placeholder="Combined LaTeX of the selected problem..."
            disabled={isLoading}
          />
        </div>

        {editedLatex.trim() && (
            <div>
                <h3 className="text-sm font-bold text-black mb-2">Live Preview</h3>
                <div className="p-4 border-2 border-dashed border-black rounded-lg bg-white min-h-[50px]">
                    <SmartMathRenderer content={editedLatex} />
                </div>
            </div>
        )}
      </div>

      <div className="p-4 border-t-2 border-black bg-gray-100 space-y-2">
        {error && (
          <div className="bg-red-100 border-2 border-red-600 rounded-lg p-3">
            <p className="text-sm text-red-800 font-bold">{error}</p>
          </div>
        )}

        <Button
          variant="primary"
          onClick={onSubmit}
          disabled={!editedLatex.trim() || isLoading}
          loading={isLoading}
          className="w-full"
        >
          {isLoading ? 'Processing...' : 'Run Full Pipeline'}
        </Button>
      </div>
    </div>
  );
};