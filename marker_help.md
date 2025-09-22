# Marker CLI Configuration Reference

Complete reference of all Marker CLI options and their descriptions.

## Basic Options

| Option | Description |
|--------|-------------|
| `--chunk_idx INTEGER` | Chunk index to convert |
| `--num_chunks INTEGER` | Number of chunks being processed in parallel |
| `--max_files INTEGER` | Maximum number of pdfs to convert |
| `--skip_existing` | Skip existing converted files |
| `--debug_print` | Print debug information |
| `--max_tasks_per_worker INTEGER` | Maximum number of tasks per worker process before recycling |
| `--workers INTEGER` | Number of worker processes to use. Set automatically by default, but can be overridden |
| `--llm_service TEXT` | LLM service to use - should be full import path, like `marker.services.gemini.GoogleGeminiService` |
| `--converter_cls TEXT` | Converter class to use. Defaults to PDF converter |
| `--page_range TEXT` | Page range to convert, specify comma separated page numbers or ranges. Example: `0,5-10,20` |
| `--disable_image_extraction` | Disable image extraction |
| `--disable_multiprocessing` | Disable multiprocessing |
| `--config_json TEXT` | Path to JSON file with additional configuration |
| `--processors TEXT` | Comma separated list of processors to use. Must use full module path |
| `--output_format [markdown\|json\|html\|chunks]` | Format to output results in |
| `-d, --debug` | Enable debug mode |
| `--output_dir PATH` | Directory to save output |

## Document Builder Options

| Option | Description |
|--------|-------------|
| `--lowres_image_dpi INTEGER` | DPI setting for low-resolution page images used for Layout and Line Detection. Default is 96 |
| `--highres_image_dpi INTEGER` | DPI setting for high-resolution page images used for OCR. Default is 192 |
| `--disable_ocr` | Disable OCR processing. Default is False |

## Layout Builder Options

| Option | Description |
|--------|-------------|
| `--layout_batch_size INTEGER` | The batch size to use for the layout model. Default is None, which will use the default batch size for the model |
| `--force_layout_block TEXT` | Skip layout and force every page to be treated as a specific block type. Default is None |
| `--disable_tqdm` | Disable tqdm progress bars. Default is False |
| `--max_expand_frac FLOAT` | The maximum fraction to expand the layout box bounds by. Default is 0.05 |

## Line Builder Options

| Option | Description |
|--------|-------------|
| `--detection_batch_size INTEGER` | The batch size to use for the detection model. Default is None, which will use the default batch size for the model |
| `--ocr_error_batch_size INTEGER` | The batch size to use for the ocr error detection model. Default is None, which will use the default batch size for the model |
| `--layout_coverage_min_lines INTEGER` | The minimum number of PdfProvider lines that must be covered by the layout model to consider the lines from the PdfProvider valid. Default is 1 |
| `--layout_coverage_threshold FLOAT` | The minimum coverage ratio required for the layout model to consider the lines from the PdfProvider valid. Default is 0.25 |
| `--min_document_ocr_threshold FLOAT` | If less pages than this threshold are good, OCR will happen in the document. Otherwise it will not. Default is 0.85 |
| `--provider_line_provider_line_min_overlap_pct FLOAT` | The percentage of a provider line that has to be covered by a detected line. Default is 0.1 |
| `--keep_chars` | Keep individual characters. Default is False |

## OCR Builder Options

| Option | Description |
|--------|-------------|
| `--recognition_batch_size INTEGER` | The batch size to use for the recognition model. Default is None, which will use the default batch size for the model |
| `--ocr_task_name TEXT` | The OCR mode to use, see surya for details. Set to 'ocr_without_boxes' for potentially better performance, at the expense of formatting. Default is `ocr_with_boxes` |
| `--disable_ocr_math` | Disable inline math recognition in OCR. Default is False |
| `--drop_repeated_text` | Drop repeated text in OCR results. Default is False |
| `--block_mode_intersection_thresh FLOAT` | Max intersection before falling back to line mode. Default is 0.5 |
| `--block_mode_max_lines INTEGER` | Max lines within a block before falling back to line mode. Default is 15 |
| `--block_mode_max_height_frac FLOAT` | Max height of a block as a percentage of the page before falling back to line mode. Default is 0.5 |

## Structure Builder Options

| Option | Description |
|--------|-------------|
| `--gap_threshold FLOAT` | The minimum gap between blocks to consider them part of the same group. Default is 0.05 |
| `--list_gap_threshold FLOAT` | The minimum gap between list items to consider them part of the same group. Default is 0.1 |

## Processor Options

### Blank Page Processor
| Option | Description |
|--------|-------------|
| `--full_page_block_intersection_threshold FLOAT` | Threshold to detect blank pages. Default is 0.8 |
| `--filter_blank_pages` | Remove blank pages detected as images. Default is False |

### Block Relabel Processor
| Option | Description |
|--------|-------------|
| `--block_relabel_str TEXT` | Comma-separated relabeling rules in the format `<original_label>:<new_label>:<confidence_threshold>`. Example: `Table:Picture:0.85,Form:Picture:0.9`. Default is empty |

### Blockquote Processor
| Option | Description |
|--------|-------------|
| `--min_x_indent FLOAT` | The minimum horizontal indentation required to consider a block as part of a blockquote. Expressed as a percentage of the block width. Default is 0.1 |
| `--x_start_tolerance FLOAT` | The maximum allowable difference between the starting x-coordinates of consecutive blocks to consider them aligned. Expressed as a percentage of the block width. Default is 0.01 |
| `--x_end_tolerance FLOAT` | The maximum allowable difference between the ending x-coordinates of consecutive blocks to consider them aligned. Expressed as a percentage of the block width. Default is 0.01 |

### Debug Processor
| Option | Description |
|--------|-------------|
| `--debug_data_folder TEXT` | The folder to dump debug data to. Default is `debug_data` |
| `--debug_layout_images` | Whether to dump layout debug images. Default is False |
| `--debug_pdf_images` | Whether to dump PDF debug images. Default is False |
| `--debug_json` | Whether to dump block debug data. Default is False |

### Equation Processor
| Option | Description |
|--------|-------------|
| `--model_max_length INTEGER` | The maximum number of tokens to allow for the Recognition model. Default is 1024 |
| `--equation_batch_size INTEGER` | The batch size to use for the recognition model while processing equations. Default is None, which will use the default batch size for the model |

### Ignore Text Processor
| Option | Description |
|--------|-------------|
| `--common_element_threshold FLOAT` | The minimum ratio of pages a text block must appear on to be considered a common element. Default is 0.2 |
| `--common_element_min_blocks INTEGER` | The minimum number of occurrences of a text block within a document to consider it a common element. Default is 3 |
| `--max_streak INTEGER` | The maximum number of consecutive occurrences of a text block allowed before it is classified as a common element. Default is 3 |
| `--text_match_threshold INTEGER` | The minimum fuzzy match score (0-100) required to classify a text block as similar to a common element. Default is 90 |

### Line Merge Processor
| Option | Description |
|--------|-------------|
| `--min_merge_pct FLOAT` | The minimum percentage of intersection area to consider merging. Default is 0.015 |
| `--block_expand_threshold FLOAT` | The percentage of the block width to expand the bounding box. Default is 0.05 |
| `--min_merge_ydist FLOAT` | The minimum y distance between lines to consider merging. Default is 5 |
| `--intersection_pct_threshold FLOAT` | The total amount of intersection area concentrated in the max intersection block. Default is 0.5 |
| `--vertical_overlap_pct_threshold FLOAT` | The minimum percentage of vertical overlap to consider merging. Default is 0.8 |

### Line Numbers Processor
| Option | Description |
|--------|-------------|
| `--strip_numbers_threshold FLOAT` | The fraction of lines or tokens in a block that must be numeric to consider them as line numbers. Default is 0.6 |
| `--min_lines_in_block INTEGER` | The minimum number of lines required in a block for it to be considered during processing. Default is 4 |
| `--min_line_length INTEGER` | The minimum length of a line (in characters) to consider it significant when checking for numeric prefixes or suffixes. Default is 10 |
| `--min_line_number_span_ratio FLOAT` | The minimum ratio of detected line number spans to total lines required to treat them as line numbers. Default is 0.6 |

## LLM Processor Options

### General LLM Options
| Option | Description |
|--------|-------------|
| `--use_llm` | Whether to use LLMs to improve accuracy. Default is False |
| `--max_concurrency INTEGER` | The maximum number of concurrent requests to make to the LLM model. Default is 3 |
| `--image_expansion_ratio FLOAT` | The ratio to expand the image by when cropping. Default is 0.01 |

### LLM Equation Processor
| Option | Description |
|--------|-------------|
| `--min_equation_height FLOAT` | The minimum ratio between equation height and page height to consider for processing. Default is 0.06 |
| `--redo_inline_math` | Whether to redo inline math blocks. Default is False |
| `--equation_latex_prompt TEXT` | The prompt to use for generating LaTeX from equations. Default is a string containing the Gemini prompt |

### LLM Handwriting Processor
| Option | Description |
|--------|-------------|
| `--handwriting_generation_prompt TEXT` | The prompt to use for OCRing handwriting. Default is a string containing the Gemini prompt |

### LLM Image Description Processor
| Option | Description |
|--------|-------------|
| `--extract_images BOOLEAN` | Extract images from the document. Default is True |
| `--image_description_prompt TEXT` | The prompt to use for generating image descriptions. Default is a string containing the Gemini prompt |

### LLM Math Block Processor
| Option | Description |
|--------|-------------|
| `--inlinemath_min_ratio FLOAT` | If more than this ratio of blocks are inlinemath blocks, assume everything has math. Default is 0.4 |

### LLM Page Correction Processor
| Option | Description |
|--------|-------------|
| `--block_correction_prompt TEXT` | The user prompt to guide the block correction process. Default is None |

### LLM Table Processor
| Option | Description |
|--------|-------------|
| `--max_rows_per_batch INTEGER` | If the table has more rows than this, chunk the table. Default is 60 |
| `--max_table_rows INTEGER` | The maximum number of rows in a table to process with the LLM processor. Beyond this will be skipped. Default is 175 |
| `--table_image_expansion_ratio FLOAT` | The ratio to expand the image by when cropping. Default is 0 |
| `--rotation_max_wh_ratio FLOAT` | The maximum width/height ratio for table cells for a table to be considered rotated. Default is 0.6 |
| `--max_table_iterations INTEGER` | The maximum number of iterations to attempt rewriting a table. Default is 2 |
| `--table_rewriting_prompt TEXT` | The prompt to use for rewriting text. Default is a string containing the Gemini rewriting prompt |

### LLM Table Merge Processor
| Option | Description |
|--------|-------------|
| `--table_height_threshold FLOAT` | The minimum height ratio relative to the page for the first table in a pair to be considered for merging. Default is 0.6 |
| `--table_start_threshold FLOAT` | The maximum percentage down the page the second table can start to be considered for merging. Default is 0.2 |
| `--vertical_table_height_threshold FLOAT` | The height tolerance for 2 adjacent tables to be merged into one. Default is 0.25 |
| `--vertical_table_distance_threshold INTEGER` | The maximum distance between table edges for adjacency. Default is 20 |
| `--horizontal_table_width_threshold FLOAT` | The width tolerance for 2 adjacent tables to be merged into one. Default is 0.25 |
| `--horizontal_table_distance_threshold INTEGER` | The maximum distance between table edges for adjacency. Default is 10 |
| `--column_gap_threshold INTEGER` | The maximum gap between columns to merge tables. Default is 50 |
| `--no_merge_tables_across_pages` | Whether to disable merging tables across pages and keep page delimiters. Default is False |
| `--table_merge_prompt TEXT` | The prompt to use for rewriting text. Default is a string containing the Gemini rewriting prompt |

## Section Header Processor
| Option | Description |
|--------|-------------|
| `--level_count INTEGER` | The number of levels to use for headings. Default is 4 |
| `--merge_threshold FLOAT` | The minimum gap between headings to consider them part of the same group. Default is 0.25 |
| `--default_level INTEGER` | The default heading level to use if no heading level is detected. Default is 2 |
| `--height_tolerance FLOAT` | The minimum height of a heading to consider it a heading. Default is 0.99 |

## Table Processor
| Option | Description |
|--------|-------------|
| `--table_rec_batch_size INTEGER` | The batch size to use for the table recognition model. Default is None, which will use the default batch size for the model |
| `--row_split_threshold FLOAT` | The percentage of rows that need to be split across the table before row splitting is active. Default is 0.5 |
| `--pdftext_workers INTEGER` | The number of workers to use for pdftext. Default is 1 |
| `--drop_repeated_table_text` | Drop repeated text in OCR results. Default is False |

## Text Processor
| Option | Description |
|--------|-------------|
| `--column_gap_ratio FLOAT` | The minimum ratio of the page width to the column gap to consider a column break. Default is 0.02 |

## Converter Options

### Extraction Converter
| Option | Description |
|--------|-------------|
| `--pattern TEXT` | Default is `{\d+\}-{48}\n\n` |
| `--existing_markdown TEXT` | Markdown that was already converted for extraction. Default is None |

### Document Provider Options
| Option | Description |
|--------|-------------|
| `--flatten_pdf BOOLEAN` | Whether to flatten the PDF structure. Default is True |
| `--force_ocr` | Whether to force OCR on the whole document. Default is False |
| `--ocr_space_threshold FLOAT` | The minimum ratio of spaces to non-spaces to detect bad text. Default is 0.7 |
| `--ocr_newline_threshold FLOAT` | The minimum ratio of newlines to non-newlines to detect bad text. Default is 0.6 |
| `--ocr_alphanum_threshold FLOAT` | The minimum ratio of alphanumeric characters to non-alphanumeric characters to consider an alphanumeric character. Default is 0.3 |
| `--image_threshold FLOAT` | The minimum coverage ratio of the image to the page to consider skipping the page. Default is 0.65 |
| `--strip_existing_ocr` | Whether to strip existing OCR text from the PDF. Default is False |
| `--disable_links` | Whether to disable links. Default is False |

## Key Prompt Configuration Options

For math content detection and correction, the most important options are:

- `--use_llm`: Enable LLM processing (required for block correction)
- `--redo_inline_math`: Enable inline math processing
- `--force_ocr`: Force OCR for better text extraction
- `--block_correction_prompt TEXT`: Custom prompt for block type correction and content rewriting
- `--equation_latex_prompt TEXT`: Custom prompt for LaTeX equation generation
- `--image_description_prompt TEXT`: Custom prompt for image descriptions
- `--table_rewriting_prompt TEXT`: Custom prompt for table processing
- `--handwriting_generation_prompt TEXT`: Custom prompt for handwriting OCR

## Example Usage for Math Content

```bash
marker input.pdf \
  --use_llm \
  --force_ocr \
  --redo_inline_math \
  --output_format json \
  --block_correction_prompt "Pay special attention to mathematical content..."
```