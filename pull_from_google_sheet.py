import os
from pathlib import Path
from urllib import request
from urllib.parse import parse_qs, urlparse

import dotenv


def download_csv_from_google_sheet(export_url: str, output_path: Path) -> None:
    """Download a published CSV export from a Google Sheet URL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with request.urlopen(export_url) as response, open(output_path, "wb") as file_handle:
        file_handle.write(response.read())

    print(f"downloaded {output_path}")


def build_csv_export_url_from_sheet_url(sheet_url: str) -> str:
    """Build a CSV export URL from a pasted Google Sheet tab URL."""
    parsed = urlparse(sheet_url.strip())
    if "google.com" not in parsed.netloc:
        raise ValueError(f"Not a Google Sheets URL: {sheet_url}")

    parts = [p for p in parsed.path.split("/") if p]
    try:
        sheet_id = parts[parts.index("d") + 1]
    except (ValueError, IndexError):
        raise ValueError(f"Missing sheet ID in sheet URL: {sheet_url}") from None

    query_gid = parse_qs(parsed.query).get("gid", [None])[0]
    fragment_gid = parse_qs(parsed.fragment).get("gid", [None])[0]
    if query_gid and fragment_gid:
        assert query_gid == fragment_gid, (
            "gid mismatch between query and fragment in sheet URL: "
            f"{sheet_url}"
        )

    tab_gid = query_gid or fragment_gid
    if not tab_gid:
        raise ValueError(f"Missing gid in sheet URL: {sheet_url}")
    if not tab_gid.isdigit():
        raise ValueError(f"gid must be numeric in sheet URL: {sheet_url}")

    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={tab_gid}"
    )


def main():
    dotenv.load_dotenv()

    sheet_url = os.getenv("EVENTS_SHEET_URL")
    if not sheet_url:
        raise ValueError("Missing env var EVENTS_SHEET_URL")
    download_csv_from_google_sheet(
        build_csv_export_url_from_sheet_url(sheet_url),
        Path("sitedata") / "events.csv",
    )


if __name__ == "__main__":
    main()
