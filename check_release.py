import requests
import json
import datetime
import re

# --------- CONFIG ---------
REPO = "afyef/XP-App"  # EX: "OpenVPN/openvpn"
ASSET_NAME = "XP.ipa"  # The IPA file in your GitHub releases
ALTSTORE_FILE = "app-repo.json"
# --------------------------


def clean_markdown(md: str) -> str:
    """Cleans GitHub markdown so AltStore renders it correctly."""
    if not md:
        return ""

    md = md.replace("\r\n", "\n").replace("\r", "\n")

    # Remove random indentation that breaks AltStore
    md = re.sub(r"\n\s+(#{1,6}\s)", r"\n\1", md)

    # Remove accidental code blocks
    md = md.replace("```", "")

    # Remove double spaces that cause preformatted blocks
    md = re.sub(r"\n {2,}", "\n", md)

    # Remove tabs
    md = md.replace("\t", " ")

    # Strip trailing whitespace
    md = "\n".join(line.rstrip() for line in md.split("\n"))

    return md.strip()


def get_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    r = requests.get(url)

    if r.status_code != 200:
        raise Exception("GitHub API error:", r.text)

    data = r.json()

    # Remove "v" prefix if present
    tag = data["tag_name"].lstrip("v")

    raw_notes = data.get("body", "").strip()
    release_notes = clean_markdown(raw_notes)

    publish_date = data.get("published_at", "").split("T")[0]
    if not publish_date:
        publish_date = str(datetime.date.today())

    # Ensure date is not in the future (AltStore rejects future dates)
    today = str(datetime.date.today())
    if publish_date > today:
        publish_date = today

    # Look for IPA asset
    for asset in data["assets"]:
        if asset["name"] == ASSET_NAME:
            download_url = asset["browser_download_url"]
            file_size = asset["size"]        # bytes
            return tag, download_url, release_notes, publish_date, file_size

    raise Exception(f"No asset named '{ASSET_NAME}' found in release.")


def load_altstore_file():
    with open(ALTSTORE_FILE, "r") as f:
        return json.load(f)


def save_altstore_file(data):
    with open(ALTSTORE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def fix_raw_github_url(url: str):
    """Fixes GitHub raw URLs using /refs/heads/ which AltStore rejects."""
    return url.replace("/refs/heads/", "/")


def main():
    tag, download_url, release_notes, publish_date, file_size = get_latest_release(REPO)

    print("Latest version:", tag)
    print("Published:", publish_date)
    print("File size:", file_size)
    print("IPA:", download_url)

    data = load_altstore_file()
    app = data["apps"][0]   # Update only first app

    # Fix known bad URLs
    app["iconURL"] = fix_raw_github_url(app["iconURL"])
    if "headerURL" in app:
        app["headerURL"] = fix_raw_github_url(app["headerURL"])
    if "screenshots" in app:
        for shot in app["screenshots"]:
            shot["imageURL"] = fix_raw_github_url(shot["imageURL"])

    # Fix /n → \n
    if "localizedDescription" in app:
        app["localizedDescription"] = app["localizedDescription"].replace("/n", "\n").replace("/n ", "\n")

    # Ensure versions array exists
    if "versions" not in app or not isinstance(app["versions"], list):
        app["versions"] = []

    # Check if version already exists
    for v in app["versions"]:
        if v["version"] == tag:
            print("Already up to date.")
            return

    # Create version entry
    new_version = {
        "version": tag,
        "date": publish_date,
        "bundleIdentifier": app["bundleIdentifier"],
        "downloadURL": download_url,
        "size": file_size,
        "localizedDescription": release_notes or f"Updated to {tag}"
    }

    # Insert newest version at top
    app["versions"].insert(0, new_version)

    save_altstore_file(data)
    print("AltStore source updated successfully with version history.")


if __name__ == "__main__":
    main()
