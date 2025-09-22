// // import React from 'react';
// // import { MathJax } from 'better-react-mathjax';
// // import { MathErrorBoundary } from '../vision/VisionErrorBoundary';

// // interface SmartMathRendererProps {
// //   content: string;
// // }

// // // const sanitizeContent = (html: string): string => {
// // //   // Marker sometimes wraps clean math in ugly <p> tags. This is a pragmatic way to clean it.
// // //   // It removes the outer <p ...> and </p> tags if the content is primarily a math block.
// // //   const trimmed = html.trim();
// // //   const match = trimmed.match(/^<p block-type=".*?">(.*)<\/p>$/s);
// // //   if (match) {
// // //     // If the inner content is just a math tag, return it directly.
// // //     const inner = match[1].trim();
// // //     if (inner.startsWith('<math')) {
// // //       return inner;
// // //     }
// // //   }
// // //   return html; // Return original if it doesn't match the pattern
// // // }

// // // const sanitiseContent = (html: string): string => {
// // //   const sanitised = html.trim()
// // //     .replaceAll(/<math\b[^>]*>/g, '$')
// // //     .replaceAll(/<\/math>/g, "$");
// // //   return sanitised;
// // // }

// // // export const SmartMathRenderer: React.FC<SmartMathRendererProps> = ({ content }) => {
// // //   // const cleanedContent = sanitizeContent(content);
// // //   const cleanedContent = sanitiseContent(content);

// // //   return (
// // //     <MathErrorBoundary>
// // //       <MathJax dynamic>
// // //         <div
// // //           className="prose prose-sm max-w-none"
// // //           // We still need dangerouslySetInnerHTML because the content is HTML
// // //           dangerouslySetInnerHTML={{ __html: cleanedContent }}
// // //         />
// // //       </MathJax>
// // //     </MathErrorBoundary>
// // //   );
// // // };

// import React, { useMemo } from 'react';
// import { MathJax } from 'better-react-mathjax';
// import { MathErrorBoundary } from '../vision/VisionErrorBoundary';
// import { looksLikeHTML, ensureDelimiters, normalizeMathPlaceholders } from './mathml';

// interface SmartMathRendererProps {
//   content: string;
// }

// export const SmartMathRenderer: React.FC<SmartMathRendererProps> = ({ content }) => {
//   const prepared = useMemo(() => {
//     if (!looksLikeHTML(content)) return ensureDelimiters(content);
//     return normalizeMathPlaceholders(content);
//   }, [content]);

//   return (
//     <MathErrorBoundary>
//       <MathJax dynamic>
//         {looksLikeHTML(content)
//           ? (
//             <div
//               className="prose prose-sm max-w-none"
//               dangerouslySetInnerHTML={{ __html: prepared }}
//             />
//           )
//           : (
//             <div className="prose prose-sm max-w-none">
//               {prepared}
//             </div>
//           )
//         }
//       </MathJax>
//     </MathErrorBoundary>
//   );
// };

import React from 'react';
import { MathJax } from 'better-react-mathjax';
import { MathErrorBoundary } from '../vision/VisionErrorBoundary';

interface SmartMathRendererProps {
  content: string;
}

const sanitizeContent = (html: string): string => {
  const sanitised = html.trim()
    .replaceAll(/<math\b[^>]*>/g, '$')
    .replaceAll(/<\/math>/g, "$");
  return sanitised;
}

export const SmartMathRenderer: React.FC<SmartMathRendererProps> = ({ content }) => {
  // const cleanedContent = sanitizeContent(content);
  const cleanedContent = sanitizeContent(content);

  return (
    <MathErrorBoundary>
      <MathJax dynamic>
        <div
          className="prose prose-sm max-w-none"
          // We still need dangerouslySetInnerHTML because the content is HTML
          dangerouslySetInnerHTML={{ __html: cleanedContent }}
        />
      </MathJax>
    </MathErrorBoundary>
  );
};
