import requests
import json
import datetime

# --------- CONFIG ---------
REPO = "afyef/XP-App"  # EX: "OpenVPN/openvpn"
ASSET_NAME = "XP.ipa"  # The IPA file in your GitHub releases
ALTSTORE_FILE = "app-repo.json"
# --------------------------



def get_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    r = requests.get(url)

    if r.status_code != 200:
        raise Exception("GitHub API error:", r.text)

    data = r.json()

    tag = data["tag_name"]
    release_notes = data.get("body", "").strip()
    publish_date = data.get("published_at", "").split("T")[0]

    if not publish_date:
        publish_date = str(datetime.date.today())

    # Look for IPA asset
    for asset in data["assets"]:
        if asset["name"] == ASSET_NAME:
            download_url = asset["browser_download_url"]
            file_size = asset["size"]        # <-- file size in bytes
            return tag, download_url, release_notes, publish_date, file_size

    raise Exception(f"No asset named '{ASSET_NAME}' found in release.")


def load_altstore_file():
    with open(ALTSTORE_FILE, "r") as f:
        return json.load(f)


def save_altstore_file(data):
    with open(ALTSTORE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def main():
    tag, download_url, release_notes, publish_date, file_size = get_latest_release(REPO)

    print("Latest version:", tag)
    print("Published:", publish_date)
    print("File size:", file_size)
    print("IPA:", download_url)

    data = load_altstore_file()
    app = data["apps"][0]   # Update only first app

    # Ensure versions array exists
    if "versions" not in app or not isinstance(app["versions"], list):
        app["versions"] = []

    # Check if version already exists
    for v in app["versions"]:
        if v["version"] == tag:
            print("Already up to date.")
            return

    # Add new version entry
    new_version = {
        "version": tag,
        "date": publish_date,
        "downloadURL": download_url,
        "size": file_size,
        "localizedDescription": release_notes.replace("\r\n", "\n")
    }

    # Insert newest version at top
    app["versions"].insert(0, new_version)

    save_altstore_file(data)
    print("AltStore source updated successfully with version history.")


if __name__ == "__main__":
    main()
