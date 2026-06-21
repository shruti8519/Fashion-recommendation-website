from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing import image as keras_image
from sklearn.preprocessing import OneHotEncoder


@dataclass
class RecommendationResult:
    item_id: str
    image: str
    category: str
    color: str
    style: str
    score: float
    reason: str
    tags: List[str]


class DeepFashionRecommender:
    """
    Hybrid deep learning recommender:
    - CNN image embeddings using MobileNetV2 (transfer learning)
    - Dense projection network over item metadata
    - Late fusion + cosine similarity ranking
    """

    def __init__(self, dataset_csv: Path, image_root: Path):
        self.dataset_csv = dataset_csv
        self.image_root = image_root
        self.df: pd.DataFrame | None = None
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.cnn = MobileNetV2(weights="imagenet", include_top=False, pooling="avg")
        self.meta_net = self._build_meta_network()
        self.item_embeddings: np.ndarray | None = None

    def _build_meta_network(self) -> tf.keras.Model:
        model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(256,)),
                tf.keras.layers.Dense(128, activation="relu"),
                tf.keras.layers.Dropout(0.15),
                tf.keras.layers.Dense(64, activation="relu"),
                tf.keras.layers.Dense(32, activation=None),
            ]
        )
        return model

    def _resolve_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        lowered = {c.lower(): c for c in df.columns}

        def pick(candidates: List[str], fallback: str | None) -> str | None:
            for candidate in candidates:
                for lower_name, original_name in lowered.items():
                    if candidate in lower_name:
                        return original_name
            return fallback

        return {
            "id": pick(["id", "item"], df.columns[0]),
            "category": pick(["category", "product", "type"], df.columns[0]),
            "color": pick(["color"], df.columns[min(1, len(df.columns) - 1)]),
            "style": pick(["style", "occasion"], df.columns[min(2, len(df.columns) - 1)]),
            # No last-column fallback: avoids treating unrelated text as image filenames.
            "image": pick(["image", "img", "file"], None),
        }

    def _first_existing_column(self, df: pd.DataFrame, candidates: List[str]) -> str | None:
        lowered = {c.lower(): c for c in df.columns}
        for candidate in candidates:
            for low, original in lowered.items():
                if candidate in low:
                    return original
        return None

    def _read_image_embedding(self, image_rel_path: str) -> np.ndarray:
        try:
            image_path = self.image_root / str(image_rel_path)
            img = Image.open(image_path).convert("RGB").resize((224, 224))
            arr = keras_image.img_to_array(img)
            arr = np.expand_dims(arr, axis=0)
            arr = preprocess_input(arr)
            features = self.cnn.predict(arr, verbose=0)[0]
            return features.astype(np.float32)
        except Exception:
            return np.zeros((1280,), dtype=np.float32)

    def _normalize(self, matrix: np.ndarray) -> np.ndarray:
        denom = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8
        return matrix / denom

    def prepare(self) -> None:
        df = pd.read_csv(self.dataset_csv)
        cols = self._resolve_columns(df)
        df = df.rename(columns={v: k for k, v in cols.items() if v})

        # Support alternate dataset schemas (including the recommended Kaggle sheet format).
        if "id" not in df.columns:
            df["id"] = [f"item_{i}" for i in range(len(df))]

        if "category" not in df.columns:
            category_col = self._first_existing_column(
                df, ["recommended fitting style", "fitting style", "recommended shoes", "materials"]
            )
            df["category"] = df[category_col] if category_col else "Fashion Recommendation"

        if "color" not in df.columns:
            color_col = self._first_existing_column(
                df, ["recommended clothing colors", "hair color", "eye color", "skin tone", "color"]
            )
            df["color"] = df[color_col] if color_col else "neutral"

        if "style" not in df.columns:
            style_col = self._first_existing_column(
                df, ["recommended patterns", "recommended fitting style", "fabric nature", "style"]
            )
            df["style"] = df[style_col] if style_col else "classic"

        if "image" not in df.columns:
            # Dataset may not include image paths; use stable placeholder seeds per item.
            df["image"] = [f"https://picsum.photos/seed/fashion-{i}/500/650" for i in range(len(df))]

        df = df[["id", "category", "color", "style", "image"]].fillna("unknown")
        # Align with storefront catalog in main._build_product_catalog: row i → id "p-{i}".
        # The raw CSV may have no real id column (first column can be mis-detected as "id").
        df["id"] = [f"p-{i}" for i in range(len(df))]
        df["category"] = df["category"].astype(str)
        df["color"] = df["color"].astype(str)
        df["style"] = df["style"].astype(str)
        df["image"] = df["image"].astype(str)

        meta = self.encoder.fit_transform(df[["category", "color", "style"]])
        pad = np.zeros((meta.shape[0], max(0, 256 - meta.shape[1])), dtype=np.float32)
        meta_padded = np.concatenate([meta, pad], axis=1)[:, :256]

        meta_emb = self.meta_net.predict(meta_padded, verbose=0).astype(np.float32)

        image_emb = np.stack([self._read_image_embedding(p) for p in df["image"].tolist()])
        fused = np.concatenate([0.55 * image_emb, 0.45 * meta_emb], axis=1)
        self.item_embeddings = self._normalize(fused)
        self.df = df

    def _build_user_embedding(
        self, preferred_styles: List[str], preferred_colors: List[str], history_ids: List[str]
    ) -> np.ndarray:
        assert self.df is not None and self.item_embeddings is not None
        if history_ids:
            hist_mask = self.df["id"].isin(history_ids).to_numpy()
            if hist_mask.any():
                return self.item_embeddings[hist_mask].mean(axis=0)

        pseudo = pd.DataFrame(
            {
                "category": ["unknown"],
                "color": [preferred_colors[0] if preferred_colors else "unknown"],
                "style": [preferred_styles[0] if preferred_styles else "unknown"],
            }
        )
        meta = self.encoder.transform(pseudo)
        pad = np.zeros((meta.shape[0], max(0, 256 - meta.shape[1])), dtype=np.float32)
        meta_padded = np.concatenate([meta, pad], axis=1)[:, :256]
        meta_emb = self.meta_net.predict(meta_padded, verbose=0)
        fused = np.concatenate([np.zeros((1, 1280), dtype=np.float32), meta_emb], axis=1)
        return self._normalize(fused)[0]

    def recommend(
        self,
        preferred_styles: List[str],
        preferred_colors: List[str],
        history_ids: List[str],
        top_k: int = 12,
        query: str | None = None,
        filter_category: str | None = None,
        filter_color: str | None = None,
    ) -> List[RecommendationResult]:
        assert self.df is not None and self.item_embeddings is not None
        user_emb = self._build_user_embedding(preferred_styles, preferred_colors, history_ids)
        sims = self.item_embeddings @ user_emb
        working = self.df.copy()
        working["score"] = sims

        if query:
            q = query.lower()
            mask = (
                working["category"].str.lower().str.contains(q)
                | working["color"].str.lower().str.contains(q)
                | working["style"].str.lower().str.contains(q)
            )
            working = working[mask]
        if filter_category:
            working = working[working["category"].str.lower() == filter_category.lower()]
        if filter_color:
            working = working[working["color"].str.lower() == filter_color.lower()]

        ranked = working.sort_values("score", ascending=False).head(top_k)
        out: List[RecommendationResult] = []
        for _, row in ranked.iterrows():
            tags = [row["category"], row["color"], row["style"]]
            reason = (
                f"Matched your style preference for {row['style']} with {row['color']} color profile."
            )
            out.append(
                RecommendationResult(
                    item_id=row["id"],
                    image=(
                        row["image"]
                        if str(row["image"]).startswith("http")
                        else f"/images/{str(row['image']).replace(os.sep, '/')}"
                    ),
                    category=row["category"],
                    color=row["color"],
                    style=row["style"],
                    score=float(row["score"]),
                    reason=reason,
                    tags=tags,
                )
            )
        return out

