import json
import os
import math
import shutil


from http.server import HTTPServer, SimpleHTTPRequestHandler
from livereload import Server

from jinja2 import Environment, FileSystemLoader, select_autoescape
from more_itertools import chunked

env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)

template = env.get_template('template.html')



def reload_index():
    with open('media/books_descriptions.json', 'r', encoding='utf-8') as books_file:
        books_json = books_file.read()
    shutil.rmtree("pages")
    os.makedirs('pages', exist_ok=True)
    books = json.loads(books_json)
    books_per_page = 20
    count_pages = math.ceil(len(books) / books_per_page)
    books_on_page = chunked(books, books_per_page)
    
    for page, page_books in enumerate(books_on_page, 1):
        rows_books = chunked(page_books, 2)
        rendered_page = template.render(
            books = rows_books,
            current_page = page,
            count_pages = count_pages
        )

        with open(f'pages/index{page}.html', 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == '__main__':
    reload_index()
    server = Server()
    server.watch('template.html', reload_index)
    server.serve(root='.')