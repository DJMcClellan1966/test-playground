"""Learning App (MVP) - Tkinter reader with highlights and search."""

from __future__ import annotations

import tkinter as tk
import uuid
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, List, Optional

import storage


class LearningApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Learning App")
        self.geometry("1100x700")

        self.data: Dict[str, Any] = storage.load_library()
        self.current_book_id: Optional[str] = None
        self.book_index_map: List[str] = []
        self.search_results: List[Dict[str, Any]] = []
        self.highlight_index_map: List[str] = []

        self._build_ui()
        self._refresh_library()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        main_pane = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left panel: Library + Search
        left = ttk.Frame(main_pane, padding=8)
        main_pane.add(left, weight=1)

        ttk.Label(left, text="Library", font=("Segoe UI", 11, "bold")).pack(anchor="w")

        self.library_list = tk.Listbox(left, height=12)
        self.library_list.pack(fill=tk.X, pady=(4, 6))
        self.library_list.bind("<<ListboxSelect>>", self._on_select_book)

        btn_row = ttk.Frame(left)
        btn_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(btn_row, text="Add Book", command=self._add_book).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Remove", command=self._remove_book).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Separator(left).pack(fill=tk.X, pady=6)

        ttk.Label(left, text="Search All Books", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        search_row = ttk.Frame(left)
        search_row.pack(fill=tk.X, pady=(4, 6))
        self.search_all_var = tk.StringVar()
        ttk.Entry(search_row, textvariable=self.search_all_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(search_row, text="Search", command=self._search_all_books).pack(side=tk.LEFT, padx=(6, 0))

        self.search_results_list = tk.Listbox(left, height=10)
        self.search_results_list.pack(fill=tk.BOTH, expand=True)
        self.search_results_list.bind("<Double-Button-1>", self._open_search_result)

        # Right panel: Reader + Highlights
        right = ttk.Frame(main_pane, padding=8)
        main_pane.add(right, weight=3)

        header = ttk.Frame(right)
        header.pack(fill=tk.X)
        self.book_title_var = tk.StringVar(value="No book selected")
        ttk.Label(header, textvariable=self.book_title_var, font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)

        toolbar = ttk.Frame(right)
        toolbar.pack(fill=tk.X, pady=(6, 6))

        self.highlight_color_var = tk.StringVar(value="yellow")
        ttk.Label(toolbar, text="Highlight:").pack(side=tk.LEFT)
        ttk.OptionMenu(toolbar, self.highlight_color_var, "yellow", "yellow", "lightgreen", "lightblue", "pink").pack(side=tk.LEFT, padx=(4, 10))
        ttk.Button(toolbar, text="Add Highlight", command=self._add_highlight).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Remove Highlight", command=self._remove_highlight).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Label(toolbar, text="Find in book:").pack(side=tk.LEFT, padx=(16, 4))
        self.search_book_var = tk.StringVar()
        ttk.Entry(toolbar, textvariable=self.search_book_var, width=30).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Find", command=self._search_current_book).pack(side=tk.LEFT, padx=(6, 0))

        reader_frame = ttk.Frame(right)
        reader_frame.pack(fill=tk.BOTH, expand=True)

        self.reader_text = tk.Text(reader_frame, wrap=tk.WORD, undo=False)
        self.reader_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.reader_text.bind("<Key>", lambda _e: "break")

        scrollbar = ttk.Scrollbar(reader_frame, orient=tk.VERTICAL, command=self.reader_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.reader_text.configure(yscrollcommand=scrollbar.set)

        highlights_frame = ttk.Frame(right)
        highlights_frame.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(highlights_frame, text="Highlights", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.highlights_list = tk.Listbox(highlights_frame, height=6)
        self.highlights_list.pack(fill=tk.X)
        self.highlights_list.bind("<Double-Button-1>", self._jump_to_highlight)

    def _refresh_library(self) -> None:
        self.library_list.delete(0, tk.END)
        self.book_index_map.clear()
        for book in storage.list_books(self.data):
            self.library_list.insert(tk.END, book.get("title", "Untitled"))
            self.book_index_map.append(book.get("id"))

    def _save_current_position(self) -> None:
        if not self.current_book_id:
            return
        book = storage.find_book(self.current_book_id, self.data)
        if not book:
            return
        position = self.reader_text.index("@0,0")
        book["last_position"] = position
        storage.update_book(book, self.data)

    def _on_select_book(self, _event: tk.Event) -> None:
        selection = self.library_list.curselection()
        if not selection:
            return
        idx = selection[0]
        book_id = self.book_index_map[idx]
        self._load_book(book_id)

    def _load_book(self, book_id: str) -> None:
        if self.current_book_id and self.current_book_id != book_id:
            self._save_current_position()

        book = storage.find_book(book_id, self.data)
        if not book:
            return

        path = storage.get_book_path(book)
        if not path.exists():
            messagebox.showerror("Missing File", "The book file was not found.")
            return

        content = path.read_text(encoding="utf-8", errors="ignore")

        self.reader_text.delete("1.0", tk.END)
        self.reader_text.insert(tk.END, content)
        self.reader_text.tag_delete("search_match")
        self.reader_text.tag_configure("search_match", background="#cde9ff")

        self.book_title_var.set(book.get("title", "Untitled"))
        self.current_book_id = book_id
        book["last_opened"] = storage.now_iso()

        self._apply_highlights(book)
        self._refresh_highlights_list(book)

        if book.get("last_position"):
            self.reader_text.see(book["last_position"])

        storage.update_book(book, self.data)

    def _apply_highlights(self, book: Dict[str, Any]) -> None:
        for tag in self.reader_text.tag_names():
            if tag.startswith("hl_"):
                self.reader_text.tag_delete(tag)

        for hl in book.get("highlights", []):
            tag = f"hl_{hl['id']}"
            self.reader_text.tag_add(tag, hl["start"], hl["end"])
            self.reader_text.tag_configure(tag, background=hl.get("color", "yellow"))

    def _refresh_highlights_list(self, book: Dict[str, Any]) -> None:
        self.highlights_list.delete(0, tk.END)
        self.highlight_index_map.clear()
        for hl in book.get("highlights", []):
            snippet = hl.get("text", "").replace("\n", " ")
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            self.highlights_list.insert(tk.END, snippet)
            self.highlight_index_map.append(hl.get("id"))

    def _add_book(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select a text or markdown file",
            filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            book = storage.add_book(file_path, self.data)
        except Exception as exc:  # pragma: no cover - UI error
            messagebox.showerror("Import failed", str(exc))
            return

        self._refresh_library()
        self._load_book(book["id"])

    def _remove_book(self) -> None:
        selection = self.library_list.curselection()
        if not selection:
            messagebox.showinfo("Remove", "Select a book to remove.")
            return
        idx = selection[0]
        book_id = self.book_index_map[idx]
        if not messagebox.askyesno("Remove", "Remove this book from the library?"):
            return
        storage.remove_book(book_id, self.data)
        self.current_book_id = None
        self.book_title_var.set("No book selected")
        self.reader_text.delete("1.0", tk.END)
        self.highlights_list.delete(0, tk.END)
        self._refresh_library()

    def _add_highlight(self) -> None:
        if not self.current_book_id:
            messagebox.showinfo("Highlight", "Open a book first.")
            return
        try:
            start = self.reader_text.index("sel.first")
            end = self.reader_text.index("sel.last")
        except tk.TclError:
            messagebox.showinfo("Highlight", "Select text to highlight.")
            return

        text = self.reader_text.get(start, end)
        book = storage.find_book(self.current_book_id, self.data)
        if not book:
            return

        highlight_id = uuid.uuid4().hex
        color = self.highlight_color_var.get()
        tag = f"hl_{highlight_id}"

        self.reader_text.tag_add(tag, start, end)
        self.reader_text.tag_configure(tag, background=color)

        book.setdefault("highlights", []).append({
            "id": highlight_id,
            "start": start,
            "end": end,
            "color": color,
            "text": text,
        })

        storage.update_book(book, self.data)
        self._refresh_highlights_list(book)

    def _remove_highlight(self) -> None:
        if not self.current_book_id:
            return
        selection = self.highlights_list.curselection()
        if not selection:
            messagebox.showinfo("Remove Highlight", "Select a highlight to remove.")
            return
        idx = selection[0]
        hl_id = self.highlight_index_map[idx]

        book = storage.find_book(self.current_book_id, self.data)
        if not book:
            return

        book["highlights"] = [h for h in book.get("highlights", []) if h.get("id") != hl_id]
        self.reader_text.tag_delete(f"hl_{hl_id}")
        storage.update_book(book, self.data)
        self._refresh_highlights_list(book)

    def _jump_to_highlight(self, _event: tk.Event) -> None:
        if not self.current_book_id:
            return
        selection = self.highlights_list.curselection()
        if not selection:
            return
        idx = selection[0]
        hl_id = self.highlight_index_map[idx]

        book = storage.find_book(self.current_book_id, self.data)
        if not book:
            return
        highlight = next((h for h in book.get("highlights", []) if h.get("id") == hl_id), None)
        if not highlight:
            return
        self.reader_text.see(highlight.get("start"))
        self.reader_text.tag_add("search_match", highlight.get("start"), highlight.get("end"))
        self.reader_text.after(1200, lambda: self.reader_text.tag_remove("search_match", "1.0", tk.END))

    def _search_current_book(self) -> None:
        query = self.search_book_var.get().strip()
        self.reader_text.tag_remove("search_match", "1.0", tk.END)
        if not query:
            return

        start = "1.0"
        while True:
            pos = self.reader_text.search(query, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.reader_text.tag_add("search_match", pos, end)
            start = end

    def _search_all_books(self) -> None:
        query = self.search_all_var.get().strip()
        self.search_results_list.delete(0, tk.END)
        self.search_results.clear()
        if not query:
            return

        for book in storage.list_books(self.data):
            path = storage.get_book_path(book)
            if not path.exists():
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for line_no, line in enumerate(content.splitlines(), start=1):
                if query.lower() in line.lower():
                    snippet = line.strip()
                    if len(snippet) > 80:
                        snippet = snippet[:77] + "..."
                    label = f"{book.get('title', 'Untitled')} - {line_no}: {snippet}"
                    self.search_results_list.insert(tk.END, label)
                    self.search_results.append({
                        "book_id": book.get("id"),
                        "line_no": line_no,
                    })

    def _open_search_result(self, _event: tk.Event) -> None:
        selection = self.search_results_list.curselection()
        if not selection:
            return
        idx = selection[0]
        result = self.search_results[idx]
        self._load_book(result["book_id"])
        line_no = result["line_no"]
        self.reader_text.see(f"{line_no}.0")
        self.reader_text.tag_add("search_match", f"{line_no}.0", f"{line_no}.end")
        self.reader_text.after(1200, lambda: self.reader_text.tag_remove("search_match", "1.0", tk.END))

    def _on_close(self) -> None:
        self._save_current_position()
        storage.save_library(self.data)
        self.destroy()


def main() -> None:
    app = LearningApp()
    app.mainloop()


if __name__ == "__main__":
    main()
