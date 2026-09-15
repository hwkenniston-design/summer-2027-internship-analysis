"""
Run this once a day:  python scrape.py

Grabs today's postings, keeps the data-related ones, and saves them to
data/jobs_YYYY-MM-DD.csv. Run it for a few weeks and you have something
nobody else has.
"""

import utils


def main():
    print("Fetching postings from RemoteOK...")

    try:
        df = utils.fetch_jobs()
    except Exception as error:
        # A 403 here means the site is blocking the scraper. Printing the
        # actual error instead of crashing makes it much easier to fix.
        print(f"Fetch failed: {type(error).__name__}: {error}")
        return

    print(f"  got {len(df)} postings total")

    data_jobs = df[utils.is_data_role(df)].copy()
    print(f"  {len(data_jobs)} of them look data-related")

    if len(data_jobs) == 0:
        print("Nothing to save today. That happens — try again tomorrow.")
        return

    # Add a skills column so the analysis notebook does not have to redo
    # this work every time it loads the file.
    data_jobs["skills"] = data_jobs.apply(utils.extract_skills, axis=1)
    data_jobs["skills"] = data_jobs["skills"].apply(lambda s: ",".join(s))

    path = utils.save_snapshot(data_jobs)
    print(f"Saved to {path}")

    # A quick look at what came in, so you notice immediately if the
    # filter is pulling in junk.
    print("\nToday's roles:")
    for title in data_jobs["position"].head(10):
        print(f"  - {title}")


if __name__ == "__main__":
    main()
