from typing import Any, Callable
from notionize.converters import (
    BlockConverter,
    CodeBlockConverter,
    DividerConverter,
    HeadingConverter,
    ImageConverter,
    ListConverter,
    NullConverter,
    ParagraphConverter,
    QuoteConverter,
    TableConverter,
)
from notionize.errors import ConversionError, InvalidMarkdownError, UnknownTokenError
from notionize.models import NotionBlock
import mistune

ConverterFactory = Callable[[dict[str, Any]], BlockConverter | None]


class Notionizer:
    """A class that converts Markdown content into Notion API-compatible blocks.

    This class handles the parsing of Markdown content and conversion into Notion blocks
    using various converters for different Markdown elements (headings, paragraphs, lists, etc.).

    Args:
        converter_factory: Optional callable that creates custom block converters.
            It should take a token dict and return a BlockConverter or None.
    """

    def __init__(
        self,
        *,
        converter_factory: ConverterFactory | None = None,
    ):
        self._converter_factory = converter_factory

    def _get_converter(self, token: dict[str, Any]) -> BlockConverter:
        if self._converter_factory:
            res: BlockConverter | None = self._converter_factory(token)

            if res is not None:
                return res

        token_type = token.get("type")

        if token_type is None or token_type == "blank_line":
            return NullConverter()
        elif token_type == "paragraph" or token_type == "block_text":
            return ParagraphConverter()
        elif token_type == "heading":
            return HeadingConverter()
        elif token_type == "block_code":
            return CodeBlockConverter()
        elif token_type == "block_quote":
            return QuoteConverter()
        elif token_type == "thematic_break":
            return DividerConverter()
        elif token_type == "list":
            return ListConverter()
        elif token_type == "table":
            return TableConverter()
        elif token_type == "image":
            return ImageConverter()
        else:
            raise UnknownTokenError(
                f"Unknown token type: {token_type}. "
                "If you need to handle this token type, provide a custom converter_factory"
            )

    def run(self, content: str) -> list[dict[str, Any]]:
        """Convert Markdown content into a list of Notion blocks.

        Args:
            content: Markdown string to convert.

        Returns:
            List of dictionaries representing Notion blocks, ready for the Notion API.

        Raises:
            InvalidMarkdownError: If the markdown content cannot be parsed properly.
        """
        tokens = mistune.create_markdown(renderer="ast", plugins=["table"])(content)
        if isinstance(tokens, str):
            raise InvalidMarkdownError(
                "Failed to parse markdown: expected list of tokens but got string"
            )

        blocks = self.convert_blocks(tokens)
        return [block.model_dump(mode="json", exclude_none=True) for block in blocks]

    def convert_blocks(self, tokens: list[dict[str, Any]]) -> list[NotionBlock]:
        """Convert a list of Markdown tokens into Notion blocks.

        Args:
            tokens: List of Markdown tokens from the parser.

        Returns:
            List of NotionBlock objects.

        Raises:
            ConversionError: If conversion of any block fails.
        """
        res: list[NotionBlock] = []
        for token in tokens:
            token_type = token.get("type")

            if token_type is None:
                continue

            converter = self._get_converter(token)
            try:
                block = converter.convert(token)
                if block is None:
                    continue

                if isinstance(block, list):
                    res.extend(block)
                else:
                    res.append(block)

            except Exception as e:
                raise ConversionError(
                    f"Failed to convert token of type '{token_type}'",
                ) from e

        return res


def notionize(
    content: str,
    *,
    converter_factory: ConverterFactory | None = None,
) -> list[dict[str, Any]]:
    """Convert Markdown content into Notion API-compatible blocks.

    This is the main function for converting Markdown to Notion blocks. It creates
    a Notionizer instance and processes the content.

    Args:
        content: Markdown string to convert.
        converter_factory: Optional callable that creates custom block converters.
            It should take a token dict and return a BlockConverter or None.

    Returns:
        List of dictionaries representing Notion blocks, ready for the Notion API.

    Raises:
        InvalidMarkdownError: If the markdown content cannot be parsed properly.
    """
    notionizer = Notionizer(converter_factory=converter_factory)
    return notionizer.run(content)
