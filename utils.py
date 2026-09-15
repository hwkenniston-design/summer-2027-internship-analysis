"""
Job Postings — helper functions.

Everything the scraper and the notebooks need lives here, so the notebooks
stay short and readable.
"""

import json
import re
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

# Where the daily CSVs get saved. Path() handles Windows backslashes for us.
DATA_DIR = Path(__file__).parent / "data"

# Words that mark a posting as data-ish. Edit this list — it is the single
# biggest lever you have on what the whole project ends up measuring.
ROLE_KEYWORDS = [
    "data", "analyst", "analytics", "scientist", "machine learning",
    "ml engineer", "business intelligence", "statistician",
]

# Tools/skills to look for in the text of each posting. Left side is what
# we search for, right side is the clean name we count under. Several
# spellings can map to one name (google cloud and gcp are the same thing).
SKILL_PATTERNS = {
    "python": "Python",
    "r": "R",
    "sql": "SQL",
    "excel": "Excel",
    "tableau": "Tableau",
    "power bi": "Power BI",
    "looker": "Looker",
    "pandas": "pandas",
    "spark": "Spark",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "snowflake": "Snowflake",
    "databricks": "Databricks",
    "airflow": "Airflow",
    "dbt": "dbt",
    "docker": "Docker",
    "git": "Git",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "statistics": "Statistics",
}


def fetch_jobs():
    """
    Pull the current postings from the RemoteOK API and return a DataFrame.

    This makes a real network call, so it returns whatever is live right now.
    """
    req = urllib.request.Request(
        "https://remoteok.com/api",
        headers={"User-Agent": "Mozilla/5.0"},
    )
    raw = json.loads(urllib.request.urlopen(req, timeout=60).read())

    # The first item in the response is a legal notice, not a job, and some
    # entries have no title. Keep only real postings.
    jobs = [j for j in raw if isinstance(j, dict) and j.get("position")]

    return pd.DataFrame([
        {
            "position": j.get("position"),
            "company": j.get("company"),
            "location": j.get("location") or "Remote",
            "tags": ",".join(j.get("tags", [])),
            "description": strip_html(j.get("description", "")),
            "url": j.get("url"),
            "date_posted": j.get("date"),
        }
        for j in jobs
    ])


def strip_html(text):
    """
    Remove HTML tags from the description field.

    The API returns descriptions as web page markup, so the raw text is full
    of <p> and <br> junk. This walks the string once and drops anything
    sitting between a < and a >.
    """
    if not text:
        return ""
    out = []
    inside_tag = False
    for char in text:
        if char == "<":
            inside_tag = True
        elif char == ">":
            inside_tag = False
        elif not inside_tag:
            out.append(char)
    return " ".join("".join(out).split())


def is_data_role(df):
    """
    Return a True/False mask for which rows look like data jobs.

    Title only. We deliberately ignore the tags: this site auto-generates
    them and they are junk — in the sample data a Greenskeeper posting is
    tagged "analyst, exec, recruiter".
    """
    haystack = df["position"].fillna("").str.lower()

    mask = pd.Series(False, index=df.index)
    for word in ROLE_KEYWORDS:
        mask = mask | haystack.str.contains(word, regex=False)
    return mask


def extract_skills(row):
    """
    Return the list of skills mentioned anywhere in one posting.

    Title and description only — tags are excluded on purpose. 31 of the
    100 postings in the sample data carry an "excel" tag no matter what the
    job actually is, which would make Excel look like the top skill in
    tech. The description is where the real requirements live.
    """
    text = " ".join([
        str(row.get("position", "")),
        str(row.get("description", "")),
    ]).lower()

    found = []
    for pattern, clean_name in SKILL_PATTERNS.items():
        # \b means "word boundary". Without it, "git" matches the middle of
        # "digital" and "excel" matches "excellent" — which is exactly the
        # bug this project hit on the first run.
        if re.search(rf"\b{re.escape(pattern)}\b", text):
            if clean_name not in found:
                found.append(clean_name)
    return found


def save_snapshot(df, folder=DATA_DIR):
    """
    Write today's postings to their own dated file.

    One file per day is the whole point of the project. Overwriting a single
    jobs.csv would throw away the history that makes the analysis interesting.
    """
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"jobs_{date.today().isoformat()}.csv"
    # utf-8-sig keeps Excel from mangling accented characters if you open it.
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def load_all_snapshots(folder=DATA_DIR):
    """
    Read every dated CSV in the data folder and stack them into one table.

    Adds a scraped_on column so you can tell which day each row came from,
    and drops repeats, since the same posting shows up on several days.
    """
    files = sorted(folder.glob("jobs_*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No jobs_*.csv files in {folder}. Run scrape.py first."
        )

    frames = []
    for path in files:
        # utf-8-sig is what fixes the "St Johnâs" garbling.
        part = pd.read_csv(path, encoding="utf-8-sig")
        part["scraped_on"] = path.stem.replace("jobs_", "")
        frames.append(part)

    everything = pd.concat(frames, ignore_index=True)

    # The same job posted on three days is three rows. Record when we first
    # and last saw each one, so later you can measure how long postings
    # stay up, then keep one row per posting.
    everything["first_seen"] = everything.groupby(
        ["position", "company"]
    )["scraped_on"].transform("min")
    everything["last_seen"] = everything.groupby(
        ["position", "company"]
    )["scraped_on"].transform("max")

    return everything.drop_duplicates(subset=["position", "company"])
