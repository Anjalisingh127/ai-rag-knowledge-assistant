import json

from app.evaluation.runner import (
    run_retrieval_evaluation,
    write_evaluation_report,
)


def main() -> None:
    result = run_retrieval_evaluation(top_k=5)
    output = write_evaluation_report(result)

    printable = {key: value for key, value in result.items() if key != "failures"}
    print(json.dumps(printable, indent=2))
    print(f"Failures: {len(result['failures'])}")
    print(f"Report: {output}")


if __name__ == "__main__":
    main()
