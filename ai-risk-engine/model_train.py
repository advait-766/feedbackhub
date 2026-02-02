import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path

# Feature order:
# [semgrep_critical, semgrep_high, semgrep_secrets, 
#  trivy_critical, trivy_high, gitleaks_findings]

X = np.array([
    # --- SAFE SCENARIOS (y=0) ---
    [0, 0, 0, 0, 0, 0],  # Perfectly clean
    [0, 1, 0, 0, 2, 0],  # A few low/medium warnings
    [0, 2, 0, 0, 1, 0],  # Minor code smells
    [0, 0, 0, 0, 3, 0],  # Some medium container vulnerabilities
    
    # --- RISKY SCENARIOS (y=1) ---
    [1, 0, 0, 0, 0, 0],  # Even 1 Critical Semgrep issue is a fail
    [0, 0, 1, 0, 0, 0],  # A secret found by Semgrep
    [0, 0, 0, 1, 0, 0],  # A Critical Trivy vulnerability
    [0, 0, 0, 0, 0, 1],  # A single Gitleaks secret finding
    [2, 3, 1, 2, 4, 1],  # Multiple failures (Extreme Risk)
    [0, 5, 0, 0, 10, 0], # High density of medium/high issues
    [1, 1, 0, 1, 1, 0],  # Mixed critical/high issues
    [0, 0, 0, 0, 0, 2],  # Multiple leaked secrets
])

y = np.array([
    0, 0, 0, 0, # Safe
    1, 1, 1, 1, 1, 1, 1, 1 # Risky
])

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    random_state=42
)

# Train the model
model.fit(X, y)

# Save the model to the current directory
MODEL_PATH = Path(__file__).parent / "risk_model.pkl"
joblib.dump(model, MODEL_PATH)

print(f"========================================")
print(f"[AI] Model training complete.")
print(f"[AI] Saved to: {MODEL_PATH}")
print(f"========================================")

test_case = np.array([[1, 0, 0, 1, 0, 1]]) 
prob = model.predict_proba(test_case)[0][1]
pred = model.predict(test_case)[0]

print(f"Test Case [1, 0, 0, 1, 0, 1] Result:")
print(f"Probability of Risk: {prob:.2f}")
print(f"Prediction: {'BLOCK' if pred == 1 else 'APPROVE'}")
