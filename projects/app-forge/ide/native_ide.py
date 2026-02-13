import sys
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileSystemModel, QTreeView, QPlainTextEdit, QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel
)
from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtGui import QFont
# --- AGENT/IMAGINATION SYSTEM ---
import importlib.util
import traceback
# --- GIT UTILS ---
from git_utils import run_git_command
class IDEMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App Forge Native IDE")
        self.resize(1200, 800)
        self._init_ui()
        self.current_file = None

    def _init_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        # File browser
        self.model = QFileSystemModel()
        self.model.setRootPath(os.path.expanduser("~"))
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(os.path.expanduser("~")))
        self.tree.setColumnWidth(0, 250)
        self.tree.clicked.connect(self.open_file)
        # Editor
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        # Bottom panel (problems/terminal)
        self.bottom_split = QSplitter(Qt.Horizontal)
        self.problems = QPlainTextEdit()
        self.problems.setReadOnly(True)
        self.problems.setMaximumHeight(150)
        self.problems.setPlaceholderText("Problems/Errors")
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setMaximumHeight(150)
        self.terminal.setPlaceholderText("Terminal Output")
        self.terminal_input = QLineEdit()
        self.terminal_input.setPlaceholderText("Enter command and press Enter")
        self.terminal_input.returnPressed.connect(self.run_terminal_command)
        terminal_layout = QVBoxLayout()
        terminal_layout.addWidget(self.terminal)
        terminal_layout.addWidget(self.terminal_input)
        terminal_widget = QWidget()
        terminal_widget.setLayout(terminal_layout)
        self.bottom_split.addWidget(self.problems)
        self.bottom_split.addWidget(terminal_widget)
        self.bottom_split.setSizes([300, 500])
        # Agent chat
        chat_layout = QVBoxLayout()
        self.chat_display = QPlainTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_input = QLineEdit()
        self.chat_input.returnPressed.connect(self.send_chat)
        chat_layout.addWidget(QLabel("Agent Chat"))
        chat_layout.addWidget(self.chat_display)
        chat_layout.addWidget(self.chat_input)
        chat_widget = QWidget()
        chat_widget.setLayout(chat_layout)
        chat_widget.setMaximumWidth(300)
        # Layouts
        main_split = QSplitter(Qt.Vertical)
        main_split.addWidget(self.editor)
        main_split.addWidget(self.bottom_split)
        main_split.setSizes([600, 150])
        splitter.addWidget(self.tree)
        splitter.addWidget(main_split)
        splitter.addWidget(chat_widget)
        splitter.setSizes([250, 800, 300])
        self.setCentralWidget(splitter)

    def open_file(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.editor.setPlainText(f.read())
            self.current_file = path
            self.check_problems(path)
        else:
            self.current_file = None

    def check_problems(self, path):
        # Simple syntax check for Python files
        if path.endswith('.py'):
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    src = f.read()
                compile(src, path, 'exec')
                self.problems.setPlainText('No syntax errors.')
            except Exception as e:
                self.problems.setPlainText(str(e))
        else:
            self.problems.setPlainText('')

    def run_terminal_command(self):
        import subprocess
        cmd = self.terminal_input.text()
        if not cmd:
            return
        self.terminal.appendPlainText(f"> {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(self.current_file) if self.current_file else None)
            output = result.stdout + result.stderr
            self.terminal.appendPlainText(output)
        except Exception as e:
            self.terminal.appendPlainText(str(e))
        self.terminal_input.clear()

    def send_chat(self):
        text = self.chat_input.text()
        if text:
            self.chat_display.appendPlainText(f"You: {text}")
            # AGENT LOGIC: Use imagination system for creative suggestions
            try:
                sys_path = sys.path.copy()
                backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend'))
                if backend_path not in sys.path:
                    sys.path.insert(0, backend_path)
                spec = importlib.util.spec_from_file_location("imagination", os.path.join(backend_path, "imagination.py"))
                imagination = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(imagination)
                creative_system = getattr(imagination, "creative_system", None)
                if creative_system:
                    result = creative_system.explore_idea(text)
                    suggestions = result.get('suggestions', [])
                    if suggestions:
                        self.chat_display.appendPlainText("Agent: Creative suggestions:")
                        for s in suggestions:
                            self.chat_display.appendPlainText(f"  - {s}")
                    else:
                        self.chat_display.appendPlainText("Agent: No creative suggestions found.")
                else:
                    self.chat_display.appendPlainText("Agent: Imagination system not available.")
                sys.path = sys_path
            except Exception as e:
                self.chat_display.appendPlainText("Agent: Error in imagination system.")
                self.chat_display.appendPlainText(traceback.format_exc())
            self.chat_input.clear()

    def run_terminal_command(self):
        import subprocess
        cmd = self.terminal_input.text()
        if not cmd:
            return
        self.terminal.appendPlainText(f"> {cmd}")
        # GIT INTEGRATION: If command starts with 'git', use run_git_command
        if cmd.strip().startswith('git'):
            output = run_git_command(cmd.strip().split()[1:], cwd=os.path.dirname(self.current_file) if self.current_file else None)
            self.terminal.appendPlainText(output)
            self.terminal_input.clear()
            return
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(self.current_file) if self.current_file else None)
            output = result.stdout + result.stderr
            self.terminal.appendPlainText(output)
        except Exception as e:
            self.terminal.appendPlainText(str(e))
        self.terminal_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = IDEMainWindow()
    win.show()
    sys.exit(app.exec_())
