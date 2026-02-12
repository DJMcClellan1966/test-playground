"""Preview server manager - runs generated apps in a subprocess for live testing."""

import os
import sys
import time
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class PreviewServer:
    """Manages a subprocess running the user's generated Flask app."""

    PREVIEW_PORT = 5001

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.preview_dir: Optional[Path] = None

    def _write_files(self, files: dict) -> Path:
        """Write generated files to a temp directory.
        
        Args:
            files: Dict mapping file paths (e.g., 'app.py', 'models.py', 'templates/index.html')
                   to file contents.
        """
        # Use a fixed preview dir so we can clean up easily
        preview_dir = Path(tempfile.gettempdir()) / "appforge_preview"
        if preview_dir.exists():
            shutil.rmtree(preview_dir, ignore_errors=True)

        preview_dir.mkdir(parents=True, exist_ok=True)
        (preview_dir / "templates").mkdir(exist_ok=True)
        (preview_dir / "static").mkdir(exist_ok=True)

        # Write all files from the dict
        for file_path, content in files.items():
            target = preview_dir / file_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        return preview_dir

    def _patch_port(self, app_py: str) -> str:
        """Replace port 5000 with the preview port so it doesn't clash."""
        return app_py.replace("port=5000", f"port={self.PREVIEW_PORT}")

    def start(self, files: dict) -> dict:
        """Write files and start the preview Flask server.
        
        Args:
            files: Dict mapping file paths to contents. Must include 'app.py'.
        """
        # Kill any existing preview first
        self.stop()

        # Patch the port in app.py
        patched_files = files.copy()
        if 'app.py' in patched_files:
            patched_app = self._patch_port(patched_files['app.py'])
            # Also disable debug/reloader in preview to avoid issues
            patched_app = patched_app.replace("debug=True", "debug=False")
            patched_files['app.py'] = patched_app

        self.preview_dir = self._write_files(patched_files)

        try:
            # Use the same Python that's running App Forge
            python = sys.executable

            # Install requirements (quick, most are likely cached)
            req_file = self.preview_dir / "requirements.txt"
            if req_file.exists():
                subprocess.run(
                    [python, "-m", "pip", "install", "-q", "-r", str(req_file)],
                    capture_output=True,
                    timeout=30,
                )

            # Kill anything already on the preview port
            if os.name == 'nt':
                subprocess.run(
                    f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :{self.PREVIEW_PORT}\') do taskkill /F /PID %a',
                    shell=True, capture_output=True,
                )

            # Build a clean environment so werkzeug doesn't inherit
            # the parent's WERKZEUG_SERVER_FD (causes WinError 10038)
            env = os.environ.copy()
            env.pop("WERKZEUG_SERVER_FD", None)
            env.pop("WERKZEUG_RUN_MAIN", None)

            # Start the preview server
            self.process = subprocess.Popen(
                [python, "app.py"],
                cwd=str(self.preview_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
            )

            # Give it a moment to start
            time.sleep(1.5)

            # Check it didn't crash immediately
            if self.process.poll() is not None:
                stderr = self.process.stderr.read().decode() if self.process.stderr else ""
                return {
                    "success": False,
                    "error": f"Preview server crashed on startup:\n{stderr}",
                }

            return {
                "success": True,
                "preview_url": f"http://127.0.0.1:{self.PREVIEW_PORT}",
                "preview_dir": str(self.preview_dir),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self):
        """Stop the running preview server."""
        if self.process and self.process.poll() is None:
            try:
                if os.name == 'nt':
                    # Windows: kill process tree
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                        capture_output=True,
                    )
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

        self.process = None

        # Clean up temp files
        if self.preview_dir and self.preview_dir.exists():
            try:
                shutil.rmtree(self.preview_dir, ignore_errors=True)
            except Exception:
                pass
            self.preview_dir = None

    @property
    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None


# Singleton
preview = PreviewServer()
