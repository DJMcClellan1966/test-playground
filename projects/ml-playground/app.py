"""Local-first ML Playground (Flask + SQLite)."""

from __future__ import annotations

import json
from typing import Dict, Any

from flask import Flask, render_template, request, redirect, url_for, flash

import db
import ml


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-key"

    db.init_db()

    @app.route("/")
    def index() -> str:
        dataset = ml.get_dataset_info()
        experiments = db.list_experiments(limit=8)
        return render_template(
            "index.html",
            dataset=dataset,
            experiments=experiments,
            models=ml.available_models(),
        )

    @app.route("/run", methods=["GET", "POST"])
    def run_experiment() -> str:
        if request.method == "POST":
            form = request.form
            model_name = form.get("model", "logreg")
            test_size = float(form.get("test_size", "0.2"))
            random_state = int(form.get("random_state", "42"))
            standardize = form.get("standardize", "off") == "on"
            note = (form.get("note") or "").strip()

            try:
                result = ml.run_experiment(
                    model_name=model_name,
                    test_size=test_size,
                    random_state=random_state,
                    standardize=standardize,
                )
            except ValueError as exc:
                flash(str(exc), "error")
                return redirect(url_for("run_experiment"))

            exp_id = db.add_experiment(
                model_name=model_name,
                params={
                    "test_size": test_size,
                    "random_state": random_state,
                    "standardize": standardize,
                },
                metrics=result["metrics"],
                artifacts={
                    "confusion_matrix": result["confusion_matrix"],
                    "target_names": result["target_names"],
                    "report": result["report"],
                },
                note=note,
            )

            return redirect(url_for("experiment_detail", experiment_id=exp_id))

        dataset = ml.get_dataset_info()
        return render_template(
            "run.html",
            dataset=dataset,
            models=ml.available_models(),
            defaults={"test_size": 0.2, "random_state": 42, "standardize": True},
        )

    @app.route("/experiment/<int:experiment_id>")
    def experiment_detail(experiment_id: int) -> str:
        exp = db.get_experiment(experiment_id)
        if not exp:
            flash("Experiment not found.", "error")
            return redirect(url_for("index"))
        return render_template("experiment.html", exp=exp)

    @app.template_filter("pretty_json")
    def pretty_json(value: Dict[str, Any]) -> str:
        return json.dumps(value, indent=2, sort_keys=True)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
