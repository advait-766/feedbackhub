import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path

# Feature order:
# [semgrep_critical, semgrep_high, semgrep_secrets,
#  trivy_critical, trivy_high, gitleaks_findings]

X = np.array([
    [0, 0, 0, 0, 0, 0],  # clean
    [0, 1, 0, 0, 1, 0],  # minor issues
    [0, 0, 1, 0, 0, 1],  # secrets detected
    [1, 2, 1, 0, 0, 0],  # code risks
    [0, 0, 0, 1, 2, 0],  # container vulns
    [2, 3, 1, 2, 4, 1],  # high risk
    [1, 0, 0, 1, 0, 0],  # mixed
    [0, 0, 0, 0, 0, 2],  # gitleaks only
])

# 0 = SAFE, 1 = RISKY
y = np.array([
    0,
    0,
    1,
    1,
    1,
    1,
    1,
    1,
])

model = RandomForestClassifier(
    n_estimators=150,
    random_state=42
)

model.fit(X, y)

MODEL_PATH = Path(__file__).parent / "risk_model.pkl"
joblib.dump(model, MODEL_PATH)

print(f"[AI] Model trained and saved to {MODEL_PATH}")
