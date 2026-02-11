"""ML utilities for running baseline Iris experiments."""

from __future__ import annotations

from typing import Dict, Any, List

from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier


def available_models() -> List[Dict[str, str]]:
    return [
        {"id": "logreg", "label": "Logistic Regression"},
        {"id": "svm_rbf", "label": "SVM (RBF)"},
        {"id": "knn", "label": "KNN (k=5)"},
        {"id": "rf", "label": "Random Forest"},
    ]


def get_dataset_info() -> Dict[str, Any]:
    iris = load_iris()
    return {
        "name": "Iris",
        "samples": int(iris.data.shape[0]),
        "features": int(iris.data.shape[1]),
        "classes": list(iris.target_names),
        "feature_names": list(iris.feature_names),
        "description": "Classic 3-class classification dataset.",
    }


def _build_model(model_name: str, standardize: bool) -> Pipeline:
    if model_name == "logreg":
        model = LogisticRegression(max_iter=250)
        needs_scaling = True
    elif model_name == "svm_rbf":
        model = SVC(kernel="rbf", gamma="scale", C=1.0)
        needs_scaling = True
    elif model_name == "knn":
        model = KNeighborsClassifier(n_neighbors=5)
        needs_scaling = True
    elif model_name == "rf":
        model = RandomForestClassifier(n_estimators=200, random_state=42)
        needs_scaling = False
    else:
        raise ValueError("Unknown model selection.")

    if standardize and needs_scaling:
        return Pipeline([("scaler", StandardScaler()), ("model", model)])

    return Pipeline([("model", model)])


def run_experiment(
    *,
    model_name: str,
    test_size: float,
    random_state: int,
    standardize: bool,
) -> Dict[str, Any]:
    if not (0.1 <= test_size <= 0.5):
        raise ValueError("Test size must be between 0.1 and 0.5.")

    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data,
        iris.target,
        test_size=test_size,
        random_state=random_state,
        stratify=iris.target,
    )

    model = _build_model(model_name, standardize)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    report = classification_report(y_test, preds, target_names=iris.target_names, output_dict=True)
    cm = confusion_matrix(y_test, preds).tolist()

    metrics = {
        "accuracy": round(float(acc), 4),
        "precision_macro": round(float(report["macro avg"]["precision"]), 4),
        "recall_macro": round(float(report["macro avg"]["recall"]), 4),
        "f1_macro": round(float(report["macro avg"]["f1-score"]), 4),
    }

    return {
        "metrics": metrics,
        "confusion_matrix": cm,
        "target_names": list(iris.target_names),
        "report": report,
    }
