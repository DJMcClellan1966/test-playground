"""Socratic Learner GUI (Tkinter)."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from socrates import Socrates


class SocratesGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Socratic Learner")
        self.geometry("900x700")

        self.socrates: Optional[Socrates] = None
        self.is_busy = False
        self.knowledge_path: Optional[str] = None
        self.timeout_job: Optional[str] = None

        self._build_ui()
        self._load_default_knowledge()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Knowledge file:").pack(side=tk.LEFT)
        self.knowledge_var = tk.StringVar()
        self.knowledge_combo = ttk.Combobox(top, textvariable=self.knowledge_var, width=60, state="readonly")
        self.knowledge_combo.pack(side=tk.LEFT, padx=(6, 6))
        ttk.Button(top, text="Browse", command=self._browse_knowledge).pack(side=tk.LEFT)
        ttk.Button(top, text="Load", command=self._load_selected_knowledge).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(top, text="Export", command=self._export_history).pack(side=tk.LEFT, padx=(6, 0))

        options = ttk.Frame(self, padding=(8, 0, 8, 0))
        options.pack(fill=tk.X)
        self.auto_reset_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options, text="New question (auto reset)", variable=self.auto_reset_var).pack(anchor="w")

        self.status_var = tk.StringVar(value="No knowledge loaded.")
        ttk.Label(self, textvariable=self.status_var, padding=8).pack(anchor="w")

        self.banner_var = tk.StringVar(value="")
        self.banner_label = ttk.Label(self, textvariable=self.banner_var, foreground="#b00020", padding=(8, 0, 8, 6))
        self.banner_label.pack(anchor="w")

        self.chat = tk.Text(self, wrap=tk.WORD, state="disabled")
        self.chat.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        bottom = ttk.Frame(self, padding=8)
        bottom.pack(fill=tk.X)

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(bottom, textvariable=self.input_var)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", lambda _e: self._on_ask())

        ttk.Button(bottom, text="Ask", command=self._on_ask).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(bottom, text="Hint", command=self._on_hint).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(bottom, text="Reveal", command=self._on_reveal).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(bottom, text="Reset", command=self._on_reset).pack(side=tk.LEFT, padx=(6, 0))

        self.spinner = ttk.Progressbar(bottom, mode="indeterminate", length=120)
        self.spinner.pack(side=tk.LEFT, padx=(10, 0))

    def _load_default_knowledge(self) -> None:
        knowledge_dir = Path(__file__).resolve().parent / "knowledge"
        files = sorted(knowledge_dir.glob("*_knowledge.json"))
        if files:
            self.knowledge_combo["values"] = [str(f) for f in files]
            self.knowledge_var.set(str(files[0]))
            self._load_selected_knowledge()
        else:
            self.knowledge_combo["values"] = []

    def _browse_knowledge(self) -> None:
        path = filedialog.askopenfilename(
            title="Select a knowledge JSON file",
            filetypes=[("Knowledge JSON", "*_knowledge.json"), ("JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        values = list(self.knowledge_combo["values"])
        if path not in values:
            values.append(path)
            self.knowledge_combo["values"] = values
        self.knowledge_var.set(path)
        self._load_selected_knowledge()

    def _load_selected_knowledge(self) -> None:
        path = self.knowledge_var.get().strip()
        if not path:
            return
        try:
            self.socrates = Socrates(path)
            self.knowledge_path = path
            self.status_var.set(f"Loaded: {path}")
            self._set_banner("")
            self._append_system("Knowledge loaded. Ask a question to begin.")
        except Exception as exc:
            messagebox.showerror("Load failed", str(exc))

    def _set_banner(self, text: str) -> None:
        self.banner_var.set(text)

    def _set_busy(self, busy: bool) -> None:
        self.is_busy = busy
        state = "disabled" if busy else "normal"
        self.input_entry.configure(state=state)
        for child in self.input_entry.master.winfo_children():
            if isinstance(child, ttk.Button):
                child.configure(state=state)
        if busy:
            self.status_var.set("Thinking...")
            self.spinner.start(10)
            self._schedule_timeout_warning()
        else:
            if self.knowledge_path:
                self.status_var.set(f"Loaded: {self.knowledge_path}")
            else:
                self.status_var.set("No knowledge loaded.")
            self.spinner.stop()
            self._cancel_timeout_warning()

    def _append_message(self, role: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert(tk.END, f"{role}: {text}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see(tk.END)

    def _append_system(self, text: str) -> None:
        self._append_message("System", text)

    def _schedule_timeout_warning(self) -> None:
        self._cancel_timeout_warning()

        def warn() -> None:
            if self.is_busy:
                self._set_banner("This is taking longer than usual. The model may be busy or timed out.")

        self.timeout_job = self.after(45000, warn)

    def _cancel_timeout_warning(self) -> None:
        if self.timeout_job is not None:
            try:
                self.after_cancel(self.timeout_job)
            except Exception:
                pass
            self.timeout_job = None

    def _run_async(self, func, *args) -> None:
        def runner() -> None:
            try:
                result = func(*args)
                self.after(0, lambda: self._append_message("Socrates", result))
            except Exception as exc:
                def show_error() -> None:
                    self._set_banner("Request failed. Check Ollama and try again.")
                    messagebox.showerror("Error", str(exc))

                self.after(0, show_error)
            finally:
                self.after(0, lambda: self._set_busy(False))

        self._set_busy(True)
        threading.Thread(target=runner, daemon=True).start()

    def _on_ask(self) -> None:
        if self.is_busy:
            return
        if not self.socrates:
            messagebox.showinfo("No knowledge", "Load a knowledge file first.")
            return
        question = self.input_var.get().strip()
        if not question:
            return
        if self.auto_reset_var.get() and self.socrates.dialogue_history:
            self._on_reset()
        self._set_banner("")
        self.input_var.set("")
        self._append_message("You", question)

        if self.socrates.dialogue_history:
            self._run_async(self.socrates.continue_dialogue, question)
        else:
            self._run_async(self.socrates.respond, question)

    def _on_hint(self) -> None:
        if self.is_busy:
            return
        if not self.socrates:
            messagebox.showinfo("No knowledge", "Load a knowledge file first.")
            return
        self._set_banner("")
        self._append_message("You", "/hint")
        self._run_async(self.socrates.give_hint)

    def _on_reveal(self) -> None:
        if self.is_busy:
            return
        if not self.socrates:
            messagebox.showinfo("No knowledge", "Load a knowledge file first.")
            return
        self._set_banner("")
        self._append_message("You", "/reveal")
        self._run_async(self.socrates.reveal_answer)

    def _on_reset(self) -> None:
        if not self.socrates:
            return
        self.socrates.reset_dialogue()
        self.chat.configure(state="normal")
        self.chat.delete("1.0", tk.END)
        self.chat.configure(state="disabled")
        self._set_banner("")
        self._append_system("Dialogue reset.")

    def _export_history(self) -> None:
        if not self.socrates or not self.socrates.dialogue_history:
            messagebox.showinfo("Nothing to export", "No dialogue to export yet.")
            return

        default_name = f"socratic-dialogue-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        path = filedialog.asksaveasfilename(
            title="Export dialogue",
            defaultextension=".md",
            initialfile=default_name,
            filetypes=[("Markdown", "*.md"), ("JSON", "*.json")],
        )
        if not path:
            return

        try:
            if path.lower().endswith(".json"):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.socrates.dialogue_history, f, indent=2)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("# Socratic Dialogue Export\n\n")
                    if self.knowledge_path:
                        f.write(f"Knowledge: {self.knowledge_path}\n\n")
                    for entry in self.socrates.dialogue_history:
                        role = entry.get("role", "")
                        content = entry.get("content", "")
                        f.write(f"**{role.title()}**:\n\n{content}\n\n---\n\n")
            messagebox.showinfo("Exported", f"Saved to {path}")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))


def main() -> None:
    app = SocratesGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
