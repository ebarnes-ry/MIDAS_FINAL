import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { MathJaxContext } from 'better-react-mathjax';

const config = {
  loader: { load: ["input/tex", "input/mml", "output/chtml"] },
  tex: {
    inlineMath: [["$", "$"], ["\\(", "\\)"]],
    displayMath: [["$$", "$$"], ["\\[", "\\]"]],
  },
  svg: { fontCache: "global" }
};

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <MathJaxContext config={config}>
      <App />
    </MathJaxContext>
  </React.StrictMode>
);