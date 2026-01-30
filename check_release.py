import requests
import json
import datetime
import re

# --------- CONFIG ---------
REPO = "afyef/XP-App"        # GitHub repo
ASSET_NAME = "XP.ipa"        # Expected IPA name (fallback: any .ipa)
ALTSTORE_FILE = "app-repo.json"
# --------------------------


def clean_markdown(md: str) -> str:
    """Clean GitHub markdown so AltStore renders it correctly."""
    if not md:
        return ""

    md = md.replace("\r\n", "\n").replace("\r", "\n")

    # Remove indentation before headings
    md = re.sub(r"\n\s+(#{1,6}\s)", r"\n\1", md)

    # Remove code fences
    md = md.replace("```", "")

    # Remove indentation that creates code blocks
    md = re.sub(r"\n {2,}", "\n", md)

    # Remove tabs
    md = md.replace("\t", " ")

    # Trim trailing whitespace
    md = "\n".join(line.rstrip() for line in md.split("\n"))

    return md.strip()


def get_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases"
    r = requests.get(url)

    if r.status_code != 200:
        raise Exception("GitHub API error:", r.text)

    releases = r.json()

    ios_release = None
    ipa_asset = None

    # Find the newest release that contains an IPA
    for rel in releases:
        for asset in rel.get("assets", []):
            if asset["name"] == ASSET_NAME or asset["name"].endswith(".ipa"):
                ios_release = rel
                ipa_asset = asset
                break
        if ios_release:
            break

    if not ios_release or not ipa_asset:
        raise Exception("No iOS IPA release found.")

    tag = ios_release["tag_name"].lstrip("v")

    raw_notes = ios_release.get("body", "").strip()
    release_notes = clean_markdown(raw_notes)

    publish_date = ios_release.get("published_at", "").split("T")[0]
    if not publish_date:
        publish_date = str(datetime.date.today())

    today = str(datetime.date.today())
    if publish_date > today:
        publish_date = today

    download_url = ipa_asset["browser_download_url"]
    file_size = ipa_asset["size"]

    return tag, download_url, release_notes, publish_date, file_size


def load_altstore_file():
    with open(ALTSTORE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_altstore_file(data):
    with open(ALTSTORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def fix_raw_github_url(url: str):
    """Fix GitHub raw URLs containing /refs/heads/"""
    return url.replace("/refs/heads/", "/")


def main():
    tag, download_url, release_notes, publish_date, file_size = get_latest_release(REPO)

    print("Latest version:", tag)
    print("Published:", publish_date)
    print("File size:", file_size)
    print("IPA:", download_url)

    data = load_altstore_file()
    app = data["apps"][0]

    # Fix bad raw URLs
    app["iconURL"] = fix_raw_github_url(app["iconURL"])
    if "headerURL" in app:
        app["headerURL"] = fix_raw_github_url(app["headerURL"])
    if "screenshots" in app:
        for shot in app["screenshots"]:
            shot["imageURL"] = fix_raw_github_url(shot["imageURL"])

    # Fix incorrect /n usage
    if "localizedDescription" in app:
        app["localizedDescription"] = (
            app["localizedDescription"]
            .replace("/n", "\n")
            .replace("/n ", "\n")
        )

    # Ensure versions array exists
    if "versions" not in app or not isinstance(app["versions"], list):
        app["versions"] = []

    # Prevent duplicate versions
    for v in app["versions"]:
        if v["version"] == tag:
            print("Already up to date.")
            return

    new_version = {
        "version": tag,
        "date": publish_date,
        "bundleIdentifier": app["bundleIdentifier"],
        "downloadURL": download_url,
        "size": file_size,
        "localizedDescription": release_notes or f"Updated to {tag}"
    }

    # Insert newest version at the top
    app["versions"].insert(0, new_version)

    save_altstore_file(data)
    print("AltStore source updated successfully with version history.")


if __name__ == "__main__":
    main()
