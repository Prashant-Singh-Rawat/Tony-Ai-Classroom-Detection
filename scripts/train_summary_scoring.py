"""
scripts/train_summary_scoring.py — Train Educational Summary Quality Regressor
=============================================================================
Predicts 'content' and 'wording' scores from student summary texts.
Uses TF-IDF n-grams + text surface statistics with MultiOutput Ridge Regression.
Evaluates on held-out test split (1,075 summaries) using MAE, RMSE, and R2.
Saves model to models/checkpoints/summary_scoring/summary_regressor.joblib.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "datasets" / "kaggle" / "commonlit_summaries"
CHECKPOINT_DIR = REPO_ROOT / "models" / "checkpoints" / "summary_scoring"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
np.random.seed(SEED)


def extract_text_stats(texts: list[str]) -> np.ndarray:
    """Extracts simple stylistic and length features."""
    features = []
    for t in texts:
        words = t.split()
        n_words = len(words)
        n_chars = len(t)
        n_sentences = max(1, t.count(".") + t.count("!") + t.count("?"))
        avg_word_len = n_chars / max(1, n_words)
        avg_sent_len = n_words / n_sentences
        features.append([n_words, n_chars, n_sentences, avg_word_len, avg_sent_len])
    return np.array(features, dtype=np.float32)


def main():
    train_csv = DATA_DIR / "summaries_train.csv"
    if not train_csv.is_file():
        logger.error("summaries_train.csv not found in %s", DATA_DIR)
        return

    logger.info("Loading CommonLit Student Summaries...")
    df = pd.read_csv(train_csv)
    logger.info("Total dataset rows: %d. Target columns: ['content', 'wording']", len(df))

    # Stratified 70/15/15 split
    df["content_bin"] = pd.qcut(df["content"], q=5, labels=False)
    df["strata"] = df["prompt_id"].astype(str) + "_" + df["content_bin"].astype(str)

    train_df, temp_df = train_test_split(df, test_size=0.30, random_state=SEED, stratify=df["strata"])
    val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=SEED, stratify=temp_df["strata"])

    logger.info("Splits: Train=%d, Val=%d, Test=%d", len(train_df), len(val_df), len(test_df))

    # Features: TF-IDF on student text
    tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english", sublinear_tf=True)

    X_train_text = tfidf.fit_transform(train_df["text"].values)
    X_val_text = tfidf.transform(val_df["text"].values)
    X_test_text = tfidf.transform(test_df["text"].values)

    # Stylistic features
    scaler = StandardScaler()
    X_train_stats = scaler.fit_transform(extract_text_stats(train_df["text"].tolist()))
    X_val_stats = scaler.transform(extract_text_stats(val_df["text"].tolist()))
    X_test_stats = scaler.transform(extract_text_stats(test_df["text"].tolist()))

    from scipy.sparse import hstack
    X_train = hstack([X_train_text, X_train_stats]).tocsr()
    X_val = hstack([X_val_text, X_val_stats]).tocsr()
    X_test = hstack([X_test_text, X_test_stats]).tocsr()

    y_train = train_df[["content", "wording"]].values
    y_val = val_df[["content", "wording"]].values
    y_test = test_df[["content", "wording"]].values

    # Model: MultiOutput Ridge Regressor
    logger.info("Training MultiOutput Ridge Regressor...")
    t0 = time.perf_counter()
    regressor = MultiOutputRegressor(Ridge(alpha=2.0))
    regressor.fit(X_train, y_train)
    train_duration = time.perf_counter() - t0

    # Validation evaluation
    val_preds = regressor.predict(X_val)
    val_content_mae = mean_absolute_error(y_val[:, 0], val_preds[:, 0])
    val_wording_mae = mean_absolute_error(y_val[:, 1], val_preds[:, 1])
    logger.info("Validation MAE — Content: %.4f | Wording: %.4f | Mean: %.4f",
                val_content_mae, val_wording_mae, (val_content_mae + val_wording_mae) / 2)

    # Held-out Test evaluation
    t_eval_start = time.perf_counter()
    test_preds = regressor.predict(X_test)
    eval_time = (time.perf_counter() - t_eval_start) / len(test_df)

    content_mae = float(mean_absolute_error(y_test[:, 0], test_preds[:, 0]))
    wording_mae = float(mean_absolute_error(y_test[:, 1], test_preds[:, 1]))
    content_rmse = float(np.sqrt(mean_squared_error(y_test[:, 0], test_preds[:, 0])))
    wording_rmse = float(np.sqrt(mean_squared_error(y_test[:, 1], test_preds[:, 1])))
    content_r2 = float(r2_score(y_test[:, 0], test_preds[:, 0]))
    wording_r2 = float(r2_score(y_test[:, 1], test_preds[:, 1]))

    mean_mae = (content_mae + wording_mae) / 2
    mean_rmse = (content_rmse + wording_rmse) / 2
    mean_r2 = (content_r2 + wording_r2) / 2
    latency_ms = round(eval_time * 1000.0, 3)

    logger.info("================ TEST EVALUATION RESULTS ================")
    logger.info("Test Samples: %d", len(test_df))
    logger.info("Content — MAE: %.4f | RMSE: %.4f | R²: %.4f", content_mae, content_rmse, content_r2)
    logger.info("Wording — MAE: %.4f | RMSE: %.4f | R²: %.4f", wording_mae, wording_rmse, wording_r2)
    logger.info("Overall — MAE: %.4f | RMSE: %.4f | R²: %.4f", mean_mae, mean_rmse, mean_r2)
    logger.info("Inference Latency: %.3f ms / summary", latency_ms)

    # Save Pipeline artifacts
    pipeline_bundle = {
        "tfidf": tfidf,
        "scaler": scaler,
        "regressor": regressor,
        "targets": ["content", "wording"],
    }
    model_path = CHECKPOINT_DIR / "summary_regressor.joblib"
    joblib.dump(pipeline_bundle, model_path)
    logger.info("Saved regressor model to %s", model_path)

    metrics_payload = {
        "dataset": "CommonLit Student Summaries",
        "task": "Educational Summary Quality Regression",
        "targets": ["content", "wording"],
        "test_samples": len(test_df),
        "content_metrics": {
            "mae": round(content_mae, 4),
            "rmse": round(content_rmse, 4),
            "r2": round(content_r2, 4),
        },
        "wording_metrics": {
            "mae": round(wording_mae, 4),
            "rmse": round(wording_rmse, 4),
            "r2": round(wording_r2, 4),
        },
        "overall_metrics": {
            "mean_mae": round(mean_mae, 4),
            "mean_rmse": round(mean_rmse, 4),
            "mean_r2": round(mean_r2, 4),
        },
        "avg_inference_latency_ms": latency_ms,
        "training_time_seconds": round(train_duration, 2),
        "model_architecture": "TF-IDF (5000 ngrams) + Surface Stats + MultiOutput Ridge Regressor",
        "ethical_boundary": "Scores reflect writing quality and rubric adherence only; never student intelligence",
    }
    with open(CHECKPOINT_DIR / "evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    print("CommonLit Summary Regressor training and evaluation successfully completed!")


if __name__ == "__main__":
    main()

