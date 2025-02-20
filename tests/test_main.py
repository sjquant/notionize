from typing import Any
import pytest
from notionize.enums import NotionBlockType
from notionize.main import Notionizer, notionize
from notionize.errors import ConversionError, UnknownTokenError
from notionize.converters import BlockConverter
from notionize.models import NotionBlock

from syrupy.assertion import SnapshotAssertion
from inline_snapshot import snapshot as inline_snapshot


def test_paragraph_conversion():
    """Test paragraph conversion with various inline elements."""
    markdown = """This is a simple paragraph."""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == inline_snapshot(
        [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "This is a simple paragraph."},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            }
        ]
    )


def test_heading_conversion():
    """Test heading conversion with all levels."""
    markdown = """# Heading 1
## Heading 2
### Heading 3
#### Heading 4 (should be converted to h3)"""

    notionizer = Notionizer()
    res: list[dict[str, Any]] = notionizer.run(markdown)
    assert res == inline_snapshot(
        [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Heading 1"},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Heading 2"},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Heading 3"},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Heading 4 (should be converted to h3)"
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            },
        ]
    )


def test_code_block_conversion():
    """Test code block conversion with different languages."""
    markdown = """```python
print("Hello")
```"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == inline_snapshot(
        [
            {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": 'print("Hello")\n'},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ],
                    "language": "python",
                },
            }
        ]
    )


def test_code_block_conversion_with_unknown_language():
    """Test code block conversion with unknown language.
    It should be converted to plain text)."""
    markdown = """```unknown
print("Hello")
```"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == inline_snapshot(
        [
            {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": 'print("Hello")\n'},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ],
                    "language": "plain text",
                },
            }
        ]
    )


def test_bullet_list_conversion():
    """Test list conversion with nested and mixed lists."""
    markdown = """- Unordered item 1
- Unordered item 2
"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == inline_snapshot(
        [
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Unordered item 1"},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Unordered item 2"},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            },
        ]
    )


def test_ordered_list_conversion():
    """Test ordered list conversion with nested and mixed lists."""
    markdown = """1. Ordered item 1
2. Ordered item 2
"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == inline_snapshot(
        [
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Ordered item 1"},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Ordered item 2"},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            },
        ]
    )


def test_quote_conversion():
    """Test quote conversion with multiple lines and formatting."""
    markdown = """> This is a blockquote"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == inline_snapshot(
        [
            {
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "This is a blockquote"},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            }
        ]
    )


def test_divider_conversion():
    """Test divider converter."""
    markdown = """Some text

---

More text"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == inline_snapshot(
        [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Some text"},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            },
            {"object": "block", "type": "divider", "divider": {}},
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "More text"},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                        }
                    ]
                },
            },
        ]
    )


def test_table_conversion():
    """Test table conversion with headers, links, and formatting."""
    markdown = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1 | Cell 2 |
| Cell 3 | Cell 4 |"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == inline_snapshot(
        [
            {
                "object": "block",
                "type": "table",
                "table": {
                    "table_width": 2,
                    "has_column_header": True,
                    "has_row_header": False,
                    "children": [
                        {
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [
                                        {
                                            "type": "text",
                                            "text": {"content": "Header 1"},
                                            "annotations": {
                                                "bold": False,
                                                "italic": False,
                                                "strikethrough": False,
                                                "underline": False,
                                                "code": False,
                                                "color": "default",
                                            },
                                        }
                                    ],
                                    [
                                        {
                                            "type": "text",
                                            "text": {"content": "Header 2"},
                                            "annotations": {
                                                "bold": False,
                                                "italic": False,
                                                "strikethrough": False,
                                                "underline": False,
                                                "code": False,
                                                "color": "default",
                                            },
                                        }
                                    ],
                                ]
                            },
                        },
                        {
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [
                                        {
                                            "type": "text",
                                            "text": {"content": "Cell 1"},
                                            "annotations": {
                                                "bold": False,
                                                "italic": False,
                                                "strikethrough": False,
                                                "underline": False,
                                                "code": False,
                                                "color": "default",
                                            },
                                        }
                                    ],
                                    [
                                        {
                                            "type": "text",
                                            "text": {"content": "Cell 2"},
                                            "annotations": {
                                                "bold": False,
                                                "italic": False,
                                                "strikethrough": False,
                                                "underline": False,
                                                "code": False,
                                                "color": "default",
                                            },
                                        }
                                    ],
                                ]
                            },
                        },
                        {
                            "type": "table_row",
                            "table_row": {
                                "cells": [
                                    [
                                        {
                                            "type": "text",
                                            "text": {"content": "Cell 3"},
                                            "annotations": {
                                                "bold": False,
                                                "italic": False,
                                                "strikethrough": False,
                                                "underline": False,
                                                "code": False,
                                                "color": "default",
                                            },
                                        }
                                    ],
                                    [
                                        {
                                            "type": "text",
                                            "text": {"content": "Cell 4"},
                                            "annotations": {
                                                "bold": False,
                                                "italic": False,
                                                "strikethrough": False,
                                                "underline": False,
                                                "code": False,
                                                "color": "default",
                                            },
                                        }
                                    ],
                                ]
                            },
                        },
                    ],
                },
            }
        ]
    )


def test_image_conversion():
    """Test image conversion."""
    markdown = """![Image alt text](https://example.com/image.jpg)"""

    notionizer = Notionizer()
    res = notionizer.run(markdown)
    assert res == inline_snapshot(
        [
            {
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {"url": "https://example.com/image.jpg"},
                },
            }
        ]
    )


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
