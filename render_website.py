import json

from http.server import HTTPServer, SimpleHTTPRequestHandler

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server

env = Environment(
    loader=FileSystemLoader('.'),
    autoescape=select_autoescape(['html', 'xml'])
)

template = env.get_template('template.html')



def reload_index():
    with open('books_descriptions.json', 'r', encoding='utf-8') as books_file:
        books_json = books_file.read()
    books = json.loads(books_json)

    rendered_page = template.render(
        books = books
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


# def main():
reload_index()
server = Server()
server.watch('template.html', reload_index)
server.serve(root='.')


# if __name__ == '__main__':
    # main()