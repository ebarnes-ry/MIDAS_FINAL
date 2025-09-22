import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '../ui/Button';

interface Props {
  children: ReactNode;
  componentName?: string;
  onRetry?: () => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class VisionErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`VisionErrorBoundary (${this.props.componentName || 'Unknown'}) caught an error:`, error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">
                {this.props.componentName ? `${this.props.componentName} Error` : 'Component Error'}
              </h3>
              <div className="mt-2 text-sm text-red-700">
                <p>This component failed to render properly.</p>
                {this.state.error && (
                  <details className="mt-2">
                    <summary className="cursor-pointer text-xs">Technical details</summary>
                    <pre className="mt-2 text-xs bg-red-100 p-2 rounded overflow-auto max-h-32">
                      {this.state.error.message}
                      {this.state.errorInfo && (
                        <>
                          {'\n\nComponent Stack:'}
                          {this.state.errorInfo.componentStack}
                        </>
                      )}
                    </pre>
                  </details>
                )}
              </div>
              {this.props.onRetry && (
                <div className="mt-3">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={this.handleRetry}
                  >
                    Try Again
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Specialized error boundaries for different vision components
export const MathErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => (
  <VisionErrorBoundary componentName="Math Renderer">
    {children}
  </VisionErrorBoundary>
);

export const ImageErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => (
  <VisionErrorBoundary componentName="Image Renderer">
    {children}
  </VisionErrorBoundary>
);

export const BlockErrorBoundary: React.FC<{ children: ReactNode; onRetry?: () => void }> = ({ children, onRetry }) => (
  <VisionErrorBoundary componentName="Block Component" onRetry={onRetry}>
    {children}
  </VisionErrorBoundary>
);