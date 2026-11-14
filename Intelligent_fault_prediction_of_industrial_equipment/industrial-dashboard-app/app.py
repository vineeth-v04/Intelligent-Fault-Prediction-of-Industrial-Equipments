from flask import Flask, render_template, request, jsonify
import webbrowser
import threading
import os
from predictor import predictor

app = Flask(__name__)

@app.route("/")
def dashboard():
    # Renders the existing dashboard UI exactly as before.
    return render_template("index.html")

@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    Inference endpoint: takes machine parameters from new dataset,
    runs the same preprocessing, and returns model prediction.
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        
        result = predictor.predict(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/model-info", methods=["GET"])
def api_model_info():
    """Returns metadata and metrics of the trained model."""
    if predictor.config:
        info = {
            "dataset_name": predictor.config.get("dataset_name"),
            "features": predictor.config.get("features"),
            "type_mapping": predictor.config.get("type_mapping"),
            "metrics": {
                "random_forest": predictor.config.get("random_forest", {}).get("metrics", {}),
                "logistic_regression": predictor.config.get("logistic_regression", {}).get("metrics", {}),
                "rule_based": predictor.config.get("rule_based", {}).get("metrics", {})
            }
        }
        return jsonify(info)
    return jsonify({"status": "Model config loading..."})

def open_browser():
    # Automatically open the browser
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    # Wait ~1.25s for the Flask server to start, then open the browser
    threading.Timer(1.25, open_browser).start()
    # Disable debug to prevent the timer from running twice due to the reloader
    app.run(debug=False, port=5000)
