import json
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def main():
    template = get_template()
    render_pages(template)
    rebuild()
    server = Server()
    server.watch('template.html', main)
    server.watch('pages/*.html', rebuild)
    server.serve(root='pages/')


def rebuild():
    print("server rebuilt")


def get_template():
    env = Environment(
        loader=FileSystemLoader("."),
        autoescape=select_autoescape(["html"])
    )
    template = env.get_template("template.html")

    return template


def render_pages(template, directory="pages/", number_pages=10):
    os.makedirs(directory, exist_ok=True)
    with open('books.json', 'r') as file:
        books = json.load(file)

    books_chunked = list(chunked(chunked(json.loads(books), 2), number_pages))
    file_names = [f"index{page+1}.html" for page in range(len(books_chunked))]

    for number, books in enumerate(books_chunked, start=1):
        rendered_page = template.render(books=books, pages=file_names,
                                        page_number=number,
                                        number_pages=len(file_names))
        path = os.path.join(directory, f"index{number}.html")
        with open(path, "w") as file:
            file.write(rendered_page)


if __name__ == "__main__":
    main()
