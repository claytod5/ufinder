import argparse
import sys

from ufinder import ufinder


def main():

    app = ufinder.App()

    parser = argparse.ArgumentParser(
        description="Find a user and their associated network equipment",
        epilog="Please report issues to dclayton@bluegrasscellular.com",
    )
    subparsers = parser.add_subparsers(title="Commands", prog="ufinder", metavar="")

    username = subparsers.add_parser(
        "username",
        usage="ufinder username [-h] [username]",
        help="Find user by username",
    )
    username.add_argument("username", type=str, help="A username. (i.e. mjackson)")
    username.set_defaults(func=app.get_by_username)

    computer = subparsers.add_parser(
        "computer",
        usage="ufinder computer [-h] [computer_name]",
        help="Find user by computer name",
    )
    computer.add_argument(
        "computer_name", type=str, help="A computer name. (i.e.  ET1INF01)"
    )
    computer.set_defaults(func=app.get_by_machine)

    args = parser.parse_args()

    try:
        print(args.func(args))
    except AttributeError:
        parser.print_help()

    return 0

# TODO: add ability to refresh data in DB

def interactive_main():

    app = ufinder.App()

    print(
        """Welcome to ufinder!

    Please report any issues to dclayton@bluegrasscellular.com"""
    )

    search_method_prompt = """
    
    How would you like to search?

    [1] Username
    [2] Computer

    [0] Exit

    """

    while True:
        print(search_method_prompt)
        search_method = input("Selection: ")

        if search_method == "1":
            query = input("Username: ")
            try:
                app.get_by_username(query)
            except IndexError:
                print("\nQuery Failed. Is the username correct?")
        elif search_method == "2":
            query = input("Computer: ")
            try:
                app.get_by_machine(query)
            except IndexError:
                print("\nQuery Failed. Is the computer name correct?")
        elif search_method == "0":
            sys.exit()
        else:
            print("\nInvalid Selection. Please select an option from the list.")


if __name__ == "__main__":
    main()
