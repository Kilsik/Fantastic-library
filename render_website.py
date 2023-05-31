import json
import os
import math
import shutil
import argparse

from http.server import HTTPServer, SimpleHTTPRequestHandler
from more_itertools import chunked
from livereload import Server
from jinja2 import Environment, FileSystemLoader, select_autoescape


def reload_index():
    env = Environment(
    loader=FileSystemLoader("."),
    autoescape=select_autoescape(["html", "xml"])
    )

    template = env.get_template("template.html")

    *folder, file_name = os.path.split(register)
    with open(register, "r", encoding="utf-8") as books_file:
        books = json.load(books_file)
    shutil.rmtree("pages")
    os.makedirs("pages", exist_ok=True)
    books_per_page = 20
    count_pages = math.ceil(len(books) / books_per_page)
    books_on_page = chunked(books, books_per_page)
    count_columns = 2    
    for page, page_books in enumerate(books_on_page, 1):
        rows_books = chunked(page_books, count_columns)
        rendered_page = template.render(
            books = rows_books,
            current_page = page,
            count_pages = count_pages,
            folder = folder[0]
        )

        with open(f"pages/index{page}.html", "w", encoding="utf8") as file:
            file.write(rendered_page)


def main():
    parser = argparse.ArgumentParser(
        description="Запуск онлайн-библиотеки"
        )
    parser.add_argument(
        "--reg",
        help="Путь и имя json-файла с описание книг, по умолчанию media/books_descriptions.json",
        default="media/books_descriptions.json"
        )
    args = parser.parse_args()
    global register
    register = args.reg
    reload_index()
    server = Server()
    server.watch('template.html', reload_index)
    server.serve(root='.')


if __name__ == "__main__":
    main()
