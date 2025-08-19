"""Learning content models for the Learn plugin.

These models represent learning materials, explanations, and content metadata
for the educational experience.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ContentType(Enum):
    """Types of learning content."""

    EXPLANATION = "explanation"
    EXAMPLE = "example"
    CODE_SNIPPET = "code_snippet"
    BEST_PRACTICE = "best_practice"
    WARNING = "warning"
    TIP = "tip"
    QUIZ = "quiz"


class ContentFormat(Enum):
    """Content formats supported."""

    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    HTML = "html"
    CODE = "code"


@dataclass
class ContentMetadata:
    """Metadata for learning content."""

    id: str
    title: str
    description: str = ""
    concept: str = ""
    difficulty: str = "beginner"
    tags: List[str] = field(default_factory=list)
    author: str = ""
    version: str = "1.0.0"
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    prerequisites: List[str] = field(default_factory=list)
    estimated_time_minutes: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "concept": self.concept,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "author": self.author,
            "version": self.version,
            "created_date": self.created_date,
            "updated_date": self.updated_date,
            "prerequisites": self.prerequisites,
            "estimated_time_minutes": self.estimated_time_minutes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentMetadata":
        """Create ContentMetadata from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            concept=data.get("concept", ""),
            difficulty=data.get("difficulty", "beginner"),
            tags=data.get("tags", []),
            author=data.get("author", ""),
            version=data.get("version", "1.0.0"),
            created_date=data.get("created_date"),
            updated_date=data.get("updated_date"),
            prerequisites=data.get("prerequisites", []),
            estimated_time_minutes=data.get("estimated_time_minutes", 5),
        )


@dataclass
class ContentBlock:
    """Individual content block within learning content."""

    type: ContentType
    format: ContentFormat = ContentFormat.MARKDOWN
    content: str = ""
    title: Optional[str] = None
    language: Optional[str] = None  # For code blocks
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type.value,
            "format": self.format.value,
            "content": self.content,
            "title": self.title,
            "language": self.language,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentBlock":
        """Create ContentBlock from dictionary."""
        return cls(
            type=ContentType(data["type"]),
            format=ContentFormat(data.get("format", "markdown")),
            content=data.get("content", ""),
            title=data.get("title"),
            language=data.get("language"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class LearningContent:
    """Complete learning content with metadata and blocks."""

    metadata: ContentMetadata
    blocks: List[ContentBlock] = field(default_factory=list)

    def add_explanation(self, content: str, title: Optional[str] = None) -> None:
        """Add an explanation block."""
        block = ContentBlock(
            type=ContentType.EXPLANATION,
            format=ContentFormat.MARKDOWN,
            content=content,
            title=title,
        )
        self.blocks.append(block)

    def add_code_example(
        self, code: str, language: str = "python", title: Optional[str] = None
    ) -> None:
        """Add a code example block."""
        block = ContentBlock(
            type=ContentType.CODE_SNIPPET,
            format=ContentFormat.CODE,
            content=code,
            title=title,
            language=language,
        )
        self.blocks.append(block)

    def add_tip(self, content: str, title: Optional[str] = None) -> None:
        """Add a tip block."""
        block = ContentBlock(
            type=ContentType.TIP, format=ContentFormat.MARKDOWN, content=content, title=title
        )
        self.blocks.append(block)

    def add_warning(self, content: str, title: Optional[str] = None) -> None:
        """Add a warning block."""
        block = ContentBlock(
            type=ContentType.WARNING, format=ContentFormat.MARKDOWN, content=content, title=title
        )
        self.blocks.append(block)

    def get_blocks_by_type(self, content_type: ContentType) -> List[ContentBlock]:
        """Get all blocks of a specific type."""
        return [block for block in self.blocks if block.type == content_type]

    def get_estimated_reading_time(self) -> int:
        """Get estimated reading time in minutes."""
        # Base time from metadata
        base_time = self.metadata.estimated_time_minutes

        # Add time based on content blocks
        for block in self.blocks:
            if block.type == ContentType.CODE_SNIPPET:
                base_time += 2  # Code takes longer to read
            elif block.type == ContentType.EXPLANATION:
                # Estimate reading time based on word count (average 200 words/min)
                word_count = len(block.content.split())
                base_time += max(1, word_count // 200)

        return base_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "metadata": self.metadata.to_dict(),
            "blocks": [block.to_dict() for block in self.blocks],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LearningContent":
        """Create LearningContent from dictionary."""
        metadata = ContentMetadata.from_dict(data["metadata"])
        blocks = [ContentBlock.from_dict(block) for block in data.get("blocks", [])]
        return cls(metadata=metadata, blocks=blocks)
