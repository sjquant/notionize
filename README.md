# Notionize

A Python library for converting Markdown text to Notion blocks.

## Description

Notionize is a tool that helps you transform Markdown text into Notion-compatible blocks, making it easy to integrate your Markdown content with the Notion API.

## Installation

```bash
pip install notionize
```

## Usage

````python
from notionize import notionize

markdown = """# Main Heading

This is a paragraph with formatting and a [link](https://example.com).

> Here's a blockquote
> With multiple lines

- List item 1
  - Nested item
- List item 2

```python
def hello_world():
    print("Hello World!")
```

| Header 1 | Header 2 |
| -------- | -------- |
| Cell 1   | Cell 2   |

"""

notion_blocks = notionize(markdown)

````

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
