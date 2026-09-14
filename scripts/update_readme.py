"""
Fetches competitive programming ratings for a fixed set of handles and
rewrites the table between the <!--RATINGS_START--> / <!--RATINGS_END-->
markers in README.md. Intended to be run by a GitHub Action on a schedule.
"""

import re
import requests

CF_HANDLE = "AnupBarman"
AC_HANDLE = "AnupBarman"
LC_HANDLE = "beedoescode"
CC_HANDLE = "anup_barman"

README_PATH = "README.md"

HEADERS = {"User-Agent": "Mozilla/5.0 (README-rating-bot)"}


def get_codeforces_rating(handle):
    try:
        r = requests.get(
            f"https://codeforces.com/api/user.info?handles={handle}",
            timeout=10,
        )
        data = r.json()
        if data.get("status") == "OK":
            user = data["result"][0]
            rating = user.get("rating", "Unrated")
            max_rating = user.get("maxRating", "N/A")
            rank = user.get("rank", "unrated").title()
            return f"{rating} ({rank}, max: {max_rating})"
    except Exception as e:
        print(f"Codeforces fetch failed: {e}")
    return "N/A"


def get_atcoder_rating(handle):
    try:
        r = requests.get(
            f"https://atcoder.jp/users/{handle}/history/json",
            timeout=10,
            headers=HEADERS,
        )
        history = r.json()
        if history:
            rating = history[-1]["NewRating"]
            max_rating = max(h["NewRating"] for h in history)
            return f"{rating} (max: {max_rating})"
    except Exception as e:
        print(f"AtCoder fetch failed: {e}")
    return "N/A"


def get_leetcode_rating(handle):
    try:
        query = {
            "query": """
            query getUserContestRanking($username: String!) {
              userContestRanking(username: $username) {
                rating
                globalRanking
              }
            }
            """,
            "variables": {"username": handle},
        }
        r = requests.post(
            "https://leetcode.com/graphql",
            json=query,
            timeout=10,
            headers={**HEADERS, "Content-Type": "application/json"},
        )
        data = r.json()
        ranking = data.get("data", {}).get("userContestRanking")
        if ranking and ranking.get("rating") is not None:
            rating = round(ranking["rating"])
            rank = ranking.get("globalRanking", "N/A")
            return f"{rating} (Global Rank: {rank})"
    except Exception as e:
        print(f"LeetCode fetch failed: {e}")
    return "N/A"


def get_codechef_rating(handle):
    try:
        r = requests.get(
            f"https://www.codechef.com/users/{handle}",
            timeout=10,
            headers=HEADERS,
        )
        match = re.search(r'rating-number">\s*([\d]+)', r.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"CodeChef fetch failed: {e}")
    return "N/A"


def update_readme():
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    cf = get_codeforces_rating(CF_HANDLE)
    ac = get_atcoder_rating(AC_HANDLE)
    lc = get_leetcode_rating(LC_HANDLE)
    cc = get_codechef_rating(CC_HANDLE)

    print(f"Codeforces: {cf}")
    print(f"AtCoder:    {ac}")
    print(f"LeetCode:   {lc}")
    print(f"CodeChef:   {cc}")

    new_block = (
        "<!--RATINGS_START-->\n"
        "| Platform | Rating |\n"
        "|---|---|\n"
        f"| Codeforces | {cf} |\n"
        f"| AtCoder | {ac} |\n"
        f"| LeetCode | {lc} |\n"
        f"| CodeChef | {cc} |\n"
        "<!--RATINGS_END-->"
    )

    updated = re.sub(
        r"<!--RATINGS_START-->.*?<!--RATINGS_END-->",
        new_block,
        content,
        flags=re.DOTALL,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)


if __name__ == "__main__":
    update_readme()
