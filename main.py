import sys
import json
import requests
from datetime import datetime, timedelta
from dateutil import parser

from jinja2 import Environment, FileSystemLoader

def download_data(name: str, base_url: str, username: str, password: str) -> dict:
    s = requests.Session()
    # Login
    resp = s.post(
        f"{base_url}api/login",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=f"client_id=ANDR&grant_type=password&username={username}&password={password}"
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to authenticate {name}")

    token = resp.json()["access_token"]

    # get homeworks
    resp = s.get(
        f"{base_url}/api/3/homeworks",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to download homeworks {name}")

    homeworks = resp.json()

    resp = s.post(
        f"{base_url}/api/3/komens/messages/received",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to download komens {name}")
    komens = resp.json()

    return {
        "name": name,
        "homeworks": homeworks,
        "komens": komens,
    }


def main():
    if len(sys.argv) != 2:
        raise RuntimeError("Requires path to logins.json")

    try:
        with open(sys.argv[1]) as f:
            logins = json.load(f)
    except Exception as e:
        print("Unable to load logins")
        raise e

    context = {
        "now": datetime.now(),
        "records": [
            download_data(**e) for e in logins
        ]
    }

    # render jinja template
    env = Environment(loader = FileSystemLoader('templates'))
    env.filters["to_date_repr"] = lambda value: value.strftime("%Y-%m-%d")
    env.filters["from_iso_to_date"] = lambda value: parser.parse(value)
    env.filters["fire"] = lambda value: value.date() <= (datetime.now() + timedelta(days=1)).date()
    env.filters["active_homeworks"] = lambda homeworks: [e for e in homeworks if not e["Closed"] and not e["Finished"]]
    env.filters["unread_komens"] = lambda komens: [e for e in komens if not e["Read"]]
    template = env.get_template("summary.html")
    output = template.render(**context)
    print(output)



if __name__ == "__main__":
    main()
