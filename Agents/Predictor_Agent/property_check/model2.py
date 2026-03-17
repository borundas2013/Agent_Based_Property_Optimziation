# train_property_models.py

import os
import sys
import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# --- Import your existing utilities & feature pipeline ---
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', '..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# assuming your file defines these:
# load_data, extract_molecular_features, create_train_test_split
from data_processor import load_data, extract_molecular_features, create_train_test_split


def eval_regression(name, y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2  = r2_score(y_true, y_pred)
    print(f"\n[{name}]")
    print(f"  MAE : {mae:.4f}")
    print(f"  RMSE: {rmse:.4f}")
    print(f"  R2  : {r2:.4f}")
    return {"mae": mae, "rmse": rmse, "r2": r2}


def main():
    # ---- Paths ----
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    data_path = os.path.join(project_root, "data", "unique_smiles_Er.csv")

    out_dir = os.path.join(project_root, "src", "Reward_component", "property_alignment", "models")
    os.makedirs(out_dir, exist_ok=True)

    model_tg_path = os.path.join(out_dir, "tg_hgb_without_mod.pkl")
    model_er_path = os.path.join(out_dir, "er_hgb_log1p_without_mod.pkl")

    # ---- Load ----
    smiles1_list, smiles2_list, tg_list, er_list, ratio1_list, ratio2_list = load_data(data_path)

    # ---- Features (IMPORTANT: pass ratios!) ----
    X = extract_molecular_features(
        smiles1_list,
        smiles2_list,
        ratio1_list=ratio1_list,
        ratio2_list=ratio2_list,
        fp_bits=1024,
        use_symmetric=True
    )

    y_tg = np.array(tg_list, dtype=np.float32)
    y_er = np.array(er_list, dtype=np.float32)

    # ---- Split (group split avoids leakage) ----
    X_train, X_test, y_tg_train, y_tg_test, y_er_train, y_er_test = create_train_test_split(
        X, y_tg, y_er,
        smiles1_list=smiles1_list,
        smiles2_list=smiles2_list,
        test_size=0.2,
        random_state=42,
        use_group_split=True
    )

    # ---- Transform Er (recommended) ----
    y_er_train_log = np.log1p(y_er_train)
    y_er_test_log  = np.log1p(y_er_test)

    # ---- Models ----
    # Good defaults for ~1k samples; you can tune later.
    tg_model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.05,
        max_depth=6,
        max_iter=600,
        min_samples_leaf=15,
        l2_regularization=1e-3,
        random_state=42
    )

    er_model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.05,
        max_depth=6,
        max_iter=600,
        min_samples_leaf=15,
        l2_regularization=1e-3,
        random_state=42
    )

    # ---- Train ----
    print("\nTraining Tg model...")
    tg_model.fit(X_train, y_tg_train)

    print("Training Er model (log1p)...")
    er_model.fit(X_train, y_er_train_log)

    # ---- Evaluate ----
    # Tg
    y_tg_pred = tg_model.predict(X_test)
    eval_regression("Tg (test)", y_tg_test, y_tg_pred)

    # Er (log space)
    y_er_pred_log = er_model.predict(X_test)
    eval_regression("Er log1p (test)", y_er_test_log, y_er_pred_log)

    # Er (original scale)
    y_er_pred = np.expm1(y_er_pred_log)
    eval_regression("Er original scale (test)", y_er_test, y_er_pred)

    # ---- Save ----
    joblib.dump(tg_model, model_tg_path)
    joblib.dump(er_model, model_er_path)

    print("\nSaved models:")
    print(f"  Tg model -> {model_tg_path}")
    print(f"  Er model -> {model_er_path}")


if __name__ == "__main__":
    main()
