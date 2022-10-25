import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date, timedelta

# Parse data from Last.fm
def parse_lastfm_page(user, method, start, end, page_number):
    url = f"https://www.last.fm/user/{user}/library/{method}?from={start}&to={end}&page={page_number}"
    page = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G996U Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36"})
    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.findAll('table')[0].findAll('tr', class_="chartlist-row")
    # print(url)
    return results

# Create pandas dataframes
def fetch_lastfm_charts(user, method, start, end):
    columns = ["no", "name", "artist", "scrobbles"]
    lastfm_df = pd.DataFrame(columns=columns)
    for i in range(1,11):
        print(str(i)+"/10")
        results = parse_lastfm_page(user, method, start, end, i)
        for row in results:
            no = row.find("td", class_="chartlist-index").text.strip()
            name = row.find("td", class_="chartlist-name").text.strip()
            if method != "artists":
                artist = row.find("td", class_="chartlist-artist").text.strip()
            scrobbles = row.find("span", class_="chartlist-count-bar-value").text.strip().strip(" scrobbles").replace(",","")
            if method == "artists":
                data = [{"no": no, "name": name, "artist": "", "scrobbles": scrobbles}]
                temp_lastfm_df = pd.DataFrame(data)
                lastfm_df = pd.concat([lastfm_df, temp_lastfm_df])
            else:
                data = [{"no": no, "name": name, "artist": artist, "scrobbles": scrobbles}]
                temp_lastfm_df = pd.DataFrame(data)
                lastfm_df = pd.concat([lastfm_df, temp_lastfm_df])
    return lastfm_df

# Get comparison results
def compare_lastfm_periods(user, method, cutoff, end):
    # dataframe for NOW period
    print("Scraping data for the current period")
    now = fetch_lastfm_charts(user, method, cutoff, "")
    now["scrobbles"] = now["scrobbles"].apply(pd.to_numeric)
    now['pct_rank'] = now['scrobbles'].rank(pct=True)
    # dataframe for PAST period
    print("Scraping data for the past period")
    past = fetch_lastfm_charts(user, method, end, cutoff)
    past["scrobbles"] = past["scrobbles"].apply(pd.to_numeric)
    past['pct_rank'] = past['scrobbles'].rank(pct=True)
    # compare data frames
    diff = past.merge(now[['name', 'pct_rank']], how='left', on='name', suffixes=('_past','_now')).fillna(0)
    diff["rank_diff"] = diff["pct_rank_past"] - diff["pct_rank_now"]
    diff = diff.sort_values(by="rank_diff", ascending=False)
    if method == "artists":
        diff = diff[["name", "scrobbles"]]
    else:
        diff = diff[["name", "artist", "scrobbles"]]
    print(diff.head(20))

# User input function for time periods
period_dict = {
    "1 month": 30,
    "3 months": 90,
    "6 months": 180,
    "1 year": 365,
    "2 years": 730,
    "3 years": 1095,
    "5 years": 1825
}

def get_input():
    while True:
        choices = period_dict.keys()
        print("\n(Choose from:)")
        for i in choices:
            print(i)
        user_input = input("")
        if user_input in choices:
            return period_dict.get(user_input)
        else:
            print("\nIncorrect input, try again")

# User input & running the functions
print("Choose user")
user = input("")
print("Choose method: tracks / albums / artists")
method = input("")
# ^ works for: "tracks", "albums", "artists"
print("Compare last ...")
period_1 = get_input()
print("... to the previous ...")
period_2 = get_input()

today = date.today()
cutoff = today - timedelta(days = period_1)
end = cutoff - timedelta(days = period_2)

compare_lastfm_periods(user, method, cutoff, end)