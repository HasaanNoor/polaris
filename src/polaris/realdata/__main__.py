"""Command line entry point for Phase 11 validation."""

from polaris.realdata.runner import run_real_dataset_validation


def main() -> None:
    result = run_real_dataset_validation()
    print(result.model_dump_json(indent=2, exclude={"report"}))


if __name__ == "__main__":
    main()
