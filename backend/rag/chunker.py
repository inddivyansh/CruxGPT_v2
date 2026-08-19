"""
Chunking.

Rather than blindly splitting on a fixed character count, this walks each
extracted block (which already corresponds to a paragraph/heading/table/page)
and packs consecutive paragraphs into chunks up to chunk_size_chars, only
splitting mid-block when a single paragraph is itself larger than the chunk
size. Overlap is added between chunks so retrieval doesn't lose context at
boundaries. Page number and section metadata ride along with every chunk.

Character-based sizing is used instead of a model-specific tokenizer so the
chunker doesn't depend on any single LLM/embedding provider - it stays a
simple, configurable knob (CHUNK_SIZE_CHARS / CHUNK_OVERLAP_CHARS) that
works reasonably for any provider.
"""
from dataclasses import dataclass

from app.config import settings
from rag.parser import ExtractedBlock


@dataclass
class Chunk:
    text: str
    chunk_index: int
    page_number: int | None
    section: str | None


def _split_large_text(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]
    parts = []
    start = 0
    step = max(size - overlap, 1)
    while start < len(text):
        parts.append(text[start : start + size])
        start += step
    return parts


def chunk_blocks(
    blocks: list[ExtractedBlock],
    chunk_size_chars: int | None = None,
    chunk_overlap_chars: int | None = None,
) -> list[Chunk]:
    size = chunk_size_chars or settings.chunk_size_chars
    overlap = chunk_overlap_chars or settings.chunk_overlap_chars

    chunks: list[Chunk] = []
    buffer = ""
    buffer_page: int | None = None
    buffer_section: str | None = None
    index = 0

    def flush():
        nonlocal buffer, buffer_page, buffer_section, index
        if buffer.strip():
            chunks.append(
                Chunk(text=buffer.strip(), chunk_index=index, page_number=buffer_page, section=buffer_section)
            )
            index += 1
        buffer = ""

    for block in blocks:
        block_text = block.text.strip()
        if not block_text:
            continue

        # A block far bigger than the chunk size (e.g. a dense PDF page) gets
        # split on its own, each piece keeping the block's page/section.
        if len(block_text) > size:
            flush()
            for piece in _split_large_text(block_text, size, overlap):
                chunks.append(
                    Chunk(text=piece, chunk_index=index, page_number=block.page_number, section=block.section)
                )
                index += 1
            continue

        candidate = f"{buffer}\n\n{block_text}" if buffer else block_text
        if len(candidate) > size:
            flush()
            buffer = block_text
            buffer_page = block.page_number
            buffer_section = block.section
        else:
            buffer = candidate
            buffer_page = buffer_page if buffer_page is not None else block.page_number
            buffer_section = buffer_section or block.section

    flush()
    return chunks
