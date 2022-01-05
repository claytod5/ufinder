import getpass
import ipaddress
import json
import pathlib
import sqlite3
import sys
import time
from base64 import urlsafe_b64encode
from pprint import pprint

import requests

# TODO: support connection errors


class App:
    def __init__(self, config_file=pathlib.Path.home() / ".ufinder" / "config.json"):

        try:
            with open(config_file, "rt") as f:
                self.config = json.load(f)
        except OSError:
            print(f"Cannot open {config_file}")
            sys.exit(1)

        self.dc_url = "{host}{api}".format(
            host=self.config["dc_host"],
            api=self.config["dc_api"],
        )
        requests.packages.urllib3.disable_warnings()

        self.user = User(self.config, config_file)
        self.db = Database(self.config)

    def get_by_username(self, args):
        try:
            username = args.username
        except AttributeError:
            username = args
        params = {
            "searchtype": "agent_logged_on_users",
            "searchcolumn": "agent_logged_on_users",
            "searchvalue": username,
        }
        response = self._make_request(
            self.user.dc_token, self.dc_url, "/som/computers", params=params
        )
        res_json = response.json()["message_response"]["computers"][0]
        ip_address = res_json["ip_address"]
        machine = res_json["resource_name"]
        ip, network, subnet = self._correlate_ip(ip_address)
        return self._print_data(username, machine, ip, network, subnet)

    def get_by_machine(self, args):
        try:
            machine = args.computer_name
        except AttributeError:
            machine = args
        params = {
            "searchtype": "resource_name",
            "searchcolumn": "resource_name",
            "searchvalue": machine,
        }
        response = self._make_request(
            self.user.dc_token, self.dc_url, "/som/computers", params=params
        )
        res_json = response.json()["message_response"]["computers"][0]
        ip_address = res_json["ip_address"]
        username = res_json["agent_logged_on_users"]
        try:
            ip, network, subnet = self._correlate_ip(ip_address)
        except TypeError:
            ip, network, subnet = "Not Found", "Not Found", "Not Found"
        return self._print_data(username, machine, ip, network, subnet)

    def _make_request(self, token, url, resource, params=""):
        headers = {"Authorization": token}
        url = f"https://{url}{resource}"

        return requests.get(url, headers=headers, params=params, verify=False)

    def _correlate_ip(self, ip):
        ip_list = ip.split(",")
        ip = [each for each in ip_list if each.startswith("10.175.")]
        ip = ip.pop()
        net = "/29" if ip.startswith("10.175.250") else "/30"

        ip_address = ipaddress.IPv4Interface(f"{ip}{net}")
        cur = self.db.cursor()
        cur.execute(
            "SELECT * FROM meraki WHERE subnet = :subnet",
            {"subnet": str(ip_address.network)},
        )
        network, subnet = cur.fetchone()

        return ip, network, subnet

    def _print_data(self, username, machine, ip, network_name, subnet):
        print("\n")
        columns = ["Username", "Machine", "IP Address", "Network", "Subnet"]
        underlines = ["-" * len(each) for each in columns]
        args = [username, machine, ip, network_name, subnet]

        for each in [columns, underlines, args]:
            print("{:<20s} {:<20s} {:<20s} {:<20s} {:<20s}".format(*each))
        return "\n"


class User:
    def __init__(self, config, config_file):
        self.dc_token = config["dc_token"]
        self.dc_url = "{host}{api}".format(
            host=config["dc_host"],
            api=config["dc_api"],
        )
        self.config_file = config_file
        self.config = config

        if self.dc_token == "":
            self.dc_token = self._new_dc_token()

    def _new_dc_token(self):
        username = getpass.getuser()
        password = getpass.getpass("AD Password: ")
        encoded_password = urlsafe_b64encode(password.encode("utf-8")).decode("utf-8")
        domain = self.config["domain"]
        auth_url = f"https://{self.dc_url}/desktop/authentication"
        params = {
            "username": username,
            "password": encoded_password,
            "auth_type": "ad_authentication",
            "domainName": domain,
        }
        response = requests.get(auth_url, params=params, verify=False).json()
        try:
            return self._update_token(
                response["message_response"]["authentication"]["auth_data"][
                    "auth_token"
                ]
            )
        except KeyError:
            print(response["error_description"])
            sys.exit(1)

    def _update_token(self, token):
        self.config["dc_token"] = token

        with open(self.config_file, "wt") as f:
            json.dump(self.config, f)

        return token


class Database:
    def __init__(self, config):
        self.config = config
        self.meraki_token = self.config["meraki_token"]
        self.meraki_host = self.config["meraki_host"]
        self.org_id = self.config["org_id"]
        self.vlan = self.config["vlan"]

        self.url = pathlib.Path.home() / ".ufinder" / "meraki.sqlite"

        try:
            self.conn = sqlite3.connect(self.url)

        except OSError:
            print("Cannot open {}".format(self.url))
            sys.exit(1)

        else:
            self.conn.row_factory = sqlite3.Row
            self.cur = self.conn.cursor()

    def _populate_data(self):
        with requests.Session() as s:
            s.headers = {"X-Cisco-Meraki-API-Key": self.meraki_token}
            nets = s.get(f"{self.meraki_host}/organizations/{self.org_id}/networks")
            subnets = []
            for each in nets.json():
                if each["name"].startswith("Remote"):
                    net_id = each["id"]
                    subnet = s.get(
                        f"{self.meraki_host}/networks/{net_id}/vlans/{self.vlan}"
                    )
                    while subnet.status_code == 429:
                        print("Retry: ", subnet.headers["Retry-After"])
                        time.sleep(int(subnet.headers["Retry-After"]))
                        subnet = s.get(
                            f"{self.meraki_host}/networks/{net_id}/vlans/{self.vlan}"
                        )
                    if subnet.status_code == 200:
                        print(subnet)
                        subnet = subnet.json()
                        subnets.append((subnet["subnet"], each["name"]))

        self.cur.executemany(
            "INSERT INTO meraki (subnet, network_name) VALUES (?, ?)", subnets
        )

    def init_db(self):
        db_schema = pathlib.Path.home() / "schema.sql"

        with open(db_schema, "rt") as f:
            self.cur.executescript(f.read())

        self._populate_data()

        self.conn.commit()
        self.conn.close()
