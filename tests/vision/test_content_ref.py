"""
Tests for content-ref resolution functionality in the formatter
"""

import pytest
from src.pipeline.vision.formatter import Formatter
from src.pipeline.vision.types import Block


class TestContentRefResolution:
    """Test content-ref resolution functionality"""
    
    def test_extract_content_refs_from_html(self):
        """Test extraction of content-ref tags from HTML"""
        # Test with single quotes
        html1 = "<p>Solve: <content-ref src='/page/0/Equation/1'></content-ref></p>"
        refs1 = Formatter.extract_content_refs_from_html(html1)
        assert refs1 == ['/page/0/Equation/1']
        
        # Test with double quotes
        html2 = '<p>Answer: <content-ref src="/page/0/Equation/2"></content-ref></p>'
        refs2 = Formatter.extract_content_refs_from_html(html2)
        assert refs2 == ['/page/0/Equation/2']
        
        # Test with multiple refs
        html3 = '<p>Problem: <content-ref src="/page/0/Text/1"></content-ref> Solution: <content-ref src="/page/0/Equation/1"></content-ref></p>'
        refs3 = Formatter.extract_content_refs_from_html(html3)
        assert refs3 == ['/page/0/Text/1', '/page/0/Equation/1']
        
        # Test with no refs
        html4 = "<p>No content-ref tags here</p>"
        refs4 = Formatter.extract_content_refs_from_html(html4)
        assert refs4 == []
    
    def test_resolve_content_refs(self):
        """Test resolution of individual content-refs"""
        # Create test blocks
        block1 = Block(
            id="/page/0/Equation/1",
            block_type="Equation",
            html_content="<math display='block'>x^2 + 1 = 0</math>",
            raw_content="x^2 + 1 = 0",
            bbox=[0, 0, 100, 20],
            polygon=[[0, 0], [100, 0], [100, 20], [0, 20]],
            confidence=0.95
        )
        
        block2 = Block(
            id="/page/0/Text/1",
            block_type="Text",
            html_content="<p>Solve the equation</p>",
            raw_content="Solve the equation",
            bbox=[0, 25, 100, 45],
            polygon=[[0, 25], [100, 25], [100, 45], [0, 45]],
            confidence=0.92
        )
        
        blocks = [block1, block2]
        
        # Test successful resolution
        resolved = Formatter.resolve_content_refs(blocks, "/page/0/Equation/1")
        assert resolved == "<math display='block'>x^2 + 1 = 0</math>"
        
        # Test missing content-ref
        missing = Formatter.resolve_content_refs(blocks, "/page/0/Nonexistent/1")
        assert missing == "[Content not found: /page/0/Nonexistent/1]"
    
    def test_create_editable_problem_statement(self):
        """Test creation of editable problem statement with resolved content-refs"""
        # Create test blocks with content-refs
        text_block = Block(
            id="/page/0/Text/1",
            block_type="Text",
            html_content="<p>Solve: <content-ref src='/page/0/Equation/1'></content-ref></p>",
            raw_content="Solve: [EQUATION_REF]",
            bbox=[0, 0, 100, 20],
            polygon=[[0, 0], [100, 0], [100, 20], [0, 20]],
            confidence=0.95
        )
        
        equation_block = Block(
            id="/page/0/Equation/1",
            block_type="Equation",
            html_content="<math display='block'>x^2 + 2x + 1 = 0</math>",
            raw_content="x^2 + 2x + 1 = 0",
            bbox=[0, 25, 100, 45],
            polygon=[[0, 25], [100, 25], [100, 45], [0, 45]],
            confidence=0.98
        )
        
        selected_blocks = [text_block, equation_block]
        
        # Test problem statement creation
        problem_statement = Formatter.create_editable_problem_statement(selected_blocks)
        
        # Should resolve content-ref and include both blocks
        assert "<math display='block'>x^2 + 2x + 1 = 0</math>" in problem_statement
        assert "Solve:" in problem_statement
        # Content-ref should be resolved (not present in final output)
        assert "<content-ref" not in problem_statement
    
    def test_resolve_all_content_refs(self):
        """Test resolution of all content-refs in a list of blocks"""
        # Create test blocks
        block1 = Block(
            id="/page/0/Text/1",
            block_type="Text",
            html_content="<p>Problem: <content-ref src='/page/0/Equation/1'></content-ref></p>",
            raw_content="Problem: [EQUATION_REF]",
            bbox=[0, 0, 100, 20],
            polygon=[[0, 0], [100, 0], [100, 20], [0, 20]],
            confidence=0.95
        )
        
        block2 = Block(
            id="/page/0/Equation/1",
            block_type="Equation",
            html_content="<math display='block'>x^2 = 1</math>",
            raw_content="x^2 = 1",
            bbox=[0, 25, 100, 45],
            polygon=[[0, 25], [100, 25], [100, 45], [0, 45]],
            confidence=0.98
        )
        
        block3 = Block(
            id="/page/0/Text/2",
            block_type="Text",
            html_content="<p>Solution: <content-ref src='/page/0/Equation/2'></content-ref></p>",
            raw_content="Solution: [SOLUTION_REF]",
            bbox=[0, 50, 100, 70],
            polygon=[[0, 50], [100, 50], [100, 70], [0, 70]],
            confidence=0.92
        )
        
        blocks = [block1, block2, block3]
        
        # Test resolution of all content-refs
        resolved = Formatter.resolve_all_content_refs(blocks)
        
        # Should include all block content
        assert "/page/0/Text/1" in resolved
        assert "/page/0/Equation/1" in resolved
        assert "/page/0/Text/2" in resolved
        
        # Should handle missing content-refs
        assert "/page/0/Equation/2" in resolved
        assert resolved["/page/0/Equation/2"] == "[Content not found: /page/0/Equation/2]"
    
    def test_content_ref_with_different_quote_types(self):
        """Test content-ref resolution with different quote types"""
        # Test with single quotes
        html_single = "<p>Test: <content-ref src='/page/0/Block/1'></content-ref></p>"
        refs_single = Formatter.extract_content_refs_from_html(html_single)
        assert refs_single == ['/page/0/Block/1']
        
        # Test with double quotes
        html_double = '<p>Test: <content-ref src="/page/0/Block/1"></content-ref></p>'
        refs_double = Formatter.extract_content_refs_from_html(html_double)
        assert refs_double == ['/page/0/Block/1']
        
        # Test mixed quotes in same HTML
        html_mixed = '<p>First: <content-ref src="/page/0/Block/1"></content-ref> Second: <content-ref src=\'/page/0/Block/2\'></content-ref></p>'
        refs_mixed = Formatter.extract_content_refs_from_html(html_mixed)
        assert refs_mixed == ['/page/0/Block/1', '/page/0/Block/2']
    
    def test_content_ref_edge_cases(self):
        """Test edge cases for content-ref resolution"""
        # Test empty HTML
        refs_empty = Formatter.extract_content_refs_from_html("")
        assert refs_empty == []
        
        # Test HTML with no content-ref tags
        refs_none = Formatter.extract_content_refs_from_html("<p>No refs here</p>")
        assert refs_none == []
        
        # Test malformed content-ref (missing closing tag) - regex still extracts src
        refs_malformed = Formatter.extract_content_refs_from_html("<p>Test: <content-ref src='/page/0/Block/1'></p>")
        assert refs_malformed == ['/page/0/Block/1']  # Regex extracts src even if tag is malformed
        
        # Test empty blocks list
        resolved_empty = Formatter.resolve_content_refs([], "/page/0/Block/1")
        assert resolved_empty == "[Content not found: /page/0/Block/1]"
        
        # Test empty selected blocks
        problem_empty = Formatter.create_editable_problem_statement([])
        assert problem_empty == ""
