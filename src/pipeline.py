from src.parsers.csv_parser import parse_csv
from src.parsers.github_parser import parse_github
from src.normalizers.normalizer import normalize_record
from src.merger.merger import merge
from src.confidence.scorer import score
from src.projection.projector import project
from src.validator.validator import validate


def run_pipeline(csv_path: str, config: dict) -> list:
    results = []
    raw_csv_records = parse_csv(csv_path)

    for raw_csv in raw_csv_records:
        candidate_id = raw_csv.get("candidate_id")

        try:
            source_records = [raw_csv]

            github_url = raw_csv.get("links", {}).get("github")
            if github_url:
                raw_github = parse_github(github_url)
                if raw_github:
                    source_records.append(raw_github)
                else:
                    print(f"[pipeline] GitHub fetch failed/skipped for {candidate_id}")

            normalized_records = [normalize_record(record) for record in source_records]

            candidate = merge(normalized_records, candidate_id)

            confidence, reasons = score(candidate)
            candidate.overall_confidence = confidence

            output = project(candidate, config)
            output["candidate_id"] = candidate_id

            # Validate against the active output schema
            is_valid, errors = validate(output, config)
            output["_valid"] = is_valid

            if errors:
                output["_errors"] = errors

            results.append(output)

        except Exception as e:
            print(f"[pipeline] Unhandled error for {candidate_id}: {e}")

            results.append({
                "candidate_id": candidate_id,
                "full_name": raw_csv.get("full_name"),
                "_valid": False,
                "_errors": [f"Pipeline exception: {e}"]
            })

    return results