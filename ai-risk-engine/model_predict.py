import sys
import joblib
import numpy as np
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "risk_model.pkl"

if not MODEL_PATH.exists():
    print("[AI] Model file missing")
    sys.exit(1)

try:
    features = np.array([list(map(int, sys.argv[1:]))])
except Exception:
    print("[AI] Invalid feature input")
    sys.exit(1)

model = joblib.load(MODEL_PATH)

prediction = model.predict(features)[0]
risk_prob = model.predict_proba(features)[0][1]

print(f"[AI] Risk probability: {risk_prob:.2f}")

if prediction == 1:
    print("[AI] DEPLOYMENT BLOCKED")
    sys.exit(1)
else:
    print("[AI] DEPLOYMENT APPROVED")
    sys.exit(0)
