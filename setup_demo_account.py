import argparse
import sys
from getpass import getpass

from app.repositories.account_repo import AccountRepo
from app.repositories.restaurant_repo import RestaurantRepo
from app.services.account_service import AccountExistsError
from app.services.demo_account_service import DemoAccountError, DemoAccountService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a local staff account for demos.")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", required=True, choices=["admin", "restaurant_user"])
    parser.add_argument(
        "--restaurant-id", type=int, action="append", default=[],
        help="Assign an existing restaurant; repeat for more than one.")
    args = parser.parse_args(argv)

    try:
        # prompt instead of putting the password in command history
        password = getpass("Password (12-128 characters): ")
        confirmation = getpass("Confirm password: ")
        if password != confirmation:
            print("Passwords do not match.", file=sys.stderr)
            return 1

        service = DemoAccountService(AccountRepo(), RestaurantRepo())
        account = service.create(
            args.name, args.email, password, args.role, args.restaurant_id)
    except (DemoAccountError, AccountExistsError) as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print("Could not read or save demo data. Check DATA_DIR and its JSON files.", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("Setup cancelled.", file=sys.stderr)
        return 1

    print(f"Created {account['role']} account with ID {account['id']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
