"""Domain entity representing a file discovered in a source repository."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FileDescriptor:
    """Immutable file metadata required by the core use case."""

    file_id: str
    name: str
