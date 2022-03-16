from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def get_book_url(start_page, end_page):
    books_url = []
    for page in range(start_page, end_page):
        respone = requests.get(f"https://tululu.org/l55/{page}/")
        respone.raise_for_status()
        soup = BeautifulSoup(respone.text, "lxml")
        selector = "table div#content table"
        books_id = soup.select(selector)
        for book_id in books_id:
            book_url = urljoin("https://tululu.org", book_id.find('a')
                               .attrs["href"])
            books_url.append(book_url)

    return books_url
