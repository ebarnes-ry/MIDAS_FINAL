import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import clsx from 'clsx';
import { Button } from '../ui/Button';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isLoading?: boolean;
  error?: string | null;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  isLoading = false,
  error
}) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
      'application/pdf': ['.pdf']
    },
    multiple: false,
    disabled: isLoading,
  });

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-black mb-4">
          MIDAS Vision Pipeline
        </h1>
        <p className="text-lg text-black font-bold">
          Upload a document or image to begin mathematical content analysis
        </p>
      </div>

      <div
        {...getRootProps()}
        className={clsx(
          'border-4 border-dashed border-black rounded-lg p-12 text-center cursor-pointer transition-all duration-200 bg-white',
          isDragActive && !isDragReject && 'border-black bg-gray-100',
          isDragReject && 'border-red-600 bg-red-100',
          !isDragActive && !isDragReject && 'border-black hover:bg-gray-50',
          isLoading && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          {isLoading ? (
            <>
              <div className="flex justify-center">
                <svg
                  className="animate-spin h-12 w-12 text-blue-600"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
              </div>
              <p className="text-lg font-bold text-black">Processing document...</p>
              <p className="text-sm text-black font-bold">
                Running OCR and layout detection with Marker
              </p>
            </>
          ) : (
            <>
              <div className="flex justify-center">
                <svg
                  className="h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              
              {isDragActive && !isDragReject ? (
                <p className="text-lg font-bold text-black">
                  Drop the file here...
                </p>
              ) : isDragReject ? (
                <p className="text-lg font-bold text-red-600">
                  Please upload a PDF or image file
                </p>
              ) : (
                <>
                  <p className="text-lg font-bold text-black">
                    Drop files here, or click to select
                  </p>
                  <p className="text-sm text-black font-bold">
                    Supports PDF, PNG, JPG, JPEG, GIF, and WebP files
                  </p>
                </>
              )}
              
              <Button variant="primary" size="lg" className="mt-4">
                Choose File
              </Button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-6 p-4 bg-red-100 border-2 border-red-600 rounded-lg">
          <div className="flex">
            <svg
              className="h-5 w-5 text-red-600 mt-0.5 mr-3"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h3 className="text-sm font-bold text-red-800">Upload Error</h3>
              <p className="text-sm text-red-800 mt-1 font-bold">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};