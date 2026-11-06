"""
Training Pipeline for Intelligent Fault Prediction of Industrial Equipment
Dataset: predictive_maintenance_new_training_dataset.csv
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, accuracy_score, confusion_matrix
from scipy.optimize import minimize
import xgboost as xgb
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_DATASET_PATH = os.path.join(BASE_DIR, "predictive_maintenance_new_training_dataset.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")

def train_and_save_pipeline():
    print("=" * 60)
    print("Industrial Fault Prediction - Model Training Pipeline")
    print("=" * 60)
    
    if not os.path.exists(NEW_DATASET_PATH):
        raise FileNotFoundError(f"Training dataset not found at: {NEW_DATASET_PATH}")
    
    print(f"\n1. Loading dataset: {os.path.basename(NEW_DATASET_PATH)}")
    df = pd.read_csv(NEW_DATASET_PATH)
    print(f"   Raw Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # --- Step 1: Data Inspection and Cleaning ---
    print("\n2. Data Inspection & Cleaning:")
    missing_count = df.isnull().sum().to_dict()
    print(f"   Missing values per column: {missing_count}")
    
    initial_rows = len(df)
    df = df.drop_duplicates()
    duplicates_removed = initial_rows - len(df)
    print(f"   Duplicates removed: {duplicates_removed}")
    
    # Drop non-parameter identification columns
    identifier_cols = ['UDI', 'Product ID']
    cols_to_drop = [col for col in identifier_cols if col in df.columns]
    df_clean = df.drop(columns=cols_to_drop)
    print(f"   Dropped identifier columns: {cols_to_drop}")
    
    # Target distribution
    target_counts = df_clean['Target'].value_counts().to_dict()
    print(f"   Target distribution: {target_counts} (Class 0: No Failure, Class 1: Failure)")
    
    # --- Step 2: Feature Encoding & Preprocessing ---
    print("\n3. Feature Encoding & Preprocessing:")
    type_map = {'L': 0, 'M': 1, 'H': 2}
    df_clean['Type_encoded'] = df_clean['Type'].map(type_map)
    
    feature_names = [
        'Type_encoded',
        'Air temperature [K]',
        'Process temperature [K]',
        'Rotational speed [rpm]',
        'Torque [Nm]',
        'Tool wear [min]'
    ]
    
    X = df_clean[feature_names].values
    y = df_clean['Target'].values
    
    # Stratified train/test split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   Train samples: {len(X_train)} | Test samples: {len(X_test)}")
    
    # Fit StandardScaler on training features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    means = scaler.mean_.tolist()
    scales = scaler.scale_.tolist()
    print("   StandardScaler fitted successfully.")
    for name, m, s in zip(feature_names, means, scales):
        print(f"     - {name}: Mean = {m:.4f}, Std = {s:.4f}")
        
    # --- Step 3: Model Training ---
    print("\n4. Training Machine Learning Models:")
    
    # A. Random Forest Classifier (using XGBoost parallel trees with class weighting)
    scale_pos_weight = float((len(y_train) - sum(y_train)) / sum(y_train))
    print(f"   Training Random Forest (Balanced scale_pos_weight: {scale_pos_weight:.2f})...")
    
    rf_model = xgb.XGBClassifier(
        n_estimators=1,
        num_parallel_tree=100,
        learning_rate=1.0,
        subsample=0.8,
        colsample_bynode=0.8,
        max_depth=8,
        scale_pos_weight=scale_pos_weight,
        random_state=42
    )
    rf_model.fit(X_train_scaled, y_train)
    
    rf_test_preds = rf_model.predict(X_test_scaled)
    rf_test_probs = rf_model.predict_proba(X_test_scaled)[:, 1]
    rf_acc = accuracy_score(y_test, rf_test_preds)
    rf_auc = roc_auc_score(y_test, rf_test_probs)
    print(f"   -> Random Forest Test Accuracy: {rf_acc * 100:.2f}% | ROC-AUC: {rf_auc:.4f}")
    
    # B. Logistic Regression (Class-weighted L2 regularized via scipy)
    print("   Training Logistic Regression...")
    X_train_b = np.c_[np.ones(len(X_train_scaled)), X_train_scaled]
    X_test_b = np.c_[np.ones(len(X_test_scaled)), X_test_scaled]
    
    w0 = len(y_train) / (2.0 * (len(y_train) - sum(y_train)))
    w1 = len(y_train) / (2.0 * sum(y_train))
    sample_weights = np.where(y_train == 1, w1, w0)
    
    def log_loss(theta):
        z = X_train_b @ theta
        p = 1 / (1 + np.exp(-np.clip(z, -25, 25)))
        eps = 1e-15
        p = np.clip(p, eps, 1 - eps)
        cost = -np.mean(sample_weights * (y_train * np.log(p) + (1 - y_train) * np.log(1 - p))) + 0.01 * np.sum(theta[1:]**2)
        return cost
        
    def log_grad(theta):
        z = X_train_b @ theta
        p = 1 / (1 + np.exp(-np.clip(z, -25, 25)))
        g = (X_train_b.T @ (sample_weights * (p - y_train))) / len(y_train)
        g[1:] += 0.02 * theta[1:]
        return g
        
    opt_res = minimize(log_loss, np.zeros(X_train_b.shape[1]), jac=log_grad, method='L-BFGS-B')
    lr_theta = opt_res.x
    lr_intercept = float(lr_theta[0])
    lr_weights = [float(w) for w in lr_theta[1:]]
    
    lr_test_probs = 1 / (1 + np.exp(-np.clip(X_test_b @ lr_theta, -25, 25)))
    lr_test_preds = (lr_test_probs >= 0.5).astype(int)
    lr_acc = accuracy_score(y_test, lr_test_preds)
    lr_auc = roc_auc_score(y_test, lr_test_probs)
    print(f"   -> Logistic Regression Test Accuracy: {lr_acc * 100:.2f}% | ROC-AUC: {lr_auc:.4f}")
    
    # C. Rule-Based Physics Classifier Evaluation
    print("   Evaluating Rule-Based Physics Fault Engine...")
    rule_preds = []
    for row in X_test:
        t_type = row[0] # 0: L, 1: M, 2: H
        air_t = row[1]
        proc_t = row[2]
        rpm = row[3]
        torque = row[4]
        wear = row[5]
        
        # Physical failure modes
        hdf = (proc_t - air_t < 8.6) and (rpm < 1380)
        power_w = torque * (2 * np.pi * rpm / 60)
        pwf = (power_w < 3500) or (power_w > 9000)
        osf_thresh = 11000 if t_type == 0 else (12000 if t_type == 1 else 13000)
        osf = (wear * torque) > osf_thresh
        twf = wear >= 200
        
        rule_fault = int(hdf or pwf or osf or twf)
        rule_preds.append(rule_fault)
    rule_acc = accuracy_score(y_test, rule_preds)
    print(f"   -> Rule-Based Test Accuracy: {rule_acc * 100:.2f}%")
    
    # --- Step 4: Save Model Artifacts ---
    print("\n5. Saving Model Artifacts:")
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Save XGBoost Native Model
    rf_model_path = os.path.join(MODELS_DIR, "random_forest_model.json")
    rf_model.save_model(rf_model_path)
    print(f"   Saved: {rf_model_path}")
    
    # Extract trees for client-side evaluation if needed
    tree_dumps = rf_model.get_booster().get_dump(dump_format='json')
    tree_objects = [json.loads(t) for t in tree_dumps]
    
    # Comprehensive Config & Metadata
    model_config = {
        "dataset_name": os.path.basename(NEW_DATASET_PATH),
        "total_records": len(df_clean),
        "features": [
            "Type",
            "Air temperature [K]",
            "Process temperature [K]",
            "Rotational speed [rpm]",
            "Torque [Nm]",
            "Tool wear [min]"
        ],
        "type_mapping": type_map,
        "scaler": {
            "feature_names": feature_names,
            "means": means,
            "scales": scales
        },
        "logistic_regression": {
            "intercept": lr_intercept,
            "weights": lr_weights,
            "threshold": 0.5,
            "metrics": {
                "accuracy": round(lr_acc, 4),
                "roc_auc": round(lr_auc, 4)
            }
        },
        "random_forest": {
            "n_trees": len(tree_objects),
            "max_depth": 8,
            "metrics": {
                "accuracy": round(rf_acc, 4),
                "roc_auc": round(rf_auc, 4)
            },
            "trees": tree_objects
        },
        "rule_based": {
            "metrics": {
                "accuracy": round(rule_acc, 4)
            }
        }
    }
    
    config_path = os.path.join(MODELS_DIR, "model_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(model_config, f, indent=2)
    print(f"   Saved: {config_path}")
    
    # Also save a joblib package for standard Python integration
    joblib_path = os.path.join(MODELS_DIR, "model.joblib")
    joblib_bundle = {
        "scaler": scaler,
        "type_map": type_map,
        "feature_names": feature_names,
        "lr_theta": lr_theta,
        "metrics": {
            "rf_acc": rf_acc,
            "rf_auc": rf_auc,
            "lr_acc": lr_acc,
            "lr_auc": lr_auc
        }
    }
    joblib.dump(joblib_bundle, joblib_path)
    print(f"   Saved: {joblib_path}")
    
    print("\n" + "=" * 60)
    print("Training Complete & All Models Saved Successfully!")
    print("=" * 60)
    return model_config

if __name__ == "__main__":
    train_and_save_pipeline()
