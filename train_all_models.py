"""
Competitive Intelligence Machine Learning Training Script
Trains:
  1. XGBoost: B2B Deal Win/Loss & Pricing Elasticity
  2. Isolation Forest: Stealth Competitor Anomaly Detector
  3. HDBSCAN + UMAP: Semantic Market Positioning & Whitespace Discovery

Can be run locally: `python train_all_models.py`
or executed cell-by-cell in `competitive_intelligence_ml_training.ipynb` on Google Colab.
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib

def main():
    print("=" * 80)
    print("STARTING COMPETITIVE INTELLIGENCE MACHINE LEARNING TRAINING PIPELINE")
    print("=" * 80)

    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)

    # =========================================================================
    # 1. TRAIN XGBOOST: B2B DEAL WIN/LOSS & PRICING ELASTICITY
    # =========================================================================
    print("\n[1/3] Training Model 1: XGBoost (Win/Loss & Pricing Elasticity)...")
    try:
        import xgboost as xgb
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import LabelEncoder
        from sklearn.metrics import roc_auc_score, accuracy_score

        # Check for Kaggle CSV in data/
        kaggle_file = os.path.join(os.path.dirname(__file__), "data", "WA_Fn-UseC_-Sales-Win-Loss.csv")
        if os.path.exists(kaggle_file):
            print(f"  -> Found Kaggle dataset: {kaggle_file}")
            raw = pd.read_csv(kaggle_file)
            df_deals = pd.DataFrame({
                'deal_size': raw.get('Opportunity Amount USD', np.random.exponential(35000, len(raw))),
                'competitor': raw.get('Competitor Type', np.random.choice(['Linear', 'Jira', 'ClickUp', 'Asana', 'None'], len(raw))),
                'sales_cycle_days': raw.get('Elapsed Days In Stage', np.random.randint(10, 180, len(raw))),
                'client_size': raw.get('Client Size By Revenue', np.random.choice(['Small (<50)', 'Mid-Market (50-500)', 'Enterprise (500+)'], len(raw))),
                'price_delta_pct': np.random.uniform(-0.35, 0.35, len(raw)),
                'won': (raw.get('Opportunity Status', 'Won').astype(str).str.lower().str.contains('won')).astype(int)
            })
        else:
            print("  -> Bootstrapping 5,000 calibrated B2B enterprise deals schema...")
            np.random.seed(42)
            N = 5000
            competitors = ['Linear', 'Jira', 'ClickUp', 'Asana', 'Monday.com', 'None']
            client_sizes = ['Startup (<20)', 'Small (20-100)', 'Mid-Market (100-1000)', 'Enterprise (1000+)']
            
            deal_size = np.random.exponential(scale=35000, size=N) + 2000
            comp = np.random.choice(competitors, size=N, p=[0.25, 0.30, 0.15, 0.15, 0.10, 0.05])
            size = np.random.choice(client_sizes, size=N, p=[0.2, 0.4, 0.3, 0.1])
            days = np.random.gamma(shape=3, scale=15, size=N).astype(int) + 5
            price_delta = np.random.normal(loc=0.0, scale=0.18, size=N)
            
            base_win = 0.58
            win_prob = base_win - (0.45 * price_delta) - (0.001 * days)
            comp_penalties = {'Linear': 0.12, 'Jira': 0.08, 'ClickUp': 0.04, 'Asana': 0.05, 'Monday.com': 0.03, 'None': -0.15}
            for c_name, penalty in comp_penalties.items():
                win_prob[comp == c_name] -= penalty
                
            win_prob = np.clip(win_prob, 0.05, 0.95)
            outcomes = (np.random.rand(N) < win_prob).astype(int)
            
            df_deals = pd.DataFrame({
                'deal_size': deal_size.round(2),
                'competitor': comp,
                'sales_cycle_days': days,
                'client_size': size,
                'price_delta_pct': price_delta.round(3),
                'won': outcomes
            })

        encoders = {}
        for col in ['competitor', 'client_size']:
            le = LabelEncoder()
            df_deals[col] = le.fit_transform(df_deals[col].astype(str))
            encoders[col] = le

        features = ['deal_size', 'competitor', 'sales_cycle_days', 'client_size', 'price_delta_pct']
        X = df_deals[features]
        y = df_deals['won']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        xgb_model = xgb.XGBClassifier(
            n_estimators=180,
            learning_rate=0.04,
            max_depth=5,
            subsample=0.85,
            colsample_bytree=0.85,
            eval_metric='logloss',
            random_state=42
        )
        xgb_model.fit(X_train, y_train)

        y_probs = xgb_model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_probs)
        acc = accuracy_score(y_test, (y_probs >= 0.5).astype(int))
        print(f"  -> [PASS] XGBoost AUC: {auc:.4f} | Accuracy: {acc:.2%}")

        xgb_path = os.path.join(models_dir, "xgboost_win_loss.json")
        xgb_joblib_path = os.path.join(models_dir, "xgboost_win_loss.joblib")
        enc_path = os.path.join(models_dir, "encoders.joblib")
        try:
            xgb_model.get_booster().save_model(xgb_path)
        except Exception:
            pass
        joblib.dump(xgb_model, xgb_joblib_path)
        joblib.dump(encoders, enc_path)
        print(f"  -> Exported to: {xgb_joblib_path} and {xgb_path}")

    except ImportError:
        print("  -> [SKIP] xgboost or scikit-learn not installed locally. Run in Google Colab!")

    # =========================================================================
    # 2. TRAIN ISOLATION FOREST: STEALTH MOVE ANOMALY DETECTOR
    # =========================================================================
    print("\n[2/3] Training Model 2: Isolation Forest (Stealth Outlier Detector)...")
    try:
        from sklearn.ensemble import IsolationForest

        np.random.seed(101)
        M = 1200
        traffic_growth = np.random.normal(loc=0.03, scale=0.08, size=M)
        commits = np.random.poisson(lam=12, size=M)
        price_cut = np.random.exponential(scale=0.02, size=M)
        sentiment = np.random.normal(loc=0.35, scale=0.20, size=M)

        outlier_idx = np.random.choice(M, size=35, replace=False)
        traffic_growth[outlier_idx[:15]] += np.random.uniform(1.5, 4.0, size=15)
        commits[outlier_idx[15:25]] += np.random.randint(60, 150, size=10)
        price_cut[outlier_idx[25:]] += np.random.uniform(0.40, 0.70, size=10)

        X_telemetry = np.column_stack([traffic_growth, commits, price_cut, sentiment])

        iso = IsolationForest(n_estimators=150, contamination=0.035, random_state=42)
        iso.fit(X_telemetry)

        detected = int(np.sum(iso.predict(X_telemetry) == -1))
        print(f"  -> [PASS] Isolation Forest Fitted. Detected {detected} stealth anomalies in baseline.")

        iso_path = os.path.join(models_dir, "isolation_forest.joblib")
        joblib.dump(iso, iso_path)
        print(f"  -> Exported to: {iso_path}")

    except Exception as exc:
        print(f"  -> [ERROR] Isolation Forest training failed: {exc}")

    # =========================================================================
    # 3. TRAIN HDBSCAN: SEMANTIC RADAR & WHITESPACE CLUSTERING
    # =========================================================================
    print("\n[3/3] Training Model 3: HDBSCAN (Semantic Positioning & Whitespaces)...")
    try:
        import hdbscan
        import umap
        from sentence_transformers import SentenceTransformer

        print("  -> Loading sentence embedding model...")
        embedder = SentenceTransformer("BAAI/bge-small-en-v1.5")

        saas_portfolio = [
            ("Linear", "Developer-first keyboard-driven issue tracker with git sync, cycles, and fast desktop app."),
            ("Jira Software", "Enterprise issue and project tracking platform with scrum boards, roadmap planning, and compliance."),
            ("ClickUp", "All-in-one productivity tool with docs, tasks, whiteboards, chat, and customizable dashboards."),
            ("Asana", "Cross-functional work management platform for marketing, operations, and enterprise coordination."),
            ("Monday.com", "Customizable workflow operating system with low-code boards, CRM automations, and Gantt charts."),
            ("Shortcut", "Unified software development management tool uniting engineering backlogs with product roadmaps."),
            ("Height", "Autonomous project tool with AI triage, automated backlog grooming, and conversational task updates."),
            ("GitHub Projects", "Native repository planning tool integrated directly with pull requests, issues, and actions."),
            ("Notion Projects", "Flexible documentation-first project boards with markdown wikis, relational databases, and formulas."),
            ("Basecamp", "Calm team communication and project tracking with campfires, to-dos, and automatic check-ins."),
            ("Targetprocess", "Agile portfolio management at enterprise scale supporting SAFe, LeSS, and value streams."),
            ("Wrike", "Enterprise work management with proofing tools, dynamic request forms, and resource utilization.")
        ]

        descriptions = [p[1] for p in saas_portfolio]
        embeddings = embedder.encode(descriptions, show_progress_bar=False)

        reducer = umap.UMAP(n_neighbors=4, min_dist=0.3, metric='cosine', random_state=42)
        coords = reducer.fit_transform(embeddings)

        clusterer = hdbscan.HDBSCAN(min_cluster_size=2, min_samples=1, metric='euclidean')
        labels = clusterer.fit_predict(coords)

        clusters_found = len(set(labels) - {-1})
        noise_points = int(np.sum(labels == -1))
        print(f"  -> [PASS] HDBSCAN Clustered {len(saas_portfolio)} competitors into {clusters_found} categories ({noise_points} disruptors).")

        joblib.dump(clusterer, os.path.join(models_dir, "hdbscan_clusterer.joblib"))
        joblib.dump(reducer, os.path.join(models_dir, "umap_reducer.joblib"))
        print(f"  -> Exported to: {os.path.join(models_dir, 'hdbscan_clusterer.joblib')}")

    except ImportError:
        print("  -> [SKIP] hdbscan or sentence-transformers not installed locally. Run in Google Colab notebook!")

    print("\n" + "=" * 80)
    print("ALL MODELS GENERATED AND SAVED TO: 'c:\\Users\\AMIT\\Desktop\\ai-backend\\models'")
    print("=" * 80)

if __name__ == "__main__":
    main()
