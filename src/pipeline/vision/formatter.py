import re
from typing import List, Tuple, Dict, Any
from .types import Block, FormattedOutput, UIBlock, UIDocument
from bs4 import BeautifulSoup

class Formatter:
    @staticmethod
    def format_for_ui_interaction(marker_result) -> UIDocument:
        if marker_result is None:
            raise ValueError("Marker processing returned None")

        all_blocks = []
        if hasattr(marker_result, 'children'):
            for page_output in marker_result.children:
                if hasattr(page_output, 'children') and page_output.children:
                    for block_output in page_output.children:
                        ui_block = Formatter._create_ui_block_from_marker_output(block_output)
                        all_blocks.append(ui_block)

        # Sort blocks by reading order (top-to-bottom, left-to-right)
        sorted_blocks = sorted(all_blocks, key=lambda b: (b.bbox[1], b.bbox[0]))
        
        # === THIS IS THE NEW LOGIC ===
        merged_blocks = Formatter._merge_contiguous_blocks(sorted_blocks)

        editable_blocks = {b.id: b for b in merged_blocks if b.is_editable}
        
        return UIDocument(
            blocks=merged_blocks,
            spatial_map={b.id: b for b in merged_blocks},
            editable_blocks=editable_blocks,
            images=getattr(marker_result, 'images', {}),
            metadata=getattr(marker_result, 'metadata', {}),
            dimensions=Formatter._extract_dimensions(marker_result.children)
        )

    @staticmethod
    def _merge_contiguous_blocks(blocks: List[UIBlock]) -> List[UIBlock]:
        if not blocks:
            return []

        merged_blocks = []
        current_merged_block = blocks[0]

        MERGEABLE_TYPES = {'Text', 'Equation', 'TextInlineMath', 'ListItem'}
        VERTICAL_THRESHOLD = 20  # Max vertical pixels between blocks to merge

        for i in range(1, len(blocks)):
            prev_block = current_merged_block
            current_block = blocks[i]

            # Condition 1: Both blocks must be of a mergeable type
            are_types_mergeable = prev_block.block_type in MERGEABLE_TYPES and \
                                  current_block.block_type in MERGEABLE_TYPES

            # Condition 2: Blocks must be vertically close
            vertical_distance = current_block.bbox[1] - prev_block.bbox[3]
            are_vertically_close = 0 <= vertical_distance <= VERTICAL_THRESHOLD

            if are_types_mergeable and are_vertically_close:
                # Merge current_block into prev_block (current_merged_block)
                current_merged_block.html += f"\n{current_block.html}"
                if current_merged_block.latex_content and current_block.latex_content:
                    current_merged_block.latex_content += f"\n{current_block.latex_content}"
                
                # Update bbox to encompass both blocks
                new_bbox = [
                    min(prev_block.bbox[0], current_block.bbox[0]),
                    min(prev_block.bbox[1], current_block.bbox[1]),
                    max(prev_block.bbox[2], current_block.bbox[2]),
                    max(prev_block.bbox[3], current_block.bbox[3]),
                ]
                current_merged_block.bbox = new_bbox
            else:
                # Finish the current merge and start a new one
                merged_blocks.append(current_merged_block)
                current_merged_block = current_block
        
        # Add the last merged block
        merged_blocks.append(current_merged_block)
        return merged_blocks

    @staticmethod
    def _create_ui_block_from_marker_output(b) -> UIBlock:
        return UIBlock(
            id=str(b.id),
            block_type=str(b.block_type),
            html=getattr(b, 'html', ''),
            polygon=getattr(b, 'polygon', []),
            bbox=getattr(b, 'bbox', []),
            children=[],
            section_hierarchy=getattr(b, 'section_hierarchy', {}),
            images=getattr(b, 'images', {})
        )

    @staticmethod
    def _extract_dimensions(pages) -> Tuple[int, int]:
        if pages and hasattr(pages[0], 'bbox') and len(pages[0].bbox) >= 4:
            return (int(pages[0].bbox[2]), int(pages[0].bbox[3]))
        return (1000, 1200) # Default dimensions