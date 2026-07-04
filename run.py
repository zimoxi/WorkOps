from __future__ import annotations

import argparse

from backup_manager.server import run_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run WorkOps")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8099)
    args = parser.parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
