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

# ... existing code ...
risk_prob = model.predict_proba(features)[0][1]
print(f"[AI] Risk probability: {risk_prob:.2f}")

THRESHOLD = 0.40 

if risk_prob > THRESHOLD:
    print("[AI] DEPLOYMENT BLOCKED - Risk score too high")
    sys.exit(1) # Signal failure to Jenkins
else:
    print("[AI] DEPLOYMENT APPROVED")
    sys.exit(0)
