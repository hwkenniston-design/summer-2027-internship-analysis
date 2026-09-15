"""
Run this to collect today's data:  py scrape.py

Downloads the full internships file, keeps the Summer 2027 data roles that
are still open, saves them to data/internships_YYYY-MM-DD.csv, and prints
a readable summary.
"""

import utils

# How wide each column prints. Bump these if your terminal is wide.
W_TITLE = 46
W_COMPANY = 24
W_LOCATION = 22


def line(char="-", width=104):
    """A horizontal rule, so blocks of output are easy to tell apart."""
    print(char * width)


def heading(text):
    """A labelled section break."""
    print()
    line("=")
    print(f"  {text}")
    line("=")


def fit(text, width):
    """
    Cut a string to width, adding an ellipsis if it had to be shortened.

    Without this, one 99-character job title blows up the column alignment
    for every other row.
    """
    text = str(text)
    return text if len(text) <= width else text[: width - 1] + "…"


def bar(count, biggest, width=34):
    """Draw a proportional bar. The longest value fills the full width."""
    if biggest == 0:
        return ""
    return "█" * max(1, round(width * count / biggest))


def print_table(df, limit=20):
    """Print postings as an aligned table."""
    print(
        f"  {'ROLE':<{W_TITLE}}  {'COMPANY':<{W_COMPANY}}  "
        f"{'WHERE':<{W_LOCATION}}  {'DEGREE':<10}  POSTED"
    )
    line()

    for _, row in df.head(limit).iterrows():
        places = row["locations"]
        where = places[0] if isinstance(places, list) and places else "—"
        if isinstance(places, list) and len(places) > 1:
            where = f"{where} +{len(places) - 1}"

        degrees = row["degrees"]
        if isinstance(degrees, list) and degrees:
            # "Bachelor's, Master's" is too wide for a column, so shorten
            # each one to its first letter: BM, BMP, P.
            degree = "".join(d[0] for d in degrees)
        else:
            degree = "?"

        print(
            f"  {fit(row['title'], W_TITLE):<{W_TITLE}}  "
            f"{fit(row['company_name'], W_COMPANY):<{W_COMPANY}}  "
            f"{fit(where, W_LOCATION):<{W_LOCATION}}  "
            f"{degree:<10}  {row['date_posted'].strftime('%b %d')}"
        )


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
    print(f"  saved to {path.name}")

    total = len(roles)

    # ---- headline numbers ----
    heading("THE NUMBERS")
    for label, count in [
        ("Accept a bachelor's", roles["accepts_bachelors"].sum()),
        ("PhD only", roles["requires_phd_only"].sum()),
        ("Remote", roles["is_remote"].sum()),
    ]:
        print(f"  {label:<22} {count:>4}  ({100 * count / total:>2.0f}%)")

    # ---- when they went up ----
    heading("WHEN THEY WERE POSTED")
    months = roles["posted_month"].value_counts().sort_index()
    biggest = months.max()
    for month, count in months.items():
        print(f"  {month}  {count:>4}  {bar(count, biggest)}")

    # ---- who is hiring ----
    heading("WHO IS HIRING MOST")
    companies = roles["company_name"].value_counts().head(10)
    biggest = companies.max()
    for company, count in companies.items():
        print(f"  {fit(company, 26):<26} {count:>3}  {bar(count, biggest, 22)}")

    # ---- the actual jobs ----
    newest = roles.sort_values("date_posted", ascending=False)
    heading(f"NEWEST POSTINGS  (20 of {total})")
    print_table(newest, limit=20)

    open_to_you = newest[newest["accepts_bachelors"]]
    heading(f"OPEN TO UNDERGRADS  (20 of {len(open_to_you)})")
    print_table(open_to_you, limit=20)

    print()
    print("  Degree key: B = bachelor's, M = master's, P = PhD, ? = unspecified")
    print(f"  Full list with apply links is in data/{path.name}")
    print()


if __name__ == "__main__":
    main()