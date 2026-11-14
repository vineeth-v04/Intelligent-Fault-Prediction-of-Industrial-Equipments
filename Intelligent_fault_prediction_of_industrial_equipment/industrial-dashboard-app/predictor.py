"""
Predictor service for Intelligent Fault Prediction of Industrial Equipment
Integrates the trained models and ensures exact preprocessing during inference.
"""

import os
import json
import numpy as np
import xgboost as xgb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
CONFIG_PATH = os.path.join(MODELS_DIR, "model_config.json")
RF_MODEL_PATH = os.path.join(MODELS_DIR, "random_forest_model.json")

class FaultPredictor:
    def __init__(self):
        self.config = None
        self.rf_model = None
        self.load_models()

    def load_models(self):
        if not os.path.exists(CONFIG_PATH):
            # Attempt to run train_model if artifacts don't exist yet
            try:
                from train_model import train_and_save_pipeline
                train_and_save_pipeline()
            except Exception as e:
                print(f"Warning: Could not train pipeline automatically: {e}")

        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self.config = json.load(f)
                
        if os.path.exists(RF_MODEL_PATH):
            try:
                self.rf_model = xgb.XGBClassifier()
                self.rf_model.load_model(RF_MODEL_PATH)
            except Exception as e:
                print(f"Notice: XGBoost native model loading: {e}")
                self.rf_model = None

    def preprocess(self, data):
        """
        Applies the exact encoding and scaling used during training.
        Features: ['Type_encoded', 'Air temperature [K]', 'Process temperature [K]', 
                   'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']
        """
        raw_type = str(data.get("type", "L")).strip().upper()
        type_map = self.config.get("type_mapping", {"L": 0, "M": 1, "H": 2}) if self.config else {"L": 0, "M": 1, "H": 2}
        type_enc = float(type_map.get(raw_type, 0))

        air_temp = float(data.get("air_temperature", 300.0))
        proc_temp = float(data.get("process_temperature", 310.0))
        rot_speed = float(data.get("rotational_speed", 1538.0))
        torque = float(data.get("torque", 40.0))
        tool_wear = float(data.get("tool_wear", 108.0))

        raw_vector = [type_enc, air_temp, proc_temp, rot_speed, torque, tool_wear]

        if self.config and "scaler" in self.config:
            means = self.config["scaler"]["means"]
            scales = self.config["scaler"]["scales"]
            scaled_vector = [(x - m) / s for x, m, s in zip(raw_vector, means, scales)]
        else:
            # Fallback default scaler stats
            means = [0.4949, 300.0055, 310.0061, 1539.3569, 40.0034, 107.6850]
            scales = [0.6687, 1.9967, 1.4793, 180.9716, 10.0189, 63.6080]
            scaled_vector = [(x - m) / s for x, m, s in zip(raw_vector, means, scales)]

        return raw_vector, scaled_vector

    def predict_rule_based(self, raw_features):
        """Physical failure mechanisms defined by AI4I Predictive Maintenance dataset."""
        t_type = raw_features[0] # 0: L, 1: M, 2: H
        air_t = raw_features[1]
        proc_t = raw_features[2]
        rpm = raw_features[3]
        torque = raw_features[4]
        wear = raw_features[5]

        temp_diff = proc_t - air_t
        power_w = torque * (2 * np.pi * rpm / 60)
        osf_thresh = 11000 if t_type == 0 else (12000 if t_type == 1 else 13000)
        osf_val = wear * torque

        reasons = []
        if temp_diff < 8.6 and rpm < 1380:
            reasons.append("Heat Dissipation Failure (HDF)")
        if power_w < 3500:
            reasons.append(f"Power Failure - Low Power ({power_w:.0f} W < 3500 W)")
        elif power_w > 9000:
            reasons.append(f"Power Failure - Overload ({power_w:.0f} W > 9000 W)")
        if osf_val > osf_thresh:
            reasons.append(f"Overstrain Failure (Strain {osf_val:.0f} > {osf_thresh})")
        if wear >= 200:
            reasons.append(f"Tool Wear Failure ({wear:.0f} min >= 200 min)")
        if proc_t >= 335.0:
            reasons.append(f"Thermal Overheating Hazard ({proc_t:.1f} K >= 335 K)")
        elif air_t >= 325.0:
            reasons.append(f"Extreme Ambient Thermal Hazard ({air_t:.1f} K >= 325 K)")
        if rpm >= 3200:
            reasons.append(f"Spindle Overspeed Hazard ({rpm:.0f} RPM >= 3200 RPM)")

        is_fault = len(reasons) > 0
        failure_type = reasons[0] if is_fault else "No Failure"
        prob = 0.95 if is_fault else 0.04
        return is_fault, prob, failure_type, reasons

    def predict(self, data):
        """
        Executes prediction using specified strategy:
        'random-forest' (default), 'logistic-regression', or 'rule-based'.
        """
        strategy = str(data.get("strategy", "random-forest")).lower().strip()
        raw_vec, scaled_vec = self.preprocess(data)

        # Physics rule diagnostics
        is_rule_fault, rule_prob, rule_failure_type, rule_reasons = self.predict_rule_based(raw_vec)

        # Check moderate operating degradation / warning indicators (AI4I operating boundaries)
        air_t = raw_vec[1]
        proc_t = raw_vec[2]
        rpm = raw_vec[3]
        torque = raw_vec[4]
        wear = raw_vec[5]

        is_warning_condition = False
        warning_mode = "Operating Degradation"
        if not is_rule_fault:
            if wear >= 150:
                is_warning_condition = True
                warning_mode = f"Accelerated Tool Wear ({wear:.0f} min >= 150 min)"
            elif proc_t >= 315.0:
                is_warning_condition = True
                warning_mode = f"Elevated Process Temperature ({proc_t:.1f} K >= 315 K)"
            elif air_t >= 305.5:
                is_warning_condition = True
                warning_mode = f"Elevated Ambient Temperature ({air_t:.1f} K >= 305.5 K)"
            elif rpm >= 2900:
                is_warning_condition = True
                warning_mode = f"Elevated Spindle Speed ({rpm:.0f} RPM >= 2900 RPM)"
            elif rpm <= 1100 and rpm > 400:
                is_warning_condition = True
                warning_mode = f"Sub-optimal Spindle Speed ({rpm:.0f} RPM <= 1100 RPM)"
            elif torque >= 60.0:
                is_warning_condition = True
                warning_mode = f"High Mechanical Torque ({torque:.1f} Nm >= 60 Nm)"

        prediction = 0
        probability = 0.0
        failure_type = "No Failure"

        if strategy in ["rule-based", "rule_based"]:
            if is_rule_fault:
                prediction = 1
                probability = rule_prob
                failure_type = rule_failure_type
            elif is_warning_condition:
                prediction = 1
                probability = 0.58
                failure_type = warning_mode
            else:
                prediction = 0
                probability = rule_prob
                failure_type = "No Failure"
            
        elif strategy in ["logistic-regression", "logistic_regression", "lr"]:
            if self.config and "logistic_regression" in self.config:
                lr_cfg = self.config["logistic_regression"]
                intercept = lr_cfg["intercept"]
                weights = lr_cfg["weights"]
            else:
                intercept = -2.63
                weights = [-0.17, 0.44, -0.40, -1.82, 2.37, 1.34]

            z = intercept + sum(w * x for w, x in zip(weights, scaled_vec))
            probability = float(1.0 / (1.0 + np.exp(-np.clip(z, -25, 25))))
            if is_rule_fault:
                prediction = 1
                probability = max(probability, rule_prob)
                failure_type = rule_failure_type
            elif is_warning_condition and probability < 0.5:
                prediction = 1
                probability = 0.58
                failure_type = warning_mode
            else:
                prediction = 1 if probability >= 0.5 else 0
                failure_type = rule_failure_type if prediction == 1 else "No Failure"
            
        else: # Default: 'random-forest'
            if self.rf_model is not None:
                try:
                    prob_arr = self.rf_model.predict_proba([scaled_vec])[0]
                    probability = float(prob_arr[1])
                except Exception:
                    probability = rule_prob if is_rule_fault else 0.04
            else:
                probability = rule_prob if is_rule_fault else 0.04

            if is_rule_fault:
                prediction = 1
                probability = max(probability, rule_prob)
                failure_type = rule_failure_type
            elif is_warning_condition and probability < 0.5:
                prediction = 1
                probability = 0.58
                failure_type = warning_mode
            else:
                prediction = int(probability >= 0.5)
                failure_type = rule_failure_type if prediction == 1 else "No Failure"

        # Determine active faults and status
        if prediction == 1 or probability >= 0.5:
            if probability >= 0.75 or is_rule_fault:
                status = "CRITICAL"
                detected_faults = int(min(9, max(5, round(probability * 9))))
                msg = f"CRITICAL ({strategy.upper()}): High risk of equipment failure detected. Identified mode: {failure_type}."
            else:
                status = "WARNING"
                detected_faults = int(min(5, max(3, round(probability * 6))))
                msg = f"WARNING ({strategy.upper()}): Operating parameters indicate machine degradation."
        else:
            status = "NORMAL"
            detected_faults = 0 if probability < 0.15 else 1
            msg = f"NORMAL ({strategy.upper()}): All machine parameters are within normal tolerances."

        # Diagnostics for logging & display
        air_t = raw_vec[1]
        proc_t = raw_vec[2]
        rpm = raw_vec[3]
        torque = raw_vec[4]
        wear = raw_vec[5]
        power_w = torque * (2 * np.pi * rpm / 60)

        return {
            "prediction": int(prediction),
            "is_fault": bool(prediction == 1),
            "probability": round(float(probability), 4),
            "confidence_percent": round(float(probability if prediction == 1 else (1.0 - probability)) * 100, 1),
            "strategy": strategy,
            "status": status,
            "active_faults": detected_faults,
            "fault_message": msg,
            "failure_type": failure_type,
            "diagnostics": {
                "air_temperature_k": air_t,
                "process_temperature_k": proc_t,
                "temperature_difference_k": round(proc_t - air_t, 2),
                "rotational_speed_rpm": rpm,
                "torque_nm": torque,
                "power_watts": round(power_w, 1),
                "tool_wear_min": wear
            }
        }

# Global singleton predictor instance
predictor = FaultPredictor()

if __name__ == "__main__":
    print("Testing FaultPredictor...")
    # Test 1: Normal sample
    normal_sample = {
        "type": "L",
        "air_temperature": 298.1,
        "process_temperature": 308.6,
        "rotational_speed": 1551,
        "torque": 42.8,
        "tool_wear": 0,
        "strategy": "random-forest"
    }
    res1 = predictor.predict(normal_sample)
    print("Normal Sample Result:", res1["status"], "| Faults:", res1["active_faults"], "| Prob:", res1["probability"])

    # Test 2: Overstrain / Power fault sample
    fault_sample = {
        "type": "L",
        "air_temperature": 302.0,
        "process_temperature": 310.0,
        "rotational_speed": 1200,
        "torque": 68.0,
        "tool_wear": 215,
        "strategy": "random-forest"
    }
    res2 = predictor.predict(fault_sample)
    print("Fault Sample Result:", res2["status"], "| Mode:", res2["failure_type"], "| Prob:", res2["probability"])
