"""
Naive Bayes classifier for App Forge.

Learns from the Good/Bad store to improve:
1. Template selection (which kernel/template fits a description)
2. Feature prediction (needs_auth, needs_data, etc.)
3. Component prediction (which components work well together)

Uses scikit-learn's MultinomialNB for text classification.
Falls back to regex-based detection when not enough training data.
"""

import json
import pickle
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter

try:
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn.preprocessing import MultiLabelBinarizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed. Using fallback mode.")

from build_memory import memory, BuildRecord


# =============================================================================
# Configuration
# =============================================================================

MIN_SAMPLES_FOR_TRAINING = 5  # Minimum good builds before using classifier
MODEL_DIR = Path(__file__).parent / "data" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Template Classifier
# =============================================================================

@dataclass
class ClassifierResult:
    """Result from a classification prediction."""
    prediction: str
    confidence: float
    probabilities: Dict[str, float] = field(default_factory=dict)
    used_ml: bool = False  # True if ML was used, False if fallback


class TemplateClassifier:
    """Predicts which template/kernel to use for a description."""
    
    def __init__(self):
        self.vectorizer: Optional[CountVectorizer] = None
        self.model: Optional[MultinomialNB] = None
        self.classes: List[str] = []
        self.is_trained = False
        self._load_model()
    
    def _model_path(self) -> Path:
        return MODEL_DIR / "template_classifier.pkl"
    
    def _load_model(self):
        """Load saved model if exists."""
        path = self._model_path()
        if path.exists() and SKLEARN_AVAILABLE:
            try:
                with open(path, "rb") as f:
                    data = pickle.load(f)
                    self.vectorizer = data["vectorizer"]
                    self.model = data["model"]
                    self.classes = data["classes"]
                    self.is_trained = True
            except Exception as e:
                print(f"Warning: Could not load template classifier: {e}")
    
    def _save_model(self):
        """Save model to disk."""
        if self.is_trained:
            with open(self._model_path(), "wb") as f:
                pickle.dump({
                    "vectorizer": self.vectorizer,
                    "model": self.model,
                    "classes": self.classes,
                }, f)
    
    def train(self, force: bool = False) -> Dict[str, Any]:
        """Train on good builds from memory.
        
        Returns training stats.
        """
        if not SKLEARN_AVAILABLE:
            return {"success": False, "error": "scikit-learn not installed"}
        
        # Get training data from good builds
        good_builds = memory.get_good_builds(limit=1000)
        
        if len(good_builds) < MIN_SAMPLES_FOR_TRAINING and not force:
            return {
                "success": False,
                "error": f"Need at least {MIN_SAMPLES_FOR_TRAINING} good builds, have {len(good_builds)}",
                "samples": len(good_builds),
            }
        
        if not good_builds:
            return {"success": False, "error": "No training data"}
        
        # Prepare training data
        descriptions = [b.description for b in good_builds]
        templates = [b.template_used for b in good_builds]
        
        # Count class distribution
        class_counts = Counter(templates)
        
        # Train vectorizer and model (no stop words for small datasets)
        self.vectorizer = CountVectorizer(
            lowercase=True,
            stop_words=None if len(good_builds) < 20 else "english",  # No stop words for small data
            ngram_range=(1, 2),  # Unigrams and bigrams
            max_features=500,
            min_df=1,  # Accept all terms
        )
        
        try:
            X = self.vectorizer.fit_transform(descriptions)
        except ValueError as e:
            return {"success": False, "error": f"Vectorization failed: {e}"}
        
        self.model = MultinomialNB(alpha=1.0)  # Laplace smoothing
        self.model.fit(X, templates)
        
        self.classes = list(self.model.classes_)
        self.is_trained = True
        self._save_model()
        
        return {
            "success": True,
            "samples": len(good_builds),
            "classes": self.classes,
            "class_distribution": dict(class_counts),
        }
    
    def predict(self, description: str) -> ClassifierResult:
        """Predict template for a description."""
        if not self.is_trained or not SKLEARN_AVAILABLE:
            # Fallback: return empty result, caller uses regex
            return ClassifierResult(
                prediction="",
                confidence=0.0,
                used_ml=False,
            )
        
        X = self.vectorizer.transform([description])
        
        # Get prediction and probabilities
        prediction = self.model.predict(X)[0]
        probas = self.model.predict_proba(X)[0]
        
        # Map probabilities to class names
        prob_dict = {cls: float(prob) for cls, prob in zip(self.classes, probas)}
        confidence = max(probas)
        
        return ClassifierResult(
            prediction=prediction,
            confidence=float(confidence),
            probabilities=prob_dict,
            used_ml=True,
        )


# =============================================================================
# Feature Classifier (multi-label)
# =============================================================================

class FeatureClassifier:
    """Predicts which features a description needs (multi-label)."""
    
    FEATURES = ["needs_auth", "needs_data", "needs_realtime", "needs_search", "needs_export"]
    
    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.model: Optional[OneVsRestClassifier] = None
        self.mlb: Optional[MultiLabelBinarizer] = None
        self.is_trained = False
        self._load_model()
    
    def _model_path(self) -> Path:
        return MODEL_DIR / "feature_classifier.pkl"
    
    def _load_model(self):
        """Load saved model if exists."""
        path = self._model_path()
        if path.exists() and SKLEARN_AVAILABLE:
            try:
                with open(path, "rb") as f:
                    data = pickle.load(f)
                    self.vectorizer = data["vectorizer"]
                    self.model = data["model"]
                    self.mlb = data["mlb"]
                    self.is_trained = True
            except Exception as e:
                print(f"Warning: Could not load feature classifier: {e}")
    
    def _save_model(self):
        """Save model to disk."""
        if self.is_trained:
            with open(self._model_path(), "wb") as f:
                pickle.dump({
                    "vectorizer": self.vectorizer,
                    "model": self.model,
                    "mlb": self.mlb,
                }, f)
    
    def _extract_features_from_build(self, build: BuildRecord) -> List[str]:
        """Extract feature labels from a build's answers and template."""
        features = []
        answers = build.answers or {}
        
        # From answers
        if answers.get("has_data") or answers.get("needs_data"):
            features.append("needs_data")
        if answers.get("needs_auth"):
            features.append("needs_auth")
        if answers.get("realtime"):
            features.append("needs_realtime")
        if answers.get("search"):
            features.append("needs_search")
        if answers.get("export"):
            features.append("needs_export")
        
        # From template (infer backwards)
        template = build.template_used or ""
        if "auth" in template:
            features.append("needs_auth")
        if "data" in template or "sql" in template.lower():
            features.append("needs_data")
        if "realtime" in template or "socket" in template.lower():
            features.append("needs_realtime")
        
        return list(set(features))  # Dedupe
    
    def train(self, force: bool = False) -> Dict[str, Any]:
        """Train on good builds."""
        if not SKLEARN_AVAILABLE:
            return {"success": False, "error": "scikit-learn not installed"}
        
        good_builds = memory.get_good_builds(limit=1000)
        
        if len(good_builds) < MIN_SAMPLES_FOR_TRAINING and not force:
            return {
                "success": False,
                "error": f"Need at least {MIN_SAMPLES_FOR_TRAINING} good builds",
                "samples": len(good_builds),
            }
        
        if not good_builds:
            return {"success": False, "error": "No training data"}
        
        # Prepare training data
        descriptions = [b.description for b in good_builds]
        feature_sets = [self._extract_features_from_build(b) for b in good_builds]
        
        # Filter out samples with no features
        valid_indices = [i for i, f in enumerate(feature_sets) if f]
        if len(valid_indices) < MIN_SAMPLES_FOR_TRAINING and not force:
            return {
                "success": False,
                "error": f"Only {len(valid_indices)} builds have feature labels",
            }
        
        if not valid_indices:
            return {"success": False, "error": "No builds with feature labels"}
        
        descriptions = [descriptions[i] for i in valid_indices]
        feature_sets = [feature_sets[i] for i in valid_indices]
        
        # Vectorize text (no stop words for small datasets)
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=None if len(descriptions) < 20 else "english",
            ngram_range=(1, 2),
            max_features=300,
            min_df=1,
        )
        
        try:
            X = self.vectorizer.fit_transform(descriptions)
        except ValueError as e:
            return {"success": False, "error": f"Vectorization failed: {e}"}
        
        # Binarize labels
        self.mlb = MultiLabelBinarizer(classes=self.FEATURES)
        y = self.mlb.fit_transform(feature_sets)
        
        # Train multi-label classifier
        self.model = OneVsRestClassifier(MultinomialNB(alpha=1.0))
        self.model.fit(X, y)
        
        self.is_trained = True
        self._save_model()
        
        # Count feature distribution
        feature_counts = Counter()
        for fs in feature_sets:
            feature_counts.update(fs)
        
        return {
            "success": True,
            "samples": len(descriptions),
            "feature_distribution": dict(feature_counts),
        }
    
    def predict(self, description: str) -> Dict[str, float]:
        """Predict feature probabilities for a description.
        
        Returns dict like {"needs_auth": 0.8, "needs_data": 0.2, ...}
        """
        if not self.is_trained or not SKLEARN_AVAILABLE:
            return {}
        
        X = self.vectorizer.transform([description])
        
        # Get probabilities for each feature
        try:
            probas = self.model.predict_proba(X)
            result = {}
            for i, feature in enumerate(self.FEATURES):
                # Each estimator returns proba for [0, 1]
                if hasattr(probas[i], '__len__') and len(probas[i]) > 0:
                    # Get probability of positive class (index 1)
                    if len(probas[i][0]) > 1:
                        result[feature] = float(probas[i][0][1])
                    else:
                        result[feature] = float(probas[i][0][0])
            return result
        except Exception:
            # Fallback to binary prediction
            preds = self.model.predict(X)
            return {f: 1.0 if preds[0][i] else 0.0 for i, f in enumerate(self.FEATURES)}


# =============================================================================
# Component Classifier (multi-label)
# =============================================================================

class ComponentClassifier:
    """Predicts which components work well for a description."""
    
    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.model: Optional[OneVsRestClassifier] = None
        self.mlb: Optional[MultiLabelBinarizer] = None
        self.known_components: List[str] = []
        self.is_trained = False
        self._load_model()
    
    def _model_path(self) -> Path:
        return MODEL_DIR / "component_classifier.pkl"
    
    def _load_model(self):
        """Load saved model if exists."""
        path = self._model_path()
        if path.exists() and SKLEARN_AVAILABLE:
            try:
                with open(path, "rb") as f:
                    data = pickle.load(f)
                    self.vectorizer = data["vectorizer"]
                    self.model = data["model"]
                    self.mlb = data["mlb"]
                    self.known_components = data["known_components"]
                    self.is_trained = True
            except Exception as e:
                print(f"Warning: Could not load component classifier: {e}")
    
    def _save_model(self):
        """Save model to disk."""
        if self.is_trained:
            with open(self._model_path(), "wb") as f:
                pickle.dump({
                    "vectorizer": self.vectorizer,
                    "model": self.model,
                    "mlb": self.mlb,
                    "known_components": self.known_components,
                }, f)
    
    def train(self, force: bool = False) -> Dict[str, Any]:
        """Train on good builds."""
        if not SKLEARN_AVAILABLE:
            return {"success": False, "error": "scikit-learn not installed"}
        
        good_builds = memory.get_good_builds(limit=1000)
        
        # Filter builds that have components
        builds_with_components = [b for b in good_builds if b.components]
        
        if len(builds_with_components) < MIN_SAMPLES_FOR_TRAINING and not force:
            return {
                "success": False,
                "error": f"Need at least {MIN_SAMPLES_FOR_TRAINING} builds with components",
                "samples": len(builds_with_components),
            }
        
        if not builds_with_components:
            return {"success": False, "error": "No training data with components"}
        
        # Get all unique components
        all_components = set()
        for b in builds_with_components:
            all_components.update(b.components)
        self.known_components = sorted(all_components)
        
        # Prepare training data
        descriptions = [b.description for b in builds_with_components]
        component_sets = [b.components for b in builds_with_components]
        
        # Vectorize text (no stop words for small datasets)
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words=None if len(descriptions) < 20 else "english",
            ngram_range=(1, 2),
            max_features=300,
            min_df=1,
        )
        
        try:
            X = self.vectorizer.fit_transform(descriptions)
        except ValueError as e:
            return {"success": False, "error": f"Vectorization failed: {e}"}
        
        # Binarize component labels
        self.mlb = MultiLabelBinarizer(classes=self.known_components)
        y = self.mlb.fit_transform(component_sets)
        
        # Train classifier
        self.model = OneVsRestClassifier(MultinomialNB(alpha=1.0))
        self.model.fit(X, y)
        
        self.is_trained = True
        self._save_model()
        
        # Count component distribution
        comp_counts = Counter()
        for cs in component_sets:
            comp_counts.update(cs)
        
        return {
            "success": True,
            "samples": len(builds_with_components),
            "known_components": self.known_components,
            "component_distribution": dict(comp_counts),
        }
    
    def predict(self, description: str, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Predict components for a description.
        
        Returns list of (component, probability) tuples above threshold.
        """
        if not self.is_trained or not SKLEARN_AVAILABLE:
            return []
        
        if not self.known_components:
            return []
        
        X = self.vectorizer.transform([description])
        
        try:
            # Get predictions
            preds = self.model.predict(X)
            results = []
            
            # Handle single sample prediction
            if hasattr(preds, 'shape') and len(preds.shape) > 1:
                pred_row = preds[0]
            else:
                pred_row = preds
            
            # Try to get probabilities
            try:
                probas = self.model.predict_proba(X)
                for i, comp in enumerate(self.known_components):
                    if i < len(probas):
                        # Each estimator in OneVsRest returns probas for its binary classification
                        est_proba = probas[i]
                        if hasattr(est_proba, '__len__') and len(est_proba) > 0:
                            # probas[i] is shape (n_samples, 2) for binary
                            if hasattr(est_proba[0], '__len__') and len(est_proba[0]) > 1:
                                prob = float(est_proba[0][1])  # Probability of positive class
                            else:
                                prob = float(est_proba[0])
                        else:
                            prob = float(est_proba)
                        if prob >= threshold:
                            results.append((comp, prob))
            except Exception:
                # Fallback to binary predictions
                for i, comp in enumerate(self.known_components):
                    if i < len(pred_row) and pred_row[i]:
                        results.append((comp, 1.0))
            
            return sorted(results, key=lambda x: -x[1])
        except Exception as e:
            # Complete fallback
            return []


# =============================================================================
# Combined Classifier Manager
# =============================================================================

class AppClassifier:
    """Unified interface for all classifiers."""
    
    def __init__(self):
        self.template_clf = TemplateClassifier()
        self.feature_clf = FeatureClassifier()
        self.component_clf = ComponentClassifier()
    
    def train_all(self, force: bool = False) -> Dict[str, Any]:
        """Train all classifiers."""
        return {
            "template": self.template_clf.train(force),
            "feature": self.feature_clf.train(force),
            "component": self.component_clf.train(force),
        }
    
    def predict(self, description: str) -> Dict[str, Any]:
        """Get all predictions for a description."""
        template_result = self.template_clf.predict(description)
        feature_probs = self.feature_clf.predict(description)
        component_probs = self.component_clf.predict(description)
        
        return {
            "template": {
                "prediction": template_result.prediction,
                "confidence": template_result.confidence,
                "probabilities": template_result.probabilities,
                "used_ml": template_result.used_ml,
            },
            "features": feature_probs,
            "components": component_probs,
            "sklearn_available": SKLEARN_AVAILABLE,
        }
    
    def status(self) -> Dict[str, Any]:
        """Get training status of all classifiers."""
        return {
            "sklearn_available": SKLEARN_AVAILABLE,
            "template_trained": self.template_clf.is_trained,
            "feature_trained": self.feature_clf.is_trained,
            "component_trained": self.component_clf.is_trained,
            "template_classes": self.template_clf.classes,
            "known_components": self.component_clf.known_components,
        }


# =============================================================================
# Module-level instance
# =============================================================================

classifier = AppClassifier()


# =============================================================================
# CLI for testing
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "train":
        print("Training classifiers...")
        results = classifier.train_all(force="--force" in sys.argv)
        print(json.dumps(results, indent=2))
    
    elif len(sys.argv) > 1 and sys.argv[1] == "predict":
        desc = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "a todo list app"
        print(f"Predicting for: {desc}")
        results = classifier.predict(desc)
        print(json.dumps(results, indent=2))
    
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps(classifier.status(), indent=2))
    
    else:
        print("Usage:")
        print("  python classifier.py train [--force]  - Train on good builds")
        print("  python classifier.py predict <desc>   - Predict for description")
        print("  python classifier.py status           - Show training status")
