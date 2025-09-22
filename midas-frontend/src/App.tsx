import React from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { FullVisionPipeline } from './components/vision/FullVisionPipeline';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <div className="main-window">
        <FullVisionPipeline />
      </div>
    </ErrorBoundary>
  );
}

export default App;