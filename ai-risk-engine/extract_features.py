import json
from pathlib import Path

def safe_load(path):
    p = Path(path)

    # File does not exist
    if not p.exists():
        return None

    # File exists but is empty
    if p.stat().st_size == 0:
        return None

    try:
        with open(p, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Corrupt or invalid JSON
        return None


# ================= LOAD FILES =================
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

    if any(x in rule_id for x in ["secret", "password", "token"]):
        semgrep_secrets += 1


# ================= TRIVY =================
trivy_critical = 0
trivy_high = 0

for result in trivy.get("Results", []):
    for v in result.get("Vulnerabilities") or []:
        sev = v.get("Severity", "").upper()
        if sev == "CRITICAL":
            trivy_critical += 1
        elif sev == "HIGH":
            trivy_high += 1


# ================= GITLEAKS =================
gitleaks_findings = len(gitleaks) if isinstance(gitleaks, list) else 0


# ================= FEATURE VECTOR =================
features = [
    semgrep_critical,
    semgrep_high,
    semgrep_secrets,
    trivy_critical,
    trivy_high,
    gitleaks_findings
]

print(" ".join(map(str, features)))
