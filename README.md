# Intelligent Fault Prediction of Industrial Equipment Using Machine Learning

An intelligent industrial dashboard application that provides real-time telemetry visualization, equipment diagnostics, and machine learning-based fault prediction for industrial manufacturing equipment.

The application enables operators to monitor equipment health, analyze machine parameters, identify potential failures, and perform batch analysis of industrial datasets through an interactive dashboard.

---

## 📋 Project Overview

This project focuses on automated fault detection and predictive maintenance for industrial machinery using machine learning and physics-based diagnostic techniques.

The application provides the following capabilities:

- Real-time industrial telemetry visualization.
- Machine learning-based equipment failure prediction.
- Automated fault detection and diagnostics.
- Historical equipment performance monitoring.
- Machine health analysis through CSV uploads.
- Batch prediction for multiple machine records.
- AI-powered automated health report generation.

---

## 📊 Dataset & Features

The machine learning pipeline is trained exclusively on:

**`predictive_maintenance_new_training_dataset.csv`**

- Total Records: 10,000 industrial observations.
- Primary Dataset: `predictive_maintenance_new_training_dataset.csv`
- Historical Backup: `machine_training_data_old.csv` (preserved unchanged).

### Machine Parameters (Features)

The model uses six machine parameters for fault prediction:

| Feature | Description |
|---|---|
| Type | Machine quality variant (L, M, H) |
| Air Temperature [K] | Ambient air temperature in Kelvin (295.3–304.5 K) |
| Process Temperature [K] | Internal machine process temperature (305.7–313.8 K) |
| Rotational Speed [rpm] | Machine spindle rotational speed (1168–2886 rpm) |
| Torque [Nm] | Motor torque in Newton-meters (3.8–76.6 Nm) |
| Tool Wear [min] | Accumulated cutting tool wear (0–253 min) |

### Target Variable

| Value | Description |
|---|---|
| 0 | No Failure (Normal) |
| 1 | Equipment Failure (Fault) |

### Identified Failure Modes

The system considers five major industrial failure categories:

1. **Heat Dissipation Failure (HDF):** Occurs when the temperature differential between process and air temperature is below 8.6 K at low rotational speeds (< 1380 rpm).

2. **Power Failure (PWF):** Occurs when motor power output exceeds safe operating boundaries (below 3500 W or above 9000 W).

3. **Overstrain Failure (OSF):** Occurs when accumulated tool wear multiplied by torque exceeds the defined material threshold.

4. **Tool Wear Failure (TWF):** Associated with critical cutting tool wear (≥ 200 minutes).

5. **Random Failures:** Represents other unexpected equipment failure conditions.

---

## ⚙️ Data Preprocessing Pipeline

A consistent preprocessing pipeline is implemented during model training and real-time prediction to maintain data compatibility.

### Preprocessing Steps

1. **Data Cleaning**
   - Excludes non-predictive identification columns such as `UDI` and `Product ID`.
   - Performs duplicate checking and null-value validation.

2. **Categorical Encoding**
   - Converts the categorical `Type` feature into numerical values:
     - L → 0
     - M → 1
     - H → 2

3. **Feature Standardization**
   - Standardizes continuous numerical features using the Z-score standardization technique.

   Formula:

   `z = (x - μ) / σ`

   Where:
   - `x` = Original feature value
   - `μ` = Training dataset mean
   - `σ` = Training dataset standard deviation

4. **Preprocessing Consistency**
   - Manual machine parameter inputs and CSV batch uploads follow the same preprocessing pipeline.
   - Previously fitted training statistics are reused during inference.

---

## 🤖 Machine Learning Models

The application integrates three different prediction strategies.

### 1. Random Forest Classifier

- Class-weighted ensemble learning approach.
- Handles the class imbalance associated with the 3.4% failure class.
- Captures complex relationships between machine parameters.

**Performance:**
- Test Accuracy: 95.40%
- ROC-AUC Score: 0.9735

### 2. Logistic Regression

- L2 regularization.
- Balanced class weights.
- Provides a comparatively simple classification approach.

**Performance:**
- Test Accuracy: 82.30%
- ROC-AUC Score: 0.9047

### 3. Physics-Based Rule Engine

- Uses domain-specific mechanical and thermodynamic conditions.
- Evaluates machine parameters against predefined failure thresholds.
- Provides rule-based diagnostic predictions.

**Performance:**
- Test Accuracy: 92.45%

### Model Artifacts

Trained models and preprocessing configurations are stored in the `models/` directory.

| File | Description |
|---|---|
| `random_forest_model.json` | Serialized Random Forest model |
| `model_config.json` | Preprocessing parameters, weights, and model metadata |
| `model.joblib` | Scikit-learn model package |

---

## 🖥️ Dashboard Features

The application provides an interactive industrial monitoring dashboard with the following features.

### 1. Work Time Distribution
- Doughnut visualization of operational hours.
- Displays Operational, Idle, Maintenance, and Down hours.

### 2. Real-Time Monitoring Gauges
- Temperature monitoring.
- Pressure monitoring.
- Vibration monitoring.
- Active fault tracking.

### 3. Historical Trend Analysis
- Continuous machine parameter comparison over the last seven days.
- Critical fault timeline visualization.
- Historical equipment performance monitoring.

### 4. Fault Analysis
- Fault type breakdown.
- Machine-wise fault distribution.
- Donut and pie chart visualizations.

### 5. Manual Machine Parameter Analysis
- Enter all six machine parameters manually.
- Select the preferred prediction strategy.
- Generate instant failure predictions.
- Receive automated diagnostic results.

### 6. Dataset Health Analysis
- Upload industrial machine datasets in CSV format.
- Perform batch analysis of multiple machine records.
- Review Normal, Warning, and Critical health distributions.
- Evaluate overall fleet health.

### 7. AI-Powered Diagnostics
- Automated machine health report generation.
- Failure identification and diagnostic insights.
- Simplified interpretation of prediction results.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | Flask |
| Frontend | HTML, CSS, JavaScript |
| Machine Learning | Scikit-learn |
| Data Processing | Pandas, NumPy |
| Model Serialization | Joblib, JSON |
| Data Visualization | JavaScript Charts |
| Development Environment | VS Code |

---

## 🚀 Installation & Execution

Follow these steps to run the application locally.

### Prerequisites

- Python 3.x
- pip package manager
- Web browser

### Option 1: Using the Launcher Script (Recommended)

1. Clone or download the repository.
2. Navigate to the project directory.
3. Double-click `start_app.bat`.

Alternatively, execute the following command in the terminal:

```cmd
start_app.bat
