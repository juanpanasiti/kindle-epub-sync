"""Domain entities package."""

from kindle_epub_sync.domain.entities.file_descriptor import FileDescriptor
from kindle_epub_sync.domain.entities.processing_report import (
	FileProcessingResult,
	FileProcessingStatus,
	SynchronizationReport,
)

__all__ = [
	"FileDescriptor",
	"FileProcessingResult",
	"FileProcessingStatus",
	"SynchronizationReport",
]
