import argparse
import sys
import time

from ufinder import ufinder


def interactive_main():

    app = ufinder.App()

    # TODO: make this happen the first time, but not afterwards
    if app.config["first_time"]:
        print(
            """Welcome to ufinder!

        You will want to gather data from your Meraki dashboard and initialize the
        database. Once that is complete, you can begin searching!

        Would you like to do this now?
        """
        )
        initialize_response = input("(Y/N): ")
        if initialize_response:
            print("Setting up database\n")
            app.db.init_db()
        else:
            print("Goodbye!")
            time.sleep(1)
            sys.exit(1)

    search_method_prompt = """

    How would you like to search?

    [1] Username
    [2] Computer
    [3] Refresh data in database

    [0] Exit

    """

    while True:
        print(search_method_prompt)
        menu_choice = input("Selection: ")

        if menu_choice == "1":
            query = input("Username: ")
            try:
                app.get_by_username(query)
            except IndexError:
                print("\nQuery Failed. Is the username correct?")
        elif menu_choice == "2":
            query = input("Computer: ")
            try:
                app.get_by_machine(query)
            except IndexError:
                print("\nQuery Failed. Is the computer name correct?")
        elif menu_choice == "3":
            warning = input(
                """This action will recreate the local database using data
                    from the Meraki Dashboard.

                    Are you sure you want to proceed? (Y/N) """
            )
            if warning == "Y":
                app.db.init_db()
        elif menu_choice == "0":
            sys.exit()
        else:
            print("\nInvalid Selection. Please select an option from the list.")


if __name__ == "__main__":
    main()
