"""The workshop's models, set up the same way everywhere: notebooks, skills and the validator."""
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from build_panel import feature_columns


def make_xy(panel, spec, drop=()):
    """Feature matrix with text columns one-hot encoded, and the label.

    Use ws.xy() or reindex the test columns to the training columns, so both sides match.
    """
    cols = [c for c in feature_columns(panel, spec) if c not in drop]
    X = panel[cols].copy()
    for c in X.columns:
        if not pd.api.types.is_numeric_dtype(X[c]) or pd.api.types.is_bool_dtype(X[c]):
            X[c] = X[c].astype(str)
    X = pd.get_dummies(X, dtype=float)
    return X.astype(float), panel["label"].to_numpy()


def logistic(C=1.0):
    """Missing values filled with the median, features scaled, L2 regularisation."""
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                         LogisticRegression(C=C, max_iter=3000))


def xgboost(seed=0, **kw):
    params = dict(n_estimators=300, learning_rate=0.05, max_depth=4, subsample=0.8, colsample_bytree=0.8,
                  min_child_weight=5, reg_lambda=1.0, tree_method="hist", n_jobs=4, random_state=seed,
                  eval_metric="logloss")
    params.update(kw)
    return XGBClassifier(**params)


def proba(model, X):
    return model.predict_proba(X)[:, 1]
