"""Storage helpers for the Learning App (local JSON)."""

from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BOOKS_DIR = DATA_DIR / "books"
LIBRARY_PATH = DATA_DIR / "library.json"


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def now_iso() -> str:
    return _now_iso()


def load_library() -> Dict[str, Any]:
    if not LIBRARY_PATH.exists():
        return {"books": []}
    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_library(data: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _safe_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".", " ")).strip()


def add_book(file_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    src = Path(file_path)
    if not src.exists():
        raise FileNotFoundError(file_path)

    filetype = src.suffix.lower().lstrip(".")
    book_id = str(uuid.uuid4())
    safe_name = _safe_filename(src.stem)
    dest_name = f"{safe_name}-{book_id[:8]}{src.suffix}"
    dest_path = BOOKS_DIR / dest_name

    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest_path)

    book = {
        "id": book_id,
        "title": src.stem,
        "filename": dest_name,
        "filetype": filetype,
        "added_at": _now_iso(),
        "last_opened": None,
        "last_position": None,
        "highlights": [],
    }

    data["books"].append(book)
    save_library(data)
    return book


def remove_book(book_id: str, data: Dict[str, Any]) -> None:
    books = data.get("books", [])
    book = next((b for b in books if b.get("id") == book_id), None)
    if not book:
        return

    file_path = BOOKS_DIR / book.get("filename", "")
    if file_path.exists():
        file_path.unlink()

    data["books"] = [b for b in books if b.get("id") != book_id]
    save_library(data)


def update_book(book: Dict[str, Any], data: Dict[str, Any]) -> None:
    books = data.get("books", [])
    for idx, item in enumerate(books):
        if item.get("id") == book.get("id"):
            books[idx] = book
            break
    data["books"] = books
    save_library(data)


def get_book_path(book: Dict[str, Any]) -> Path:
    return BOOKS_DIR / book.get("filename", "")


def find_book(book_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return next((b for b in data.get("books", []) if b.get("id") == book_id), None)


def list_books(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(data.get("books", []))
