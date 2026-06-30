import argparse
import json
import os
from src.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Multi-Source Candidate Data Transformer")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--output", default="data/outputs/output.json")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    results = run_pipeline(args.csv, config)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    valid = sum(1 for r in results if r.get("_valid"))
    print(f"Processed {len(results)} candidates -> {args.output}")
    print(f"Valid: {valid} / {len(results)}")


if __name__ == "__main__":
    main()