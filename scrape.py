"""
Run this to collect today's data:  py scrape.py

Downloads the full internships file, keeps the Summer 2027 data roles that
are still open, saves them to data/internships_YYYY-MM-DD.csv, and prints
a quick summary so you can see it worked.
"""

import utils


def main():
    print("Downloading listings (about 12 MB, give it a few seconds)...")

    try:
        everything = utils.fetch_listings()
    except Exception as error:
        print(f"Download failed: {type(error).__name__}: {error}")
        return

    print(f"  {len(everything):,} total postings in the file")

    roles = utils.filter_roles(everything)
    print(f"  {len(roles):,} are open {utils.TERM} {utils.CATEGORY} roles")

    if len(roles) == 0:
        print("Nothing matched. Check CATEGORY and TERM in utils.py.")
        return

    roles = utils.add_analysis_columns(roles)
    path = utils.save_snapshot(roles)
    print(f"Saved to {path}")

    # Print the headline numbers straight away. If these look wrong you
    # want to know now, not after you have built three charts on them.
    total = len(roles)
    bach = roles["accepts_bachelors"].sum()
    phd = roles["requires_phd_only"].sum()
    remote = roles["is_remote"].sum()

    print("\n--- quick summary ---")
    print(f"accept a bachelor's:  {bach:4} ({100 * bach / total:.0f}%)")
    print(f"PhD only:             {phd:4} ({100 * phd / total:.0f}%)")
    print(f"remote:               {remote:4} ({100 * remote / total:.0f}%)")

    print("\npostings by month:")
    for month, count in roles["posted_month"].value_counts().sort_index().items():
        print(f"  {month}  {count:4}  {'#' * (count // 10)}")

    print("\ntop companies:")
    for company, count in roles["company_name"].value_counts().head(8).items():
        print(f"  {count:3}  {company}")


if __name__ == "__main__":
    main()