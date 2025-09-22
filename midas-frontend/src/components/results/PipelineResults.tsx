import React, { useState, useMemo } from 'react';
import { CompletePipelineResponse, ReasoningExplainRequest } from '../../types/api';
import { SmartMathRenderer } from '../ui/SmartMathRenderer';
import { SimpleAPIService } from '../../services/SimpleAPIService';
import { LoadingSpinner } from '../ui/LoadingSpinner';

// Simple Modal Component
const ExplanationModal: React.FC<{ content: string; isLoading: boolean; onClose: () => void }> = ({ content, isLoading, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
        <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold mb-4">Step Explanation</h3>
            <div className="prose prose-sm max-w-none border-t pt-4 min-h-[100px]">
                {isLoading ? <LoadingSpinner message="Generating explanation..."/> : <SmartMathRenderer content={content} />}
            </div>
            <button onClick={onClose} className="mt-4 bg-gray-200 px-4 py-2 rounded text-sm font-semibold">Close</button>
        </div>
    </div>
);

export const PipelineResults: React.FC<{ result: CompletePipelineResponse; onStartOver: () => void }> = ({ result, onStartOver }) => {
    const [expandedSections, setExpandedSections] = useState({ thinking: false, solution: true, code: true, errors: true });
    const [explanation, setExplanation] = useState<string | null>(null);
    const [isLoadingExplanation, setIsLoadingExplanation] = useState(false);

    const toggleSection = (section: keyof typeof expandedSections) => setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));

    const solutionSteps = useMemo(() => {
        if (!result.data?.reasoning.worked_solution) return [];
        return result.data.reasoning.worked_solution.split(/(?=\d+\.\s*)/).filter(s => s.trim());
    }, [result.data?.reasoning.worked_solution]);

    const handleStepClick = async (stepText: string) => {
        if (!result.data) return;
        setIsLoadingExplanation(true);
        setExplanation(''); // Show modal immediately with loading state
        try {
            const request: ReasoningExplainRequest = {
                problem_statement: result.data.vision.problem_statement,
                worked_solution: result.data.reasoning.worked_solution,
                step_text: stepText,
            };
            const response = await SimpleAPIService.explainStep(request);
            if (response.success && response.data) {
                setExplanation(response.data.explanation);
            } else {
                 setExplanation("Error: Could not generate an explanation.");
            }
        } catch (error) {
            console.error("Failed to get explanation", error);
            setExplanation("Sorry, an error occurred while generating the explanation for this step.");
        } finally {
            setIsLoadingExplanation(false);
        }
    };

    if (!result.data) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center p-8">
                    <div className="text-red-500 text-xl mb-4">❌ Pipeline Failed</div>
                    <p className="text-gray-600 mb-4 bg-red-100 p-4 rounded-lg">{result.message}</p>
                    <button onClick={onStartOver} className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600">Start Over</button>
                </div>
            </div>
        );
    }

    const { vision, reasoning, verification, total_processing_time } = result.data;
    const getStatusPill = (status: string) => {
        const base = "text-sm font-bold px-3 py-1 rounded-full text-white";
        const colors: Record<string, string> = {
            verified: "bg-green-600",
            failed_reasoning: "bg-orange-600",
            failed_codegen: "bg-red-600",
            failed_pipeline: "bg-red-800",
            partial: "bg-yellow-500",
            timeout: "bg-purple-600",
        };
        return `${base} ${colors[status.toLowerCase()] || 'bg-gray-500'}`;
    };

    return (
        <>
            {(isLoadingExplanation || explanation) && 
                <ExplanationModal 
                    content={explanation || ""} 
                    isLoading={isLoadingExplanation}
                    onClose={() => setExplanation(null)} 
                />
            }
            
            <div className="min-h-screen bg-gray-50">
                <div className="bg-white shadow-sm border-b">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold">Pipeline Results</h1>
                            <p className="text-sm text-gray-500 mt-1">Completed in {total_processing_time.toFixed(2)}s</p>
                        </div>
                        <button onClick={onStartOver} className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600">Start Over</button>
                    </div>
                </div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="space-y-6">
                        <div className="bg-white rounded-lg shadow-sm border p-6">
                            <h2 className="text-lg font-semibold mb-3">Problem Statement</h2>
                            <div className="p-4 bg-gray-50 rounded-md"><SmartMathRenderer content={vision.problem_statement} /></div>
                        </div>
                        <div className="bg-white rounded-lg shadow-sm border">
                            <button onClick={() => toggleSection('thinking')} className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50">
                                <h2 className="text-lg font-semibold">AI Thinking Process</h2>
                                <span className={`transform transition-transform ${expandedSections.thinking ? 'rotate-180' : ''}`}>▼</span>
                            </button>
                            {expandedSections.thinking && <div className="px-6 pb-6 border-t"><pre className="whitespace-pre-wrap text-sm font-mono bg-gray-50 p-4 rounded-md mt-4">{reasoning.think_reasoning}</pre></div>}
                        </div>
                        <div className="bg-white rounded-lg shadow-sm border">
                            <button onClick={() => toggleSection('solution')} className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50">
                                <h2 className="text-lg font-semibold">Worked Solution (Click a step for details)</h2>
                                <span className={`transform transition-transform ${expandedSections.solution ? 'rotate-180' : ''}`}>▼</span>
                            </button>
                            {expandedSections.solution && (
                                <div className="px-6 pb-6 border-t">
                                    <div className="p-4 bg-gray-50 rounded-md mt-4 space-y-4">
                                        {solutionSteps.map((step, index) => (
                                            <div key={index} onClick={() => handleStepClick(step)} className="cursor-pointer hover:bg-gray-200 p-2 rounded"><SmartMathRenderer content={step} /></div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                            <h2 className="text-lg font-semibold text-green-900 mb-3">Final Answer</h2>
                            <div className="text-xl font-mono text-green-800 bg-green-100 rounded-lg p-4 text-center"><SmartMathRenderer content={reasoning.final_answer} /></div>
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div className="bg-white rounded-lg shadow-sm border-2 border-black p-6">
                            <h2 className="text-lg font-bold text-black mb-4">Verification Status</h2>
                            <div className="flex items-center justify-between mb-4">
                                <span className="text-base font-bold">Outcome:</span>
                                <span className={getStatusPill(verification.status)}>{verification.status.toUpperCase()}</span>
                            </div>
                            <div className="flex items-center justify-between mb-4">
                                <span className="text-base font-bold">Confidence:</span>
                                <span className="text-lg font-mono font-bold">{(verification.confidence_score * 100).toFixed(1)}%</span>
                            </div>
                            {verification.answer_match !== null && (
                                <div className="flex items-center justify-between mb-4">
                                    <span className="text-base font-bold">Answer Match:</span>
                                    <span className={`text-sm font-bold px-2 py-1 rounded ${verification.answer_match ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                        {verification.answer_match ? '✓ Match' : '✗ Mismatch'}
                                    </span>
                                </div>
                            )}

                            {verification.repair_history && verification.repair_history.length > 0 && (
                                <div className="mt-4 border-t-2 border-blue-200 pt-4">
                                    <h3 className="text-sm font-bold text-blue-800 mb-2">
                                        Repair Attempts ({verification.repair_history.length})
                                    </h3>
                                    <div className="space-y-2">
                                        {verification.repair_history.map((repair, index) => (
                                            <div key={index} className={`p-3 rounded-md border text-xs ${repair.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                                                <div className="flex justify-between items-center mb-1">
                                                    <span className="font-bold">{repair.type} repair #{repair.attempt}</span>
                                                    <span className={`px-2 py-1 rounded text-xs font-bold ${repair.success ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}>
                                                        {repair.success ? 'Success' : 'Failed'}
                                                    </span>
                                                </div>
                                                <p className="text-gray-700 mb-1">{repair.reason}</p>
                                                {repair.error_message && (
                                                    <p className="text-red-600 font-mono text-xs">{repair.error_message}</p>
                                                )}
                                                <p className="text-gray-500 text-xs">Time: {repair.processing_time.toFixed(2)}s</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {verification.errors && verification.errors.length > 0 && (
                                <div className="mt-4 border-t-2 border-black pt-4">
                                    <button onClick={() => toggleSection('errors')} className="w-full text-left flex items-center justify-between">
                                        <h3 className="text-sm font-bold text-red-600">Detected Errors ({verification.errors.length})</h3>
                                        <span className={`transform transition-transform ${expandedSections.errors ? 'rotate-180' : ''}`}>▼</span>
                                    </button>
                                    {expandedSections.errors && (
                                        <div className="mt-2 space-y-2">
                                            {verification.errors.map((err, index) => (
                                                <div key={index} className="bg-red-50 p-3 rounded-md border border-red-200">
                                                    <p className="text-xs font-bold text-red-800">{err.error_type}</p>
                                                    <p className="text-xs text-red-700 mt-1 font-mono">{err.message}</p>
                                                    {err.suggested_fix && (
                                                        <p className="text-xs text-blue-700 mt-1 italic">Suggestion: {err.suggested_fix}</p>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                        <div className="bg-white rounded-lg shadow-sm border">
                            <button onClick={() => toggleSection('code')} className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-gray-50">
                                <h2 className="text-lg font-semibold">Generated Verification Code</h2>
                                <span className={`transform transition-transform ${expandedSections.code ? 'rotate-180' : ''}`}>▼</span>
                            </button>
                            {expandedSections.code && <div className="px-6 pb-6 border-t"><div className="bg-gray-900 rounded-lg p-4 overflow-x-auto mt-4"><pre className="text-sm text-green-400 font-mono"><code>{verification.generated_code}</code></pre></div></div>}
                        </div>
                        <div className="bg-white rounded-lg shadow-sm border p-6">
                            <h2 className="text-lg font-semibold mb-4">Processing Details</h2>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between"><span>Vision Analysis:</span><span className="font-mono">{vision.processing_time.toFixed(2)}s</span></div>
                                <div className="flex justify-between"><span>Reasoning:</span><span className="font-mono">{reasoning.processing_time.toFixed(2)}s</span></div>
                                <div className="flex justify-between"><span>Verification:</span><span className="font-mono">{verification.processing_time.toFixed(2)}s</span></div>
                                {verification.repair_history.length > 0 && (
                                    <div className="pl-4 border-l-2 border-blue-200 space-y-1">
                                        <div className="flex justify-between text-xs text-blue-700">
                                            <span>• Reasoning Repairs:</span><span className="font-mono">{verification.metadata.reasoning_repair_attempts}</span>
                                        </div>
                                        <div className="flex justify-between text-xs text-blue-700">
                                            <span>• Codegen Repairs:</span><span className="font-mono">{verification.metadata.codegen_repair_attempts}</span>
                                        </div>
                                    </div>
                                )}
                                <div className="border-t pt-3 flex justify-between font-semibold"><span>Total Time:</span><span className="font-mono text-blue-600">{total_processing_time.toFixed(2)}s</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};