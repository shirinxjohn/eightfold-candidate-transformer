import re
from typing import Dict, Any, List
from src.models.candidate import Candidate


def get_nested(data: dict, path: str) -> Any:
    """
    Supports: 'full_name', 'links.github', 'emails[0]', 'skills[].name'
    """
    if not path:
        return None

    # array map: skills[].name
    m = re.match(r'^(\w+)\[\]\.(.+)$', path)
    if m:
        key, subpath = m.group(1), m.group(2)
        arr = data.get(key, [])
        if not isinstance(arr, list):
            return None
        return [get_nested(item, subpath) for item in arr if isinstance(item, dict)]

    # array index: emails[0]
    m = re.match(r'^(\w+)\[(\d+)\](.*)$', path)
    if m:
        key, idx, rest = m.group(1), int(m.group(2)), m.group(3)
        arr = data.get(key, [])
        if not isinstance(arr, list) or len(arr) <= idx:
            return None
        item = arr[idx]
        return get_nested(item, rest.lstrip(".")) if rest else item

    # dotted path: links.github
    if "." in path:
        head, rest = path.split(".", 1)
        sub = data.get(head)
        return get_nested(sub, rest) if isinstance(sub, dict) else None

    return data.get(path)


def set_nested(output: dict, path: str, value: Any) -> None:
    """Sets output[path] = value. Output paths in this assignment are flat keys,
    but kept generic in case future configs request nested output shapes."""
    if "." not in path:
        output[path] = value
        return
    head, rest = path.split(".", 1)
    output.setdefault(head, {})
    set_nested(output[head], rest, value)


def project(candidate: Candidate, config: dict) -> dict:
    data = candidate.to_dict()
    fields_config = config.get("fields", [])
    include_confidence = config.get("include_confidence", True)
    include_provenance = config.get("include_provenance", True)
    on_missing = config.get("on_missing", "null")

    output: Dict[str, Any] = {}

    for field_def in fields_config:
        out_path = field_def["path"]
        from_path = field_def.get("from", out_path)
        required = field_def.get("required", False)
        normalize = field_def.get("normalize")
        output_type = field_def.get("type", "string")

        value = get_nested(data, from_path)
        value = _apply_normalize(value, normalize)
        value = _cast(value, output_type)

        is_missing = value is None or value == [] or value == ""
        if is_missing:
            if on_missing == "omit":
                continue
            if on_missing == "error" and required:
                raise ValueError(f"Required field '{out_path}' is missing and on_missing=error")
            set_nested(output, out_path, None)
        else:
            set_nested(output, out_path, value)

    if include_confidence:
        set_nested(output, "overall_confidence", data.get("overall_confidence", 0.0))
    if include_provenance:
        set_nested(output, "provenance", data.get("provenance", {}))

    return output


def _apply_normalize(value, normalize):
    if not normalize or value is None:
        return value
    if normalize == "E164":
        from src.normalizers.normalizer import normalize_phone
        return [normalize_phone(v) for v in value] if isinstance(value, list) else normalize_phone(value)
    if normalize == "canonical":
        from src.normalizers.normalizer import normalize_skill
        return [normalize_skill(v) for v in value] if isinstance(value, list) else normalize_skill(value)
    return value


def _cast(value, output_type):
    if value is None:
        return None
    if output_type == "string" and not isinstance(value, str):
        return str(value)
    if output_type == "string[]" and not isinstance(value, list):
        return [value]
    if output_type == "number" and not isinstance(value, (int, float)):
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    return value