# Learning App (MVP)

A local, offline learning reader with highlights and search.

## Features
- Import TXT/Markdown files
- Reader with saved reading position
- Highlights with color tags
- Search within a book
- Search across all books

## Run

```powershell
cd projects\learning-app
python app.py
```

## Data
- Library and highlights stored in `data/library.json`
- Imported files copied to `data/books/`

## Notes
- Highlights are stored by text positions (line.column). If the source file changes, highlights may shift.
