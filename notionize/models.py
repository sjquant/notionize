from pydantic import BaseModel, ConfigDict, Field, model_serializer
from typing import Any

from notionize.enums import NotionBlockType, NotionColor


class NotionModel(BaseModel):
    """Base model class for all Notion-related data structures with strict validation."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class NotionAnnotations(NotionModel):
    """Text formatting properties for Notion rich text, including bold, italic, and color options."""

    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: NotionColor = NotionColor.DEFAULT


class NotionLink(NotionModel):
    """Represents a URL link in Notion content with validation for URL format."""

    url: str


class NotionTextContent(NotionModel):
    """Container for text content and its associated link (if any) in Notion blocks."""

    content: str
    link: NotionLink | None = None


class NotionRichText(NotionModel):
    """Represents a rich text segment in Notion with formatting annotations and content."""

    type: str = "text"
    text: NotionTextContent
    annotations: NotionAnnotations = Field(default_factory=NotionAnnotations)


class NotionExternal(NotionModel):
    """Represents an external image in Notion with a URL."""

    url: str


class NotionImage(NotionModel):
    """Represents an image in Notion with a URL and optional caption."""

    type: str = "image"
    external: NotionExternal


class NotionBlock(BaseModel):
    """Base class for Notion block types with serialization support for API compatibility."""

    object: str = "block"
    type: NotionBlockType
    content: dict[str, Any]

    @model_serializer
    def to_api_format(self) -> dict[str, Any]:
        return {
            "object": self.object,
            "type": self.type.value,
            self.type.value: self.content,
        }

    model_config = ConfigDict(frozen=True, extra="forbid")
