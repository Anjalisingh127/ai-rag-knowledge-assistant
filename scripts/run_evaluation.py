import argparse
import json

from app.evaluation.runner import (
    run_retrieval_evaluation,
    write_evaluation_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate RAG retrieval quality."
    )

    parser.add_argument(
        "--embedding",
        choices=("hash", "minilm"),
        default="hash",
        help="Embedding strategy used during evaluation.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of retrieval results to evaluate.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    result = run_retrieval_evaluation(
        top_k=args.top_k,
        embedding_strategy=args.embedding,
    )
    output = write_evaluation_report(result)

    printable = {
        key: value
        for key, value in result.items()
        if key != "failures"
    }

    print(json.dumps(printable, indent=2))
    print(f"Failures: {len(result['failures'])}")
    print(f"Report: {output}")


if __name__ == "__main__":
    main()