# Intelligent Fault Prediction of Industrial Equipment Using Machine Learning

An intelligent industrial dashboard application providing real-time telemetry visualization, diagnostics, and machine learning fault prediction for industrial manufacturing equipment.

## 📋 Project Overview

This project provides automated fault detection and diagnostics for industrial machinery. Operators can inspect live equipment telemetry, review fault breakdowns and historical trends, input machine parameters to receive instant failure predictions and diagnostics, and batch analyze machine health datasets.

---

## 📊 Dataset & Features

The machine learning pipeline is trained exclusively on:
**`predictive_maintenance_new_training_dataset.csv`** (10,000 real-world industrial observation records).

*(Note: `machine_training_data_old.csv` is preserved untouched as a historical backup).*

### Machine Parameters (Features)
1. **Type**: Product / Machine Quality Variant (`L` = Low 50%, `M` = Medium 30%, `H` = High 20%)
2. **Air temperature [K]**: Ambient air temperature in Kelvin (range: 295.3 – 304.5 K)
3. **Process temperature [K]**: Internal machine process temperature in Kelvin (range: 305.7 – 313.8 K)
4. **Rotational speed [rpm]**: Spindle rotational speed in RPM (range: 1168 – 2886 rpm)
5. **Torque [Nm]**: Motor torque in Newton-meters (range: 3.8 – 76.6 Nm)
6. **Tool wear [min]**: Accumulated cutting tool wear in minutes (range: 0 – 253 min)

### Target & Fault Modes
- **Target**: `0` = No Failure (Normal), `1` = Equipment Failure / Fault
- **Identified Failure Modes**:
  - **Heat Dissipation Failure (HDF)**: Inadequate temperature differential ($T_{\text{process}} - T_{\text{air}} < 8.6\text{ K}$) at low RPM ($< 1380\text{ rpm}$)
  - **Power Failure (PWF)**: Motor power output exceeds safe boundaries ($P < 3500\text{ W}$ or $P > 9000\text{ W}$)
  - **Overstrain Failure (OSF)**: Accumulated tool wear $\times$ torque exceeds material threshold
  - **Tool Wear Failure (TWF)**: Critical cutting tool wear ($\ge 200\text{ min}$)
  - **Random Failures**

---

## ⚙️ Data Preprocessing Pipeline

Before training and during real-time inference, all inputs undergo the exact same preprocessing:
1. **Data Cleaning**: Non-parameter identification columns (`UDI`, `Product ID`) are excluded. Duplicate checking and null validation confirm data completeness.
2. **Categorical Encoding**: Quality variant `Type` is encoded (`L` $\to 0$, `M` $\to 1$, `H` $\to 2$).
3. **Feature Standardization**: Continuous features are standardized ($z = \frac{x - \mu}{\sigma}$) using the fitted training statistics.
4. **Consistency**: User-entered manual parameters and CSV batch uploads pass through this identical pipeline.

---

## 🤖 Trained Machine Learning Models

The application integrates three prediction strategies:
1. **Random Forest Classifier**:
   - Class-weighted ensemble addressing the 3.4% failure class imbalance.
   - **Test Accuracy**: 95.40%
   - **ROC-AUC Score**: 0.9735
2. **Logistic Regression**:
   - L2 regularized with balanced loss weights.
   - **Test Accuracy**: 82.30%
   - **ROC-AUC Score**: 0.9047
3. **Physics-Based Rule Engine**:
   - Domain-specific mechanical thermodynamics equations.
   - **Test Accuracy**: 92.45%

Model artifacts and preprocessor parameters are saved in `models/` (`random_forest_model.json`, `model_config.json`, `model.joblib`).

---

## 🚀 How to Run the Application

### Option A: Using the Launcher Script (Recommended)
Double-click `start_app.bat` or run from terminal:
```cmd
start_app.bat
```

### Option B: Using Python Directly
1. Install dependencies:
   ```cmd
   py -m pip install -r requirements.txt
   ```
2. Launch the application:
   ```cmd
   py app.py
   ```
3. Open your browser at: `http://127.0.0.1:5000/`

### Retraining the Model
To re-run the complete cleaning, preprocessing, and training pipeline:
```cmd
py train_model.py
```

---

## 🖥️ User Interface & Dashboard Features

The dashboard user interface is preserved as-is:
- **Work Time Distribution**: Doughnut visualization of Operational, Idle, Maintenance, and Down hours.
- **Real-Time Gauges**: Temperature, Pressure, Vibration, and Active Faults.
- **Trend Line Charts**: Continuous live parameter comparison (Last 7 Days) and Critical Faults Timeline.
- **Fault Breakdowns**: Donut and pie charts showing fault type and unit breakdowns.
- **Input Data Modal**: Input all 6 machine parameters, select prediction strategy, analyze data, and receive instant diagnostic results.
- **Dataset Health Analysis**: Upload CSV datasets to analyze overall fleet health and review Normal / Warning / Critical distributions.
- **AI Diagnostics**: Instant automated health report generation.

---

## 📁 Repository Structure

```
industrial-dashboard-app/
├── app.py                                          # Flask backend & API endpoints
├── predictor.py                                    # Unified preprocessing & inference engine
├── train_model.py                                  # Training script for new dataset
├── requirements.txt                                # Python dependencies
├── start_app.bat                                   # One-click startup script
├── .gitignore                                      # Git ignore rules
├── README.md                                       # Project documentation
├── machine_training_data_old.csv                   # Historical backup dataset (untouched)
├── predictive_maintenance_new_training_dataset.csv # Primary training dataset
├── models/
│   ├── model_config.json                           # Preprocessing parameters, weights & metadata
│   ├── model.joblib                                # Scikit-learn/joblib model package
│   └── random_forest_model.json                    # Serialized Random Forest model
├── static/
│   ├── indus.js                                    # Dashboard logic, charts, input & prediction
│   └── style.css                                   # Dashboard visual styling
└── templates/
    └── index.html                                  # Dashboard markup with machine parameter inputs
```
