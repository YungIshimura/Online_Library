import argparse
import json
import os
import urllib
import urllib.parse

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

from parse_tululu_category import get_book_url


def parse_number_of_page():
    response = requests.get("https://tululu.org/l55/1/")
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    selector = "table div#content p.center a.npage:last-child"
    end_page = soup.select_one(selector).get_text()

    return end_page


def create_parser(end_page):
    parser = argparse.ArgumentParser(description="""
        Парсер книг с сайта сайта https://tululu.org.
        Парсер берёт ссылки на книги с txt файла.
        txt файл формируется в скрипте parse_tululu_category.py.
        Перед стартом парса нужно зайти в него и указать диапазон
        скачивания книг.
    """)
    parser.add_argument("--start_page", default=1,
                        help="""Аргумент, позволяющий указать номер первой страницы,
                        в диапазоне которых будут скачаны книги (дефолт 1)""",
                        type=int)

    parser.add_argument("--end_page", default=end_page,
                        help="""Аргумент, позволяющий указать номер последней страницы,
                        в диапазоне которых будут скачаны книги
                        (дефолт 701)""",
                        type=int)

    parser.add_argument("--skip_imgs", default=False,
                        help="""
                        Аргумент, позволяющий не скачивать обложку книги.
                        Чтобы пропустить скачивание картинок достаточно
                        просто ввести в терминале --skip_imgs
                        (дефолт False)""",
                        action="store_true")

    parser.add_argument("--skip_txt", default=False,
                        help="""Аргумент, позволяющий не скачивать книги.
                        Чтобы пропустить скачивание картинок достаточно
                        просто ввести в терминале --skip_txt
                        (Дефолт False)""",
                        action="store_true")

    parser.add_argument("--json_path", default="books.json",
                        help="""Аргумент, позволяющий выбрать
                        путь для сохранения JSON файла
                        (необходимо передать путь до файла).""")

    parser.add_argument("--books_folder", default="books/",
                        help="""Аргумент, позволяющий выбрать
                        путь для сохранения текста книг
                        (необходимо передать путь до папки).""")

    parser.add_argument("--images_folder", default="images/",
                        help="""Аргумент, позволяющий выбрать
                        путь для сохранения обложек книг
                        (необходимо передать путь до папки).""")

    return parser


def main():
    end_page = parse_number_of_page()
    parser = create_parser(end_page)
    args = parser.parse_args()
    books_urls = get_book_url(args.start_page, args.end_page)
    book = []
    for book_url in books_urls:
        book_id = ''.join(
            [book_id for book_id in book_url if book_id.isdigit()]
            )
        response = requests.get(book_url)
        soup = BeautifulSoup(response.text, "lxml")
        try:
            check_for_redirect(response)
            book_author, book_name, comment, genres, image_link = parse_book(soup)
            response.raise_for_status()
            if not args.skip_txt:
                txt_path = download_txt(book_name, book_id, args.books_folder)
            if not args.skip_imgs:
                image_path = download_image(book_id,
                                            book_name, image_link,
                                            args.images_folder)
            book.append(
                {"name": book_name,
                    "author": book_author,
                    "image": f"../{image_path}",
                    "txt": f"../{txt_path}",
                    "comment": comment,
                    "genre": genres}
            )
        except requests.HTTPError:
            print(f"Книга по ссылке {book_url} не найдена")
    with open(args.json_path, "a") as file:
        json.dump(json.dumps(book, ensure_ascii=False), file, ensure_ascii=False, indent="")


def parse_book(soup):
    book_author_selector = "table div#content h1 a"
    book_author = soup.select_one(book_author_selector).get_text()

    book_name_selector = "table div#content h1"
    book_tags = soup.select_one(book_name_selector).get_text().split()
    book_name = []
    for book_tag in book_tags:
        if book_tag != "::":
            book_name.append(book_tag)
        else:
            book_name = " ".join(book_name)
            break

    comments_selector = "table div#content span.black"
    comment_tags = soup.select(comments_selector)
    comments = [comment_tag.get_text() for comment_tag in comment_tags]

    genre_selector = "table span.d_book a"
    genre_tags = soup.select(genre_selector)
    genres = [genre.get_text() for genre in genre_tags]

    image_selector = "table div#content img"
    image_link = soup.select_one(image_selector).attrs.get("src")

    return book_author, book_name, comments, genres, image_link


def download_txt(filename, book_id, directory):
    upload_url = "https://tululu.org/txt.php"
    params = {"id": book_id}
    response = requests.get(upload_url, params=params)
    response.raise_for_status()
    os.makedirs(directory, exist_ok=True)
    check_for_redirect(response)
    filename = sanitize_filename(filename)
    path = os.path.join(directory, f"{filename}.txt")
    with open(path, "w") as file:
        file.write(response.text)

    return path


def download_image(book_id, filename, image_tags, directory):
    os.makedirs(directory, exist_ok=True)
    image_url = urllib.parse.urljoin("https://tululu.org", image_tags)
    response = requests.get(image_url)
    response.raise_for_status()
    path = os.path.join(
        directory, f"{book_id}. Обложка к книге {filename}"
    )
    with open(path, "wb") as file:
        file.write(response.content)

    return path


def check_for_redirect(response):
    if response.history:
        raise requests.HTTPError


if __name__ == "__main__":
    main()
