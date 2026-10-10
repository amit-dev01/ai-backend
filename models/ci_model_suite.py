import os
import joblib
import numpy as np

class CIModelSuite:
    """Production inference engine for XGBoost, Isolation Forest & HDBSCAN."""
    _xgb_model = None
    _encoders = None
    _iso_forest = None
    _umap_reducer = None

    @classmethod
    def load(cls, models_dir=None):
        if cls._xgb_model is None:
            if models_dir is None:
                models_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Prefer universal cross-OS JSON format
            json_path = os.path.join(models_dir, "xgboost_win_loss.json")
            if os.path.exists(json_path):
                import xgboost as xgb
                cls._xgb_model = xgb.XGBClassifier()
                cls._xgb_model.load_model(json_path)
            else:
                cls._xgb_model = joblib.load(os.path.join(models_dir, "xgboost_win_loss.joblib"))
                
            cls._encoders = joblib.load(os.path.join(models_dir, "encoders.joblib"))
            cls._iso_forest = joblib.load(os.path.join(models_dir, "isolation_forest.joblib"))
            
            # Lazy load UMAP reducer if umap package is installed locally
            try:
                umap_path = os.path.join(models_dir, "umap_reducer.joblib")
                if os.path.exists(umap_path):
                    cls._umap_reducer = joblib.load(umap_path)
            except Exception:
                cls._umap_reducer = None

    @classmethod
    def predict_deal_odds(cls, deal_size: float, competitor: str, days: int, client_size: str):
        cls.load()
        comp_enc = cls._encoders['competitor'].transform([competitor])[0] if competitor in cls._encoders['competitor'].classes_ else 0
        size_enc = cls._encoders['client_size'].transform([client_size])[0] if client_size in cls._encoders['client_size'].classes_ else 0
        log_deal = np.log1p(deal_size)
        features = np.array([[log_deal, comp_enc, days, size_enc]])
        win_prob = float(cls._xgb_model.predict_proba(features)[0][1])
        return {
            "winProbability": round(win_prob * 100, 1),
            "status": "FAVORABLE" if win_prob >= 0.6 else "AT_RISK" if win_prob >= 0.35 else "CRITICAL"
        }

    @classmethod
    def detect_stealth_anomaly(cls, metric_val: float, rolling_mean: float, rolling_std: float, rate_of_change: float):
        cls.load()
        features = np.array([[metric_val, rolling_mean, rolling_std, rate_of_change]])
        is_anomaly = bool(cls._iso_forest.predict(features)[0] == -1)
        anomaly_score = float(cls._iso_forest.decision_function(features)[0])
        return {
            "isStealthAlert": is_anomaly,
            "severityScore": round(max(0.0, 100.0 - (anomaly_score * 200.0)), 1)
        }
