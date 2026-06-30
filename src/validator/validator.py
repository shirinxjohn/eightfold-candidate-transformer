from typing import List, Tuple


def validate(output: dict, config: dict) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    # Always required
    if not output.get("candidate_id"):
        errors.append("Missing required field: candidate_id")

    # Required fields defined by the active config
    for field in config.get("fields", []):
        if field.get("required"):
            key = field.get("path")

            if key not in output or output.get(key) in (None, "", []):
                errors.append(f"Missing required field: {key}")

    # Validate email format
    for key in ("primary_email", "emails"):
        if key in output and output[key]:
            vals = output[key] if isinstance(output[key], list) else [output[key]]
            for e in vals:
                if e and "@" not in str(e):
                    errors.append(f"Invalid email format: {e}")

    # Validate phone format (E.164)
    for key in ("phone", "phones"):
        if key in output and output[key]:
            vals = output[key] if isinstance(output[key], list) else [output[key]]
            for p in vals:
                if p and not str(p).startswith("+"):
                    errors.append(f"Phone not in E.164 format: {p}")

    # Check duplicate values
    for key in ("emails", "phones"):
        if key in output and isinstance(output[key], list):
            if len(output[key]) != len(set(output[key])):
                errors.append(f"Duplicate values found in {key}")

    # Validate confidence score
    if "overall_confidence" in output:
        conf = output["overall_confidence"]
        if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
            errors.append("overall_confidence must be a number between 0 and 1")

    return len(errors) == 0, errors