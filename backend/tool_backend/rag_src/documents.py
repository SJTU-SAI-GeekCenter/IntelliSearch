"""Document processing module for RAG service.

This module handles document loading, text extraction, and chunking
using txtai's Textractor pipeline.
"""

import logging
from typing import List, Tuple, Optional
from pathlib import Path

from txtai.pipeline import Textractor


class DocumentProcessor:
    """Process documents for RAG indexing using txtai Textractor.

    This class handles text extraction from various file formats and
    prepares documents for vector indexing.

    Attributes:
        textractor: txtai Textractor instance for text extraction
        chunk_size: Maximum size of text chunks
        overlap: Overlap between chunks
        supported_formats: List of supported file extensions
        logger: Logging instance
    """

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50,
        supported_formats: Optional[List[str]] = None,
    ):
        """
        Initialize the DocumentProcessor.

        Args:
            chunk_size: Maximum size of text chunks in characters
            overlap: Overlap between chunks in characters
            supported_formats: List of supported file extensions (e.g., ["pdf", "txt"])
                             If None, defaults to ["pdf", "txt", "md", "docx"]
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.supported_formats = (
            [fmt.lower() for fmt in (supported_formats or ["pdf", "txt", "md", "docx"])]
        )
        self.textractor = Textractor()
        self.logger = logging.getLogger(__name__)

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a file.

        Args:
            file_path: Path to the file

        Returns:
            Extracted text content

        Raises:
            ValueError: If file format is not supported
            Exception: If text extraction fails
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path_obj.suffix.lstrip(".").lower()

        if extension not in self.supported_formats:
            raise ValueError(
                f"Unsupported file format: .{extension}. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )

        try:
            # txtai Textractor automatically handles different formats
            text = self.textractor(file_path)
            return text
        except Exception as e:
            self.logger.error(f"Failed to extract text from {file_path}: {e}")
            raise

    def chunk_text(self, text: str, document_id: str) -> List[Tuple[str, str, None]]:
        """
        Split text into chunks for indexing.

        Args:
            text: Text content to chunk
            document_id: Base document ID (will be appended with chunk number)

        Returns:
            List of tuples suitable for indexing: (chunk_id, chunk_text, None)
        """
        if not text or not text.strip():
            self.logger.warning(f"Empty text for document {document_id}")
            return []

        chunks = []
        start = 0
        chunk_number = 0

        while start < len(text):
            end = start + self.chunk_size

            # Extract chunk
            chunk = text[start:end]

            # Skip empty chunks
            if chunk.strip():
                chunk_id = f"{document_id}_chunk{chunk_number}"
                chunks.append((chunk_id, chunk, None))
                chunk_number += 1

            # Move to next chunk with overlap
            start = end - self.overlap

        self.logger.debug(
            f"Split document {document_id} into {len(chunks)} chunks"
        )
        return chunks

    def process_file(
        self, file_path: str, document_id: Optional[str] = None
    ) -> List[Tuple[str, str, None]]:
        """
        Process a single file: extract text and chunk it.

        Args:
            file_path: Path to the file
            document_id: Optional document ID. If None, uses filename without extension

        Returns:
            List of tuples (chunk_id, chunk_text, None) ready for indexing
        """
        if document_id is None:
            document_id = Path(file_path).stem

        try:
            text = self.extract_text(file_path)
            chunks = self.chunk_text(text, document_id)
            self.logger.info(
                f"Processed {file_path}: {len(chunks)} chunks"
            )
            return chunks
        except Exception as e:
            self.logger.error(f"Failed to process {file_path}: {e}")
            return []

    def process_directory(
        self, directory_path: str, recursive: bool = True
    ) -> List[Tuple[str, str, None]]:
        """
        Process all supported files in a directory.

        Args:
            directory_path: Path to the directory
            recursive: If True, recursively process subdirectories

        Returns:
            List of tuples (chunk_id, chunk_text, None) from all files
        """
        directory = Path(directory_path)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory_path}")

        all_chunks = []
        files_found = 0
        files_processed = 0
        files_failed = 0

        # Find all files
        if recursive:
            files = [
                p for p in directory.rglob("*")
                if p.is_file() and p.suffix.lstrip(".").lower() in self.supported_formats
            ]
        else:
            files = [
                p for p in directory.iterdir()
                if p.is_file() and p.suffix.lstrip(".").lower() in self.supported_formats
            ]

        files_found = len(files)
        self.logger.info(f"Found {files_found} supported files in {directory_path}")

        # Process each file
        for file_path in files:
            try:
                # Use relative path as document ID for better organization
                relative_path = file_path.relative_to(directory)
                document_id = str(relative_path.with_suffix(""))

                chunks = self.process_file(str(file_path), document_id)
                all_chunks.extend(chunks)
                files_processed += 1
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
                files_failed += 1

        self.logger.info(
            f"Directory processing complete: "
            f"{files_found} found, {files_processed} processed, "
            f"{files_failed} failed, {len(all_chunks)} total chunks"
        )

        return all_chunks

    def is_supported(self, file_path: str) -> bool:
        """
        Check if a file format is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if format is supported, False otherwise
        """
        extension = Path(file_path).suffix.lstrip(".").lower()
        return extension in self.supported_formats
