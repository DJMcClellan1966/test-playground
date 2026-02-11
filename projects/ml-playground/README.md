# ML Playground (Local-First)

Hands-on machine learning labs you can run locally. Start with the Iris dataset, run experiments, and compare results.

## Features
- Train baseline models on Iris (LogReg, SVM, KNN, Random Forest)
- Track experiments in SQLite
- See metrics, confusion matrix, and classification report

## Run

```powershell
cd projects\ml-playground
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Data
- SQLite DB at `data/experiments.db`

## Next ideas
- Add new datasets (Titanic, digits)
- Add a simple agent loop to suggest next runs
- Plot learning curves
