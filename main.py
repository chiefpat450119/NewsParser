import requests
import json
import datetime as dt
import random

today = dt.datetime.now(tz=dt.timezone(dt.timedelta(hours=8)))

keywords = ["COVID", "case", "vaccine", "lockdown", "coronavirus", "omicron", " BA.2", "covid", "pandemic"]


# Custom error when you run out of api requests for that day
class OutOfRequestsError(Exception):
    pass


class API:
    # Randomly selects an API
    selected = None
    instances = []

    @classmethod
    def api_selector(cls):
        cls.selected = random.choice(cls.instances)

    # Constructor for API instances since different APIs will be used which have different keys.
    def __init__(self, name, key, endpoint, rq_limit, parse_method):
        self.name = name
        self.key = key
        self.endpoint = endpoint
        self.rq_limit = rq_limit
        self.parse_method = parse_method
        self.response = None
        self.rqs_today = 0
        # Adds the instance to the list
        API.instances.append(self.name)

    def get_news(self):
        if self.name == self.__class__.selected:
            if self.rqs_today < self.rq_limit:
                self.response = requests.get(self.endpoint).json()
                self.rqs_today += 1
            else:
                raise OutOfRequestsError(f"The request limit for {self.name} is {self.rq_limit} per day.")
        else:
            print(f"{self.name} was not selected.")

    # Parses the json from the get request using the parse method passed to the constructor for each instance (each API)
    # The parse method returns a list of python dictionaries, with each being a news article.
    # The relevant articles are then compiled into the output json file.
    def parse_news(self):
        if self.name == self.__class__.selected:
            parsed_articles = (self.parse_method(self.response))
            with open("news_file.json", "a") as out_file:
                out_dict = {"news articles": parsed_articles}
                json.dump(out_dict, out_file, indent=4)

    # Resets the total requests after every 24h (I guess call the method externally?)
    def daily_reset(self):
        self.rqs_today = 0


# Erase the json file so new articles can be added
open('news_file.json', 'w').close()


# Checks for duplicates from the title file and removes them
def dupe_remover(articles):
    with open("titles.txt", "r") as title_file:
        titles = [line.strip() for line in title_file.readlines()]
        return [article for article in articles if article["title"] not in titles]


country_keywords = {
    "United States": ["F.D.A.", "U.S.", "United States", "USA", "America", "American", "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut""Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon",
"Pennsylvania",
"Rhode Island",
"South Carolina",
"South Dakota",
"Tennessee",
"Texas",
"Utah",
"Vermont",
"Virginia",
"Washington",
"West Virginia",
"Wisconsin",
"Wyoming"
],
    "Canada": ["Canadian", "Ottawa", "Canada", "Canadian", "British Columbia", "Alberta", "Saskatchewan", "Manitoba", "Ontario", "Quebec", "Newfoundland", "Prince Edward Island", "Nova Scotia", "New Brunswick"],
    "United Kingdom": ["UK", "England", "Scotland", "Wales", "London", "Britain", "British"],
    "Singapore": ["Singapore", "SG", "S'pore", "Singaporean", "S'porean"],
    "China": ["China", "Beijing", "Shanghai", "Chinese"],
    "Taiwan": ["Taiwan", "Taipei", "Taiwanese"],
    "Hong Kong": ["Hong Kong"],
    "Malaysia": ["Kuala Lumpur", "Malaysia", "Malaysian"],
    "Thailand": ["Bangkok", "Thailand", "Thai"],
    "Indonesia": ["Indonesia", "Indonesian"],
    "Japan": ["Japan", "Japanese"],
    "South Korea": ["Korean", "Korea"],
    "Russia": ["Russia", "Russian"],
    "India": ["India", "Indian"],
    "EU": ["Europe", "European Union", "France", "Germany", "Spain", "Belgium", "Poland", "Austria", "Portugal"]
}


def find_country(title):
    for country, kws in country_keywords.items():
        for kw in kws:
            if kw.lower() in title.lower():
                return country
    return "World"


def news_api_parser(response):
    out_list = []
    cleaned_articles = dupe_remover(list(response["articles"]))
    for article in cleaned_articles:
        # parse the info into a dictionary
        news = {}
        title = article["title"]
        news["Content"] = title
        news["Country"] = find_country(title)
        date = dt.datetime.strptime(article["publishedAt"][:10], "%Y-%m-%d")
        news["Date"] = f"{int(date.strftime('%d'))}/{int(date.strftime('%m'))}/{int(date.strftime('%y'))}"
        news["Type"] = article["source"]["name"]
        news["Source"] = article["url"]
        with open("titles.txt", "a") as title_file:
            title_file.write(title)
            title_file.write("\n")
        out_list.append(news)
    return out_list


def gnews_parser(response):
    out_list = []
    cleaned_articles = dupe_remover(list(response["articles"]))
    for article in cleaned_articles:
        date = dt.datetime.strptime(article["publishedAt"][:10], "%Y-%m-%d")
        article_country = find_country(article["title"])
        news = {
            "Content": article["title"],
            "Country": article_country,
            "Date": f"{int(date.strftime('%d'))}/{int(date.strftime('%m'))}/{int(date.strftime('%y'))}",
            "Type": article["source"]["name"],
            "Source": article["source"]["url"]
        }
        with open("titles.txt", "a") as title_file:
            title_file.write(article["title"])
            title_file.write("\n")
        out_list.append(news)
    return out_list


NewsAPI = API("NewsAPI", "ub_587960b140aef344fb505b1adea65eb74d6f", "https://newsapi.org/v2/everything?language=en&apiKey=e96bed54fcd54264baacacbe558034d3&q=covid OR pandemic OR coronavirus", 100, news_api_parser)
GNews = API("GNews", "daf68a9f1aacf806578c97b6f3a29a2e", "https://gnews.io/api/v4/search?token=daf68a9f1aacf806578c97b6f3a29a2e&lang=en&q=covid OR pandemic OR coronavirus OR omicron", 100, gnews_parser)
# Randomly selects an API to request
API.api_selector()


NewsAPI.get_news()
NewsAPI.parse_news()

GNews.get_news()
GNews.parse_news()
