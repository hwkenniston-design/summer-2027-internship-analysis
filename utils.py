"""
Internship Postings — helper functions.

Data comes from the SimplifyJobs / Pitt CSC Summer 2027 internships repo,
which publishes every listing as a single JSON file and updates it hourly.
"""

import json
import urllib.request
from datetime import date, datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

LISTINGS_URL = (
    "https://raw.githubusercontent.com/SimplifyJobs/"
    "Summer2027-Internships/dev/.github/scripts/listings.json"
)

# The categories in the raw file. "AI/ML/Data" is the one we care about;
# change this if you want to compare against Software or Quant.
CATEGORY = "AI/ML/Data"
TERM = "Summer 2027"


def fetch_listings():
    """
    Download the full listings file and return it as a DataFrame.

    One request gets everything — roughly 17,000 postings, no pagination
    and no API key. The file is about 12 MB so this takes a few seconds.
    """
    req = urllib.request.Request(
        LISTINGS_URL,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    raw = json.loads(urllib.request.urlopen(req, timeout=120).read())

    df = pd.DataFrame(raw)

    # date_posted and date_updated are Unix timestamps (seconds since 1970).
    # Convert them to real dates so we can group by month later.
    for col in ["date_posted", "date_updated"]:
        df[col] = pd.to_datetime(df[col], unit="s", errors="coerce")

    return df


def filter_roles(df, category=CATEGORY, term=TERM, active_only=True):
    """
    Narrow the full file down to the postings we actually want.

    Three filters: the job category, the term it is for (a posting can list
    several), and whether it is still open. Keeping these as arguments means
    you can swap in "Software" or "Summer 2026" without touching the code.
    """
    keep = df["category"] == category

    # terms is a list per row, so we check for membership rather than equality.
    keep = keep & df["terms"].apply(
        lambda t: term in t if isinstance(t, list) else False
    )

    if active_only:
        keep = keep & df["active"]

    return df[keep].copy()


def add_analysis_columns(df):
    """
    Add the handful of derived columns the charts need.

    Everything here is computed from fields already in the data — no
    guessing, no outside sources.
    """
    out = df.copy()

    # degrees is a list like ["Bachelor's", "Master's"]. These flags make
    # "what share accept a bachelor's?" a one-line answer later.
    out["accepts_bachelors"] = out["degrees"].apply(
        lambda d: "Bachelor's" in d if isinstance(d, list) else False
    )
    out["requires_phd_only"] = out["degrees"].apply(
        lambda d: d == ["PhD"] if isinstance(d, list) else False
    )

    # locations is also a list. Count them, and flag remote separately,
    # since a remote posting is not tied to a city.
    out["n_locations"] = out["locations"].apply(
        lambda loc: len(loc) if isinstance(loc, list) else 0
    )
    out["is_remote"] = out["locations"].apply(
        lambda loc: any("remote" in str(x).lower() for x in loc)
        if isinstance(loc, list) else False
    )

    # Month the posting went up — this is what shows the hiring season.
    out["posted_month"] = out["date_posted"].dt.to_period("M").astype(str)

    return out


def save_snapshot(df, folder=DATA_DIR):
    """
    Write today's filtered postings to their own dated file.

    Snapshotting daily is what lets you later measure how long postings
    stay open, since the active flag flips to False when one closes.
    """
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"internships_{date.today().isoformat()}.csv"

    # Lists do not survive a round trip through CSV, so flatten them to
    # semicolon-joined strings on the way out.
    out = df.copy()
    for col in ["terms", "locations", "degrees"]:
        out[col] = out[col].apply(
            lambda v: "; ".join(map(str, v)) if isinstance(v, list) else ""
        )

    out.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def load_all_snapshots(folder=DATA_DIR):
    """
    Read every dated CSV back in and stack them into one table.

    Adds scraped_on so you can tell which day each row came from.
    """
    files = sorted(folder.glob("internships_*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No internships_*.csv files in {folder}. Run scrape.py first."
        )

    frames = []
    for path in files:
        part = pd.read_csv(path, encoding="utf-8-sig")
        part["scraped_on"] = path.stem.replace("internships_", "")
        frames.append(part)

    return pd.concat(frames, ignore_index=True)