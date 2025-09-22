import React, { useMemo } from 'react';
import clsx from 'clsx';
import { APIDocument, APIBlock, APIProblem } from '../../types/api';
import { SmartMathRenderer } from '../ui/SmartMathRenderer';
import { BlockErrorBoundary } from './VisionErrorBoundary';

interface BlockComponentProps {
  block: APIBlock;
  isSelected: boolean;
  onSelect: () => void;
}

const BlockComponent: React.FC<{ block: APIBlock; isSelected: boolean; onSelect: () => void }> = React.memo(({ block, isSelected, onSelect }) => {
  const isPureMathBlock = block.block_type === 'Equation' || block.block_type === 'InlineMath';
  // const contentToRender = isPureMathBlock && block.latex_content ? block.latex_content : block.html;
  const contentToRender = block.html;

  // if (block.block_type == "Equation")
    // console.log(block.latex_content);
    console.log(block.html);

  return (
    <div
      onClick={onSelect}
      className={clsx(
        'relative cursor-pointer transition-all duration-200 ease-in-out',
        'border-2 border-black rounded-lg p-4 mb-4 bg-white',
        {
          'bg-blue-50 border-blue-500 ring-2 ring-blue-500': isSelected,
          'hover:bg-gray-50': !isSelected,
        }
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-black uppercase tracking-wide border border-black px-2 py-0.5 rounded">
          {block.block_type}
        </span>
        {block.is_editable && (
          <span className="text-xs bg-gray-200 text-gray-800 px-2 py-0.5 rounded font-bold">
            EDITABLE
          </span>
        )}
      </div>
      
      {block.cropped_image ? (
        <div>
          <img src={`data:image/png;base64,${block.cropped_image}`} alt={block.block_type} className="max-w-full h-auto rounded border" />
          {block.image_description && <p className="text-xs text-gray-600 mt-2 italic">{block.image_description}</p>}
        </div>
      ) : (
        <SmartMathRenderer content={contentToRender} />
      )}
    </div>
  );
});

export const DocumentRenderer: React.FC<{
  document: APIDocument;
  selectedBlockIds: string[];
  onProblemSelect: (problemId: string) => void;
}> = ({ document, selectedBlockIds, onProblemSelect }) => {

  const blockToProblemMap = useMemo(() => {
    const map = new Map<string, string>();
    document.problems.forEach(problem => {
      problem.block_ids.forEach(blockId => {
        map.set(blockId, problem.problem_id);
      });
    });
    return map;
  }, [document.problems]);

  const displayableBlocks = [...document.blocks]
    .filter(block => block.block_type !== 'Page')
    .sort((a, b) => a.bbox[1] - b.bbox[1]);

  return (
    <div className="h-full overflow-y-auto bg-gray-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-black">Document Content</h1>
            <p className="text-sm text-gray-600">
              {document.problems.length > 0
                ? `Found ${document.problems.length} problems. Click a problem to select it.`
                : "No mathematical problems were identified in this document."}
            </p>
        </div>
        {displayableBlocks.map((block) => {
          const problemId = blockToProblemMap.get(block.id);
          console.log(block);
          return (
            <BlockErrorBoundary key={block.id}>
              <BlockComponent
                block={block}
                isSelected={selectedBlockIds.includes(block.id)}
                onSelect={() => {
                  if (problemId) {
                    onProblemSelect(problemId);
                  }
                }}
              />
            </BlockErrorBoundary>
          );
        })}
      </div>
    </div>
  );
};