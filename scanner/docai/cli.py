import argparse
import json
import requests
from docai.core.scanner import Scanner


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--commit", required=True)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--server", help="DocAI server URL")

    args = parser.parse_args()

    scanner = Scanner()

    result = scanner.scan(
        repo_path=args.repo,
        commit=args.commit
    )
    print(result)
    if args.server:

        try:

            requests.post(
                f"{args.server}/analyze",
                json=result
            )

        except Exception as e:

            print("Failed to send results to server:", e)

    else:

        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
