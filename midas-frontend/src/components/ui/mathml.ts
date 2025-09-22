// Heuristics shared by SmartMathRenderer and CanvasView

export const looksLikeHTML = (s: string) => /<[^>]+>/.test(s);

export const hasTeXDelimiters = (s: string) =>
  /^\s*(\$\$[\s\S]*\$\$|\$[\s\S]*\$|\\\[([\s\S]*)\\\]|\\\(([\s\S]*)\\\))\s*$/.test(s);

export const ensureDelimiters = (s: string) => {
  const t = (s ?? '').trim();
  if (!t) return t;
  if (hasTeXDelimiters(t)) return t;
  const display = t.includes('\n') || /\\begin|\\frac|=/.test(t);
  return display ? `$$ ${t} $$` : `\\(${t}\\)`;
};

// Replace <math>...</math> that aren't real MathML with TeX delimiters.
// Keep genuine MathML intact. Guard against SSR.
export function normalizeMathPlaceholders(html: string): string {
  if (!html || typeof window === 'undefined') return html;

  const parser = new DOMParser();
  const doc = parser.parseFromString(`<div id="__root">${html}</div>`, 'text/html');
  const root = doc.getElementById('__root') as HTMLElement;
  if (!root) return html;

  const MATHML_TAG_RE = /<(mi|mo|mn|mrow|msup|msub|mfrac|msqrt|mstyle|mtext|munderover|mover|munder|mtable|mtr|mtd)\b/i;

  for (const m of Array.from(root.querySelectorAll('math'))) {
    const inner = (m as HTMLElement).innerHTML.trim();
    const isRealMathML = MATHML_TAG_RE.test(inner);
    if (isRealMathML) continue;

    const tex = (m.textContent || '').trim();
    const displayAttr = (m.getAttribute('display') || '').toLowerCase();
    const display = displayAttr === 'block' || /\n/.test(tex) || /\\begin|\\frac|=/.test(tex);

    m.replaceWith(doc.createTextNode(display ? `$$ ${tex} $$` : `\\(${tex}\\)`));
  }
  return root.innerHTML;
}
