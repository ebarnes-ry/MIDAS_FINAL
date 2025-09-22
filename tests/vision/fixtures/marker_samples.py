"""
Sample Marker output data based on real test results
These represent the actual structure Marker returns
"""

# Sample text block from real Marker output
SAMPLE_TEXT_BLOCK = {
    "id": "/page/0/Text/1",
    "block_type": "Text", 
    "html": '<p block-type="Text"><b>Question</b>: Which function is monotonic in range [0, pi]?</p>',
    "polygon": [[14.0, 413.3056640625], [484.375, 413.3056640625], [484.375, 447.3701171875], [14.0, 447.3701171875]],
    "bbox": [14.0, 413.3056640625, 484.375, 447.3701171875],
    "children": None,
    "section_hierarchy": {},
    "images": {}
}

# Sample equation block (synthetic but realistic)
SAMPLE_EQUATION_BLOCK = {
    "id": "/page/0/Equation/2", 
    "block_type": "Equation",
    "html": '<p block-type="Equation"><math display="block">x^2 + y^2 = 1</math></p>',
    "polygon": [[100.0, 200.0], [300.0, 200.0], [300.0, 250.0], [100.0, 250.0]],
    "bbox": [100.0, 200.0, 300.0, 250.0],
    "children": None,
    "section_hierarchy": {},
    "images": {},
    "latex": "x^2 + y^2 = 1"
}

# Sample figure block from real Marker output
SAMPLE_FIGURE_BLOCK = {
    "id": "/page/0/Figure/0",
    "block_type": "Figure",
    "html": "",
    "polygon": [[2.44921875, 4.640624999999998], [528.0, 4.640624999999998], [528.0, 413.3056640625], [2.44921875, 413.3056640625]],
    "bbox": [2.44921875, 4.640624999999998, 528.0, 413.3056640625],
    "children": None,
    "section_hierarchy": {},
    "images": {"/page/0/Figure/0": "base64_image_data_here"}
}

# Sample inline math text block
SAMPLE_INLINE_MATH_BLOCK = {
    "id": "/page/0/Text/3",
    "block_type": "Text",
    "html": '<p block-type="Text">Solve for y: <math display="inline">y^2 + 3y - 4 = 0</math> when x = 2</p>',
    "polygon": [[50.0, 100.0], [400.0, 100.0], [400.0, 140.0], [50.0, 140.0]],
    "bbox": [50.0, 100.0, 400.0, 140.0],
    "children": None,
    "section_hierarchy": {},
    "images": {}
}