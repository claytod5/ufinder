# import sqlite3
# import time
# 
# import requests
# 
# # TODO: move these configs to config file
# 
# meraki_token = "3ba6162de4996e03b48d150093d6de3c8bb12df2"
# meraki_host = "https://api.meraki.com/api/v0"
# org_id = 749680
# vlan = 101
# 
# 
# def populate_data(cursor_obj):
#     with requests.Session() as s:
#         s.headers = {"X-Cisco-Meraki-API-Key": meraki_token}
#         nets = s.get(f"{meraki_host}/organizations/{org_id}/networks")
#         subnets = []
#         for each in nets.json():
#             if each["name"].startswith("Remote"):
#                 net_id = each["id"]
#                 subnet = s.get(f"{meraki_host}/networks/{net_id}/vlans/{vlan}")
#                 while subnet.status_code == 429:
#                     print("Retry: ", subnet.headers["Retry-After"])
#                     time.sleep(int(subnet.headers["Retry-After"]))
#                     subnet = s.get(f"{meraki_host}/networks/{net_id}/vlans/{vlan}")
#                 if subnet.status_code == 200:
#                     print(subnet)
#                     subnet = subnet.json()
#                     subnets.append((subnet["subnet"], each["name"]))
# 
#     cursor_obj.executemany(
#         "INSERT INTO meraki (subnet, network_name) VALUES (?, ?)", subnets
#     )
# 
# 
# def init_db():
#     con = sqlite3.connect("meraki.sqlite")
#     con.row_factory = sqlite3.Row
#     cur = con.cursor()
# 
#     with open("schema.sql", "rt") as f:
#         cur.executescript(f.read())
# 
#     populate_data(cur)
# 
#     con.commit()
#     con.close()
# 
# 
# if __name__ == "__main__":
#     init_db()
