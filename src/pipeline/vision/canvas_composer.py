# src/pipeline/vision/canvas_composer.py
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re

@dataclass
class CanvasSegment:
    block_id: str
    block_type: str
    tex: Optional[str] = None   # present for math
    html: Optional[str] = None  # present for prose (with inline math)
    display: Optional[bool] = None

@dataclass
class CanvasFigure:
    block_id: str
    image_b64: Optional[str]
    description: Optional[str]

@dataclass
class CanvasProblem:
    problem_id: str
    segments: List[CanvasSegment]
    composed_tex: str
    figures: List[CanvasFigure]

_TEX_LIKE = re.compile(r"""\\(begin|frac|int|sum|lim|mathbb|to|rightarrow|left|right|\(|\[)""")
_TEX_DELIMS = re.compile(r"(\$\$[\s\S]*\$\$|\\\[[\s\S]*\\\]|\\\([\s\S]*\\\))", re.M | re.S)

def _text_from_html(html: str) -> str:
    if not html: return ""
    soup = BeautifulSoup(html, "html.parser")
    return (soup.get_text() or "").strip()

def _has_image(images: Any) -> bool:
    if not images: return False
    if isinstance(images, dict):
        return any(bool(v) for v in images.values())
    return False

def _looks_like_tex(s: str) -> bool:
    return bool(s and _TEX_LIKE.search(s))

def _html_has_math(html: str) -> bool:
    return bool(html and ("<math" in html.lower() or _TEX_DELIMS.search(html)))

def compose_canvas(ui_document, problems: Optional[List[Any]] = None) -> Dict[str, Any]:
    blocks_by_id = {b.id: b for b in ui_document.blocks}
    source_problems = problems if problems is not None else getattr(ui_document, "problems", [])

    out: List[CanvasProblem] = []

    for p in source_problems:
        segs: List[CanvasSegment] = []
        figs: List[CanvasFigure] = []

        for bid in getattr(p, "block_ids", []):
            b = blocks_by_id.get(bid)
            if not b: continue

            bt = (b.block_type or "").lower()
            html = getattr(b, "html", "") or ""
            latex = (getattr(b, "latex_content", None) or "").strip()
            images = getattr(b, "images", {}) or {}
            desc   = getattr(b, "image_description", None)

            # A. True figures: has an image OR a relabeler description
            if bt in {"figure","picture","diagram","table"} and (_has_image(images) or desc):
                figs.append(CanvasFigure(
                    block_id=b.id,
                    image_b64=images.get("cropped") if isinstance(images, dict) else None,
                    description=desc
                ))
                # If this same block ALSO contains TeX, include it as math too (some PDFs label equations as figures)
                if not _has_image(images) and (latex and _looks_like_tex(latex)):
                    segs.append(CanvasSegment(
                        block_id=b.id, block_type="equation",
                        tex=latex,
                        display=("\n" in latex) or ("\\begin" in latex) or ("=" in latex)
                    ))
                continue

            # B. Math blocks: explicit math OR figure-without-image-but-contains-math
            is_explicit_math = bt in {"equation","inlinemath"}
            is_figure_math   = bt in {"figure","picture","diagram","table"} and not _has_image(images) and (_looks_like_tex(latex) or _html_has_math(html))

            if is_explicit_math or is_figure_math:
                if not latex:  # fallback to text extraction if relabeler only wrote it into HTML
                    latex = _text_from_html(html)
                segs.append(CanvasSegment(
                    block_id=b.id,
                    block_type="equation" if bt != "inlinemath" else "inlinemath",
                    tex=latex,
                    display=(bt != "inlinemath") or ("\n" in latex) or ("\\begin" in latex) or ("=" in latex)
                ))
                continue

            # C. Prose: carry HTML so inline <math> remains; DO NOT convert to TeX
            if bt in {"text","sectionheader","caption","listitem","reference"}:
                segs.append(CanvasSegment(block_id=b.id, block_type=bt, html=html))
                continue

            # D. Fallback: salvage something readable
            content = html or latex or _text_from_html(html)
            if content:
                # Prefer HTML if present; Canvas will normalize fake <math> tags
                segs.append(CanvasSegment(block_id=b.id, block_type=bt, html=html or None, tex=None))

        # Only TeX segments go into composed_tex (what you submit to the next step)
        composed = "\n\n".join(s.tex for s in segs if s.tex)
        out.append(CanvasProblem(problem_id=p.problem_id, segments=segs, composed_tex=composed, figures=figs))

    return {"problems": [asdict(cp) for cp in out]}
