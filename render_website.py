import argparse
import json
import math
import os
import shutil

from http.server import HTTPServer, SimpleHTTPRequestHandler

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def get_media_root(register):
    folder, _ = os.path.split(register)
    return folder


def reload_index():
    parser = argparse.ArgumentParser(
        description="Запуск онлайн-библиотеки"
        )
    parser.add_argument(
        "--reg",
        help="Путь и имя json-файла с описанием книг, по умолчанию media/books_descriptions.json",
        default="media/books_descriptions.json"
        )
    args = parser.parse_args()
    register = args.reg

    env = Environment(
        loader=FileSystemLoader("."),
        autoescape=select_autoescape(["html", "xml"])
    )

    template = env.get_template("template.html")

    with open(register, "r", encoding="utf-8") as books_file:
        books = json.load(books_file)
    shutil.rmtree("pages")
    os.makedirs("pages", exist_ok=True)
    books_per_page = 20
    pages_count = math.ceil(len(books) / books_per_page)
    books_on_page = chunked(books, books_per_page)
    columns_count = 2
    for page, page_books in enumerate(books_on_page, 1):
        books_rows = chunked(page_books, columns_count)
        rendered_page = template.render(
            books=books_rows,
            current_page=page,
            pages_count=pages_count,
            folder=get_media_root(register)
        )

        with open(f"pages/index{page}.html", "w", encoding="utf8") as file:
            file.write(rendered_page)


def main():
    reload_index()
    server = Server()
    server.watch("template.html", reload_index)
    server.serve(root=".")


if __name__ == "__main__":
    main()
