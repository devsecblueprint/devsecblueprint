"""Tests for responsive image rewriting in broadcast emails.

Broadcast images are authored as remote markdown links; the renderer must
inject inline responsive styles onto each <img> so they render cleanly across
email clients and on mobile (where <style> blocks are unreliable).
"""

import os
import sys

# Ensure backend is importable
backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(backend_dir))

from app.services.broadcast_email import (  # noqa: E402
    _make_images_responsive,
    _render_markdown_to_html,
    _IMG_INLINE_STYLE,
)


class TestMakeImagesResponsive:
    def test_plain_img_gets_inline_style(self):
        html = '<p><img src="https://cdn.example.com/a.png" alt="a"></p>'
        out = _make_images_responsive(html)
        assert f'style="{_IMG_INLINE_STYLE}"' in out
        assert 'src="https://cdn.example.com/a.png"' in out
        assert 'alt="a"' in out

    def test_self_closing_img_is_handled(self):
        html = '<img src="https://cdn.example.com/a.png" alt="a" />'
        out = _make_images_responsive(html)
        assert out.count("<img") == 1
        assert _IMG_INLINE_STYLE in out
        # No dangling self-closing slash left inside attributes
        assert "/>" not in out

    def test_existing_style_is_preserved_and_takes_precedence(self):
        html = '<img src="x.png" style="border: 2px solid red;">'
        out = _make_images_responsive(html)
        # Base constraints present
        assert "width:100%;" in out
        # Author style preserved and placed after base so it wins on conflict
        assert "border: 2px solid red;" in out
        assert out.index("width:100%;") < out.index("border: 2px solid red;")

    def test_multiple_images_all_rewritten(self):
        html = '<img src="1.png"><p>text</p><img src="2.png" alt="two">'
        out = _make_images_responsive(html)
        assert out.count(f'style="{_IMG_INLINE_STYLE}') == 2

    def test_no_images_is_noop(self):
        html = "<p>Just some <strong>text</strong> and a <a href='x'>link</a>.</p>"
        assert _make_images_responsive(html) == html

    def test_image_is_wrapped_in_anchor_to_its_own_src(self):
        html = '<img src="https://cdn.example.com/shot.png" alt="shot">'
        out = _make_images_responsive(html)
        assert '<a href="https://cdn.example.com/shot.png"' in out
        assert 'target="_blank"' in out
        assert 'rel="noopener noreferrer"' in out
        # Anchor wraps the img
        assert out.index("<a ") < out.index("<img")
        assert out.strip().endswith("</a>")

    def test_already_linked_image_is_not_double_wrapped(self):
        # Authored as a linked image: [![alt](img)](href)
        html = (
            '<a href="https://devsecblueprint.com/page">'
            '<img src="https://cdn.example.com/shot.png" alt="shot"></a>'
        )
        out = _make_images_responsive(html)
        # Only the original anchor remains; no nested <a> introduced
        assert out.count("<a ") == 1
        assert 'href="https://devsecblueprint.com/page"' in out
        # Styles still applied to the inner image
        assert "width:100%;" in out

    def test_non_http_src_is_not_wrapped(self):
        html = '<img src="cid:inline-attachment" alt="x">'
        out = _make_images_responsive(html)
        assert "<a " not in out
        # Styles still applied
        assert "width:100%;" in out


class TestRenderMarkdownToHtml:
    def test_markdown_image_link_becomes_responsive_img(self):
        md = "![Preview](https://cdn.example.com/preview.png)"
        out = _render_markdown_to_html(md)
        assert "<img" in out
        assert "width:100%;" in out
        assert "max-width:100%;" in out
        assert "height:auto;" in out
        assert 'src="https://cdn.example.com/preview.png"' in out
        # Tappable: wrapped in an anchor to the full-resolution image
        assert '<a href="https://cdn.example.com/preview.png"' in out
        assert 'target="_blank"' in out

    def test_text_only_markdown_unaffected(self):
        out = _render_markdown_to_html("Hello **world**")
        assert "<strong>world</strong>" in out
        assert "<img" not in out
