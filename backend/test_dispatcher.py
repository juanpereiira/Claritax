import json

from app.services.pipeline_service import (
    get_queue_path,
    process_queued_documents
)


def main():
    queue_path = get_queue_path()

    print("\nQUEUE FILE:", queue_path)

    if not queue_path.exists():
        print("\nNo processing queue found.")
        return

    print("\nCLASSIFICATION RESULTS")
    print("=" * 60)

    results = process_queued_documents()

    if not results:
        print("No queued documents found.")
        return

    for result in results:
        print(json.dumps(result, indent=4, ensure_ascii=False))
        print("-" * 60)


if __name__ == "__main__":
    main()