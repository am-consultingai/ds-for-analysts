"""The workshop's four models, set up the same way everywhere."""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from build_panel import feature_columns

NAMES = {"tree": "Decision tree", "logistic": "Logistic regression", "forest": "Random forest", "xgboost": "XGBoost"}


def make_xy(panel, spec):
    """Feature matrix with text columns one-hot encoded, and the label. Build it on the whole panel, then split,
    so every side has the same columns in the same order."""
    X = panel[feature_columns(spec)].copy()
    for c in X.columns:
        if not pd.api.types.is_numeric_dtype(X[c]) or pd.api.types.is_bool_dtype(X[c]):
            X[c] = X[c].astype(str)
    X = pd.get_dummies(X, dtype=float)
    return X.astype(float), panel["label"].to_numpy()


def make_model(name, settings, seed=0):
    """One model with the given settings. Missing values: filled with the median (XGBoost handles them itself)."""
    fill = SimpleImputer(strategy="median")
    if name == "logistic":
        return make_pipeline(fill, StandardScaler(), LogisticRegression(C=settings["C"], max_iter=3000))
    if name == "tree":
        return make_pipeline(fill, DecisionTreeClassifier(random_state=seed, **settings))
    if name == "forest":
        return make_pipeline(fill, RandomForestClassifier(n_estimators=300, random_state=seed, n_jobs=4, **settings))
    if name == "xgboost":
        return XGBClassifier(n_estimators=200, random_state=seed, n_jobs=4, eval_metric="logloss", **settings)
    raise ValueError(f"Unknown model: {name}")


def proba(model, X):
    return model.predict_proba(X)[:, 1]
