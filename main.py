import argparse
import sys
from pathlib import Path

from src.utils import scaffold_user_dir
from src.config import load_config
from src.exceptions import ConfigError, UserError
from src.pipeline import run_search, run_tailor, run_all

def main():
    parser = argparse.ArgumentParser(description="Job Pipeline CLI")
    parser.add_argument("--user", type=str, help="Username to isolate data.")
    parser.add_argument("--config", type=str, help="Path to config.yaml", default=None)
    parser.add_argument("--force", action="store_true", help="Force reprocessing of jobs.")
    parser.add_argument("--dry-run", action="store_true", help="Estimate tokens without executing actual API calls.")

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    search_parser = subparsers.add_parser("search", help="Search for jobs")
    tailor_parser = subparsers.add_parser("tailor", help="Tailor resumes and cover letters")
    all_parser = subparsers.add_parser("all", help="Run both search and tailor")

    args = parser.parse_args()

    if not args.user:
        print("UserError: --user flag is required.")
        sys.exit(1)

    user_dir = Path("users") / args.user
    user_dir.mkdir(parents=True, exist_ok=True)

    try:
        scaffold_user_dir(user_dir)

        config_path = Path(args.config) if args.config else user_dir / "config.yaml"
        if not config_path.exists():
            raise UserError(f"Missing config.yaml at {config_path}")

        config = load_config(config_path)

        if args.command == "search":
            run_search(config, user_dir)
        elif args.command == "tailor":
            run_tailor(config, user_dir, args.force, args.dry_run)
        elif args.command == "all":
            run_all(config, user_dir, args.force, args.dry_run)
        else:
            parser.print_help()
            sys.exit(1)

    except (ConfigError, UserError) as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
