"""Command-line client for testing the secure upload protocol."""
import argparse
import json
from client.network.upload_worker import upload_file


def main():
    parser = argparse.ArgumentParser(description="Upload a file to the LTM Group 13 server")
    parser.add_argument("file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    result = upload_file(args.host, args.port, args.file, args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
