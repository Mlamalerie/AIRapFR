

from bs4 import BeautifulSoup as bs
import re
import requests
from data_lyrics import get_artist_from_id

def get_genuis_id_from_url(url):
    """
    Get genius id from url
    :param url:
    :return:
    """
    if not url:
        return "None url"
    if not url.startswith("https://genius.com/"):
        return "Invalid url"
    # request and get page content
    page = requests.get(url)
    if page.status_code != 200:
        return "Error : " + str(page.status_code)
    # parse html
    soup = bs(page.content, 'html.parser')
    # get meta tag
    if meta := soup.find("meta", {"name": "newrelic-resource-path"}):
        # get id from meta tag
        if id := re.findall(r"artists\/(\d+)", meta["content"]):
            return id[0]
    else:
        return None


def main():
    for url in ["https://genius.com/artists/Mayo"]:
        id_ = get_genuis_id_from_url(url)
        print(id_,url, get_artist_from_id(id_))


main()