from dataclasses import dataclass
from typing import Any, Literal, cast
from abc import ABC, abstractmethod

from notionize.enums import NotionBlockType, NotionLanguage
from notionize.models import (
    NotionAnnotations,
    NotionBlock,
    NotionLink,
    NotionModel,
    NotionRichText,
    NotionTextContent,
)


class BlockConverter(ABC):
    """Abstract base class for converting markdown tokens into Notion blocks.
    All concrete converter classes must implement the convert method."""

    @abstractmethod
    def convert(self, token: dict[str, Any]) -> NotionBlock | list[NotionBlock] | None:
        pass


class ParagraphConverter(BlockConverter):
    """Converts markdown paragraph tokens into Notion paragraph blocks."""

    def convert(self, token: dict[str, Any]) -> NotionBlock:

        children = token.get("children", [])

        if len(children) == 1 and children[0]["type"] == "image":
            return ImageConverter().convert(children[0])

        blocks = convert_inline_tokens(children)

        return NotionBlock(
            type=NotionBlockType.PARAGRAPH, content={"rich_text": blocks}
        )


class HeadingConverter(BlockConverter):
    """Converts markdown heading tokens into Notion heading blocks (h1-h3)."""

    def convert(self, token: dict[str, Any]) -> NotionBlock:
        level = self._get_level(token)
        heading_type = getattr(NotionBlockType, f"HEADING_{level}")
        rich_text = convert_inline_tokens(token.get("children", []))
        return NotionBlock(type=heading_type, content={"rich_text": rich_text})

    def _get_level(self, token: dict[str, Any]) -> int:
        level = token.get("level")
        res = None
        if level := token.get("level"):
            res = level
        elif attrs := token.get("attrs"):
            res = attrs.get("level")

        if res is None:
            return 1

        if not 1 <= res <= 3:
            return 3

        return res


class CodeBlockConverter(BlockConverter):
    """Converts markdown code block tokens into Notion code blocks with language detection."""

    def convert(self, token: dict[str, Any]) -> NotionBlock:
        language = self._get_lang(token)

        return NotionBlock(
            type=NotionBlockType.CODE,
            content={
                "rich_text": [
                    NotionRichText(text=NotionTextContent(content=token.get("raw", "")))
                ],
                "language": language,
            },
        )

    def _get_lang(self, token) -> str:
        lang = token.get("info") or token.get("attrs", {}).get(
            "info", NotionLanguage.PLAIN_TEXT
        )

        if lang in [e.value for e in NotionLanguage]:
            return lang

        return NotionLanguage.PLAIN_TEXT.value


class ListConverter(BlockConverter):
    """Converts markdown list tokens into Notion list blocks."""

    def convert(self, token: dict[str, Any]) -> list[NotionBlock]:
        res: list[NotionBlock] = []

        is_ordered = token.get("attrs", {}).get("ordered", False)

        for item in token.get("children", []):
            converter = ListItemConverter(
                list_type=(
                    NotionBlockType.NUMBERED if is_ordered else NotionBlockType.BULLETED
                )
            )
            res.append(converter.convert(item))

        return res


class ListItemConverter(BlockConverter):
    """Converts markdown list item tokens into Notion bulleted or numbered list items.
    Supports nested lists and mixed content within list items."""

    def __init__(
        self,
        list_type: Literal[NotionBlockType.BULLETED, NotionBlockType.NUMBERED],
    ):
        self.list_type = list_type

    def convert(self, token: dict[str, Any]) -> NotionBlock:
        blocks: list[NotionModel] = []
        children_blocks: list[NotionBlock] = []

        for child in token.get("children", []):
            if child["type"] == "block_text" or child["type"] == "paragraph":
                blocks.extend(convert_inline_tokens(child.get("children", [])))
            else:
                # For Nested List
                from notionize.main import Notionizer

                notionizer = Notionizer()
                nested_blocks = notionizer.convert_blocks([child])
                if nested_blocks:
                    children_blocks.extend(nested_blocks)

        content: dict[str, Any] = {"rich_text": blocks}

        if children_blocks:
            content["children"] = children_blocks

        return NotionBlock(
            type=self.list_type,
            content=cast(dict[str, Any], content),
        )


class QuoteConverter(BlockConverter):
    """Converts markdown blockquote tokens into Notion quote blocks."""

    def convert(self, token: dict[str, Any]) -> NotionBlock:
        children = token.get("children", [])
        if children and children[0]["type"] == "paragraph":
            children = children[0].get("children", [])

        blocks = convert_inline_tokens(children)
        return NotionBlock(type=NotionBlockType.QUOTE, content={"rich_text": blocks})


class DividerConverter(BlockConverter):
    """Converts markdown horizontal rule tokens into Notion divider blocks."""

    def convert(self, token: dict[str, Any]) -> NotionBlock:
        return NotionBlock(type=NotionBlockType.DIVIDER, content={})


@dataclass(frozen=True, slots=True)
class TableStructure:
    header_cells: list[dict[str, Any]]
    body_rows: list[dict[str, Any]]


class TableConverter(BlockConverter):
    """Converts markdown table tokens into Notion table blocks.
    Supports tables with headers and handles special cases like link cells."""

    def convert(self, token: dict[str, Any]) -> NotionBlock:
        table_structure = self._extract_table_structure(token)
        table_rows = self._process_table_rows(table_structure)

        return NotionBlock(
            type=NotionBlockType.TABLE,
            content={
                "table_width": self._calculate_table_width(table_structure),
                "has_column_header": bool(table_structure.header_cells),
                "has_row_header": False,
                "children": [
                    {"type": "table_row", "table_row": {"cells": row}}
                    for row in table_rows
                ],
            },
        )

    def _extract_table_structure(self, token: dict[str, Any]) -> TableStructure:
        table_head = next(
            (
                child
                for child in token.get("children", [])
                if child["type"] == "table_head"
            ),
            None,
        )
        table_body = next(
            (
                child
                for child in token.get("children", [])
                if child["type"] == "table_body"
            ),
            None,
        )

        header_cells = table_head.get("children", []) if table_head else []
        body_rows = table_body.get("children", []) if table_body else []

        return TableStructure(header_cells, body_rows)

    def _calculate_table_width(self, table_structure: TableStructure) -> int:
        if table_structure.header_cells:
            return len(table_structure.header_cells)
        if table_structure.body_rows:
            return len(table_structure.body_rows[0])
        return 1

    def _process_table_rows(
        self, table_structure: TableStructure
    ) -> list[list[list[NotionModel]]]:
        table_rows = []

        if table_structure.header_cells:
            table_rows.append(self._convert_row(table_structure.header_cells))

        for row in table_structure.body_rows:
            table_rows.append(self._convert_row(row.get("children", [])))

        return table_rows

    def _convert_row(self, cells: list[dict[str, Any]]) -> list[list[NotionModel]]:
        result = []

        for cell in cells:
            cell_content = cell.get("children", [])
            if self._is_link_cell(cell_content):
                result.append(
                    cast(list[NotionModel], self._convert_link_cell(cell_content[0]))
                )
            else:
                result.append(convert_inline_tokens(cell_content))
        return result

    def _is_link_cell(self, cell_content: list[dict[str, Any]]) -> bool:
        return bool(cell_content and cell_content[0].get("type") == "link")

    def _convert_link_cell(self, link_token: dict[str, Any]) -> list[NotionRichText]:
        return [
            NotionRichText(
                text=NotionTextContent(
                    content=link_token.get("children", [{}])[0].get("raw", ""),
                    link=NotionLink(url=link_token.get("attrs", {}).get("url", "")),
                )
            )
        ]


class ImageConverter(BlockConverter):
    """Converts markdown image tokens into Notion image blocks."""

    def convert(self, token: dict[str, Any]) -> NotionBlock:
        image_url = token.get("attrs", {}).get("url", "")
        return NotionBlock(
            type=NotionBlockType.IMAGE,
            content={"type": "external", "external": {"url": image_url}},
        )


class NullConverter(BlockConverter):
    """A null object pattern implementation that returns None for any conversion.
    Used as a fallback for unsupported markdown token types."""

    def convert(self, token: dict[str, Any]) -> None:
        return None


def convert_inline_tokens(tokens: list[dict[str, Any]]) -> list[NotionModel]:
    result: list[NotionModel] = []
    for token in tokens:
        if token["type"] == "text":
            result.append(create_text(token["raw"]))
        elif token["type"] in ("strong", "emphasis"):
            result.extend(create_formatted_texts(token))
        elif token["type"] == "link":
            result.extend(create_links(token))
    return result


def create_text(
    content: str,
    annotations: dict[str, Any] | None = None,
    link: str | None = None,
) -> NotionRichText:
    return NotionRichText(
        text=NotionTextContent(
            content=content, link=NotionLink(url=link) if link else None
        ),
        annotations=NotionAnnotations(**(annotations or {})),
    )


def create_formatted_texts(token: dict[str, Any]) -> list[NotionRichText]:
    annotations = {"bold": True} if token["type"] == "strong" else {"italic": True}
    result = []
    for child in token.get("children", []):
        if child["type"] == "text":
            result.append(create_text(child["raw"], annotations))
    return result


def create_links(token: dict[str, Any]) -> list[NotionRichText]:
    return [
        create_text(
            token.get("children", [{}])[0].get("text", ""),
            link=token.get("link", ""),
        )
    ]
