import json
from pathlib import Path

def safe_load(path):
    if not Path(path).exists():
        return None
    with open(path, "r") as f:
        return json.load(f)

# Load scan outputs
semgrep = safe_load("semgrep.json") or {}
trivy = safe_load("trivy.json") or {}
gitleaks = safe_load("gitleaks.json") or []

# ================= SEMGREP =================
semgrep_results = semgrep.get("results", [])

semgrep_critical = 0
semgrep_high = 0
semgrep_secrets = 0

for r in semgrep_results:
    severity = r.get("extra", {}).get("severity", "").upper()
    rule_id = r.get("check_id", "").lower()

    if severity == "ERROR":
        semgrep_critical += 1
    elif severity == "WARNING":
        semgrep_high += 1

    if "secret" in rule_id or "password" in rule_id or "token" in rule_id:
        semgrep_secrets += 1

# ================= TRIVY =================
trivy_critical = 0
trivy_high = 0

for result in trivy.get("Results", []):
    vulns = result.get("Vulnerabilities") or []
    for v in vulns:
        sev = v.get("Severity", "").upper()
        if sev == "CRITICAL":
            trivy_critical += 1
        elif sev == "HIGH":
            trivy_high += 1

# ================= GITLEAKS =================
# gitleaks.json is an array of findings
gitleaks_findings = len(gitleaks) if isinstance(gitleaks, list) else 0

# ================= FEATURE VECTOR =================
# Order MUST match training
features = [
    semgrep_critical,
    semgrep_high,
    semgrep_secrets,
    trivy_critical,
    trivy_high,
    gitleaks_findings
]

# Jenkins-friendly output
print(" ".join(map(str, features)))
