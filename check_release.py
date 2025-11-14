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
    publish_date = data.get("published_at", None)

    # convert publish date to yyyy-mm-dd
    if publish_date:
        publish_date = publish_date.split("T")[0]
    else:
        publish_date = str(datetime.date.today())

    # find asset URL matching ASSET_NAME
    for asset in data["assets"]:
        if asset["name"] == ASSET_NAME:
            return tag, asset["browser_download_url"], release_notes, publish_date

    raise Exception(f"No asset named '{ASSET_NAME}' found in release.")


def load_altstore_file():
    with open(ALTSTORE_FILE, "r") as f:
        return json.load(f)


def save_altstore_file(data):
    with open(ALTSTORE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def main():
    tag, download_url, release_notes, publish_date = get_latest_release(REPO)

    print("Latest tag:", tag)
    print("Publish date:", publish_date)
    print("Download:", download_url)

    data = load_altstore_file()
    app = data["apps"][0]   # update only the first app

    # If version hasn't changed, nothing to do
    if app["versions"] == tag:
        print("Already up to date.")
        return

    # Write updates
    app["versions"] = [
    {
        "version": tag,
        "date": publish_date,
        "downloadURL": download_url,
        "localizedDescription": release_notes.replace("\r\n", "\n")
    }

    # Add release notes to versionDescription
    if release_notes:
        app["versionDescription"] = release_notes
    else:
        app["versionDescription"] = f"Updated to version {tag}"

    save_altstore_file(data)
    print("AltStore source updated successfully.")


if __name__ == "__main__":
    main()
