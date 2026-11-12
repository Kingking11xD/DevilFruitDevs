import argparse
import os
import subprocess
import sys
from getpass import getpass
from pathlib import Path

from app.repositories.account_repo import AccountRepo
from app.repositories.restaurant_repo import RestaurantRepo
from app.services.account_service import AccountExistsError
from app.services.demo_account_service import DemoAccountError, DemoAccountService


PROJECT_ROOT = Path(__file__).resolve().parent
DEMO_DIR = Path.home() / ".devilfruitdevs-demo"


def read_password() -> str:
    # prompt instead of putting the password in command history
    options = {"echo_char": "*"} if sys.version_info >= (3, 14) else {}
    password = getpass("Password (12-128 characters): ", **options)
    if password != getpass("Confirm password: ", **options):
        raise DemoAccountError("Passwords do not match.")
    return password


def run_demo() -> int:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Demo data: {DEMO_DIR}")

    for filename in ["restaurants.json", "menu_items.json", "accounts.json"]:
        destination = DEMO_DIR / filename
        if destination.exists():
            continue
        if filename == "accounts.json":
            contents = "[]\n"
        else:
            contents = (PROJECT_ROOT / "data" / filename).read_text(encoding="utf-8")
        # create missing files only. account changes still go through the repository
        with destination.open("x", encoding="utf-8") as file:
            file.write(contents)

    accounts = AccountRepo(DEMO_DIR / "accounts.json")
    restaurants = RestaurantRepo(DEMO_DIR / "restaurants.json")
    saved_restaurants = restaurants.get_all()
    if not saved_restaurants:
        raise DemoAccountError("Add a restaurant to the demo data before starting.")

    service = DemoAccountService(accounts, restaurants)
    password = None
    for name, email, role, restaurant_ids in [
            ("Bulma", "bulma@email.com", "admin", []),
            ("Vegeta", "vegeta@email.com", "restaurant_user", [saved_restaurants[0]["id"]])]:
        if accounts.get_by_email(email) is not None:
            print(f"Keeping {email}; use its existing password.")
            continue
        if password is None:
            print("Choose one password for the new demo accounts.")
            password = read_password()
        service.create(name, email, password, role, restaurant_ids)
        print(f"Created {email} ({role}).")

    print("Open http://127.0.0.1:8000/docs and sign in through POST /auth/login.")
    print("Press Ctrl+C to stop the demo backend.", flush=True)
    environment = os.environ.copy()
    environment["DATA_DIR"] = str(DEMO_DIR)
    return subprocess.run(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=PROJECT_ROOT, env=environment).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a local staff account for demos.")
    parser.add_argument("--demo", action="store_true", help="Prepare demo accounts and start the backend.")
    parser.add_argument("--name")
    parser.add_argument("--email")
    parser.add_argument("--role", choices=["admin", "restaurant_user"])
    parser.add_argument(
        "--restaurant-id", type=int, action="append", default=[],
        help="Assign an existing restaurant; repeat for more than one.")
    args = parser.parse_args(argv)

    if args.demo and (args.name or args.email or args.role or args.restaurant_id):
        parser.error("Use --demo on its own.")
    if not args.demo and not (args.name and args.email and args.role):
        parser.error("Provide --name, --email and --role, or use --demo.")

    try:
        if args.demo:
            return run_demo()

        password = read_password()
        service = DemoAccountService(AccountRepo(), RestaurantRepo())
        account = service.create(
            args.name, args.email, password, args.role, args.restaurant_id)
    except (DemoAccountError, AccountExistsError) as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print("Could not read or save demo data. Check the data folder and JSON files.", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("Setup cancelled.", file=sys.stderr)
        return 1

    print(f"Created {account['role']} account with ID {account['id']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
