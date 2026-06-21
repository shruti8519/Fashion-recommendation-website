"""
Optional training pipeline for deeper personalization.
This script demonstrates how to fine-tune a small MLP on top of frozen image+metadata embeddings.
"""

from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import tensorflow as tf


def load_training_pairs(path: Path) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path)
    # Expected columns:
    # user_vec_0 ... user_vec_n, item_vec_0 ... item_vec_n, label
    user_cols = [c for c in df.columns if c.startswith("user_vec_")]
    item_cols = [c for c in df.columns if c.startswith("item_vec_")]
    x = np.concatenate([df[user_cols].to_numpy(), df[item_cols].to_numpy()], axis=1)
    y = df["label"].to_numpy().astype("float32")
    return x, y


def build_ranker(input_dim: int) -> tf.keras.Model:
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(input_dim,)),
            tf.keras.layers.Dense(256, activation="relu"),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(128, activation="relu"),
            tf.keras.layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["AUC"])
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=str, required=True, help="Path to training pairs CSV")
    parser.add_argument("--out", type=str, default="ranker.keras", help="Output model path")
    args = parser.parse_args()

    x, y = load_training_pairs(Path(args.pairs))
    model = build_ranker(x.shape[1])
    model.fit(x, y, validation_split=0.2, epochs=8, batch_size=64)
    model.save(args.out)
    print(f"Saved ranker model to {args.out}")


if __name__ == "__main__":
    main()

