import pytest
from notionize.enums import NotionBlockType
from notionize.main import Notionizer, notionize
from notionize.errors import ConversionError, UnknownTokenError
from notionize.converters import BlockConverter
from notionize.models import NotionBlock

from syrupy.assertion import SnapshotAssertion


def test_paragraph_conversion(snapshot: SnapshotAssertion):
    """Test paragraph conversion with various inline elements."""
    markdown = """This is a simple paragraph.
    
This has **bold** and _italic_ text and [a link](https://example.com)."""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == snapshot


def test_heading_conversion(snapshot: SnapshotAssertion):
    """Test heading conversion with all levels."""
    markdown = """# Heading 1
## Heading 2
### Heading 3
#### Heading 4 (should be converted to h3)"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == snapshot


def test_code_block_conversion(snapshot: SnapshotAssertion):
    """Test code block conversion with different languages."""
    markdown = """```python
def hello():
    print("Hello")
```

```javascript
console.log('Hello');
```

```
Plain text code block
```"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == snapshot


def test_list_conversion(snapshot: SnapshotAssertion):
    """Test list conversion with nested and mixed lists."""
    markdown = """- Unordered item 1
  - Nested unordered
    1. Nested ordered
    2. Another ordered
- Unordered item 2
  Some paragraph in list
  
1. Ordered item 1
2. Ordered item 2
   - Nested unordered
   - Another unordered"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == snapshot


def test_quote_conversion(snapshot: SnapshotAssertion):
    """Test quote conversion with multiple lines and formatting."""
    markdown = """> This is a blockquote
> With **bold** and _italic_ text
> And multiple lines"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == snapshot


def test_divider_conversion(snapshot: SnapshotAssertion):
    """Test divider converter."""
    markdown = """Some text

---

More text"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == snapshot


def test_table_conversion(snapshot: SnapshotAssertion):
    """Test table conversion with headers, links, and formatting."""
    markdown = """| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Normal cell | **Bold** cell | [Link](https://example.com) |
| _Italic_ | Multiple<br>lines | Simple text |"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == snapshot


def test_image_conversion(snapshot: SnapshotAssertion):
    """Test image conversion."""
    markdown = """![Image alt text](https://example.com/image.jpg)"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == snapshot


def test_custom_converter_factory():
    """
    Test the ability to override default conversion behavior using a custom converter factory.
    """

    class CustomParagraphConverter(BlockConverter):
        def convert(self, token: dict) -> NotionBlock:
            return NotionBlock(
                type=NotionBlockType.PARAGRAPH,
                content={
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "CUSTOM: " + token.get("text", "")},
                        }
                    ]
                },
            )

    def custom_factory(token: dict) -> BlockConverter | None:
        if token.get("type") == "paragraph":
            return CustomParagraphConverter()
        return None

    markdown = "This is a test paragraph."
    notionizer = Notionizer(converter_factory=custom_factory)
    res = notionizer.run(markdown)
    assert res == [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "CUSTOM: "}}]
            },
        }
    ]


def test_unknown_token_type_raises_error():
    """
    Test that providing an unknown token type to convert_blocks directly raises a ValueError.
    """
    notionizer = Notionizer()
    unknown_token = {"type": "unknown_type", "text": "test"}

    try:
        notionizer.convert_blocks([unknown_token])
        assert False, "Expected UnknownTokenError"
    except UnknownTokenError as e:
        assert "Unknown token type: unknown_type" in str(e)


def test_conversion_error_raised():
    """
    Test that if the conversion fails, a ConversionError is raised.
    """

    class FailingConverter(BlockConverter):
        def convert(self, token: dict) -> NotionBlock:
            raise ValueError("Conversion failed")

    def failing_factory(token: dict) -> BlockConverter | None:
        return FailingConverter()

    notionizer = Notionizer(converter_factory=failing_factory)
    with pytest.raises(ConversionError) as exc_info:
        notionizer.run("Test paragraph")
    assert "Failed to convert token" in str(exc_info.value)


def test_notionize(snapshot: SnapshotAssertion):
    """
    Test the notionize function with comprehensive Markdown syntax.
    """
    markdown = """# Heading 1
## Heading 2
### Heading 3

This is a paragraph with **bold**, _italic_, and `inline code` text.

> This is a blockquote
> with multiple lines

1. Ordered list item 1
2. Ordered list item 2
   - Nested unordered item
   - Another nested item

- Unordered list item
- Another unordered item
  1. Nested ordered item
  2. Another nested ordered item

```python
def hello_world():
    print("Hello World!")
```

---

[Link text](https://example.com)

![Image alt text](https://example.com/image.jpg)

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
"""

    res = notionize(markdown)
    assert res == snapshot
