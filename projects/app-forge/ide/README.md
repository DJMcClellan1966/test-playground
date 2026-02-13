# App Forge IDE - Overview

This IDE aims to provide a VS Code-like experience for building and managing projects with:
- File browser (access to desktop folders)
- Code editor window (Monaco or Ace)
- Problems/terminal panel at the bottom
- Integrated chat/agent panel (App Forge agent)

## Architecture
- Backend: Flask or FastAPI (serves agent, file access, terminal, etc.)
- Frontend: React (Vite/CRA) or plain HTML+JS (for rapid prototyping)

## Core Features
- File explorer: Browse, open, create, delete, and rename files/folders
- Code editor: Syntax highlighting, editing, saving
- Problems/terminal: Show errors, run shell commands, display output
- Agent chat: Use App Forge agent for help, code generation, and Q&A

## Next Steps
- Scaffold backend and frontend
- Implement file browser and code editor
- Integrate agent chat and terminal
