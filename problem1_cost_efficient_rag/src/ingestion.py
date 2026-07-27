from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup
from pypdf import PdfReader


SUPPORTED_SUFFIXES = {".pdf", ".html", ".htm", ".md", ".markdown", ".txt"}


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source: str
    file_type: str
    category: str
    chunk_index: int
    text: str


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return clean_text("\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages))
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if suffix in {".html", ".htm"}:
        return clean_text(BeautifulSoup(raw, "html.parser").get_text(" "))
    return clean_text(raw)


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be > 0 and overlap must be in [0, chunk_size).")
    text = clean_text(text)
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        if end < len(text):
            split_at = max(text.rfind(". ", start, end), text.rfind(" ", start, end))
            if split_at > start + chunk_size // 2:
                end = split_at + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def chunk_id(source: str, index: int, text: str) -> str:
    payload = f"{source}|{index}|{text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def category_for(path: Path) -> str:
    stem = path.stem.lower()
    for category in ("product", "policy", "engineering", "support", "security", "general"):
        if category in stem:
            return category
    return "general"


def make_chunks(path: Path, source: str, chunk_size: int, overlap: int) -> list[Chunk]:
    text = load_document(path)
    file_type = path.suffix.lower().lstrip(".")
    category = category_for(path)
    return [
        Chunk(chunk_id(source, index, piece), source, file_type, category, index, piece)
        for index, piece in enumerate(split_text(text, chunk_size, overlap))
    ]


def iter_documents(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            yield path
