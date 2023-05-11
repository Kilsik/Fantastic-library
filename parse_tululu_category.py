import requests
import os
import json
import argparse
import logging
import time

from bs4 import BeautifulSoup
from pathlib import Path
from contextlib import suppress
from urllib.parse import urljoin, urlsplit
from pathvalidate import sanitize_filepath, sanitize_filename


def create_parser():
    """
    Создаем парсер с аргументами
    """

    parser = argparse.ArgumentParser(
    description="Скачивает информацию о книгах и их текст"
    )
    parser.add_argument(
        "--start_page",
        type=int,
        default=1,
        help="Начало диапазона страниц скачиваемых книг"
    )
    parser.add_argument(
        "--end_page",
        type=int,
        default=1000000,
        help="Конец диапазона страниц скачиваемых книг (книги страницы с этим номером скачаны не будут)"
    )
    parser.add_argument(
        "--dest_folder",
        help="Путь к каталогу с результатами парсинга: картинкам, книгам, JSON"
    )
    parser.add_argument(
        "--skip_imgs",
        action='store_true',
        default=False,
        help="При наличии этого параметра не будут скачиваться обложки книг"
    )
    parser.add_argument(
        "--skip_txt",
        action='store_true',
        default=False,
        help="При указании этого параметра не будут скачиваться тексты книг"
    )
    parser.add_argument(
        "--json_path",
        default='books_descriptions.json',
        help="Файл с описанием книг. По умолчанию 'books_descriptions.json'"
    )
    return parser


def get_book_page(url):
    """
    Получаем страницу книги
    """
    
    page_response = requests.get(url)
    page_response.raise_for_status()
    return page_response


def parse_book_page(soup):
    """
    Собираем информацию о книге
    """

    about_book_selector = '.ow_px_td h1'
    about_book = soup.select_one(about_book_selector).text
    raw_title, raw_author = about_book.split(sep="::")

    title = raw_title.strip()
    author = raw_author.strip()
    
    img_selector = ".bookimage img"
    img_url = soup.select_one(img_selector)["src"]

    comments_selector = ".texts .black"
    raw_comments = soup.select(comments_selector)
    comments = [comment.text for comment in raw_comments]
    
    genres_selector = "span.d_book a"
    raw_genres = soup.select(genres_selector)
    genres = [genre.text for genre in raw_genres]

    return {
        "title": title,
        "author": author,
        "img_scr": img_url,
        "comments": comments,
        "genres": genres
    }


def download_txt(url, filename, folder):
    """Скачиваем текстовые файлы.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    response = requests.get(url)
    response.raise_for_status()
    Path(folder).mkdir(parents=True, exist_ok=True)
    valid_filename = sanitize_filename(filename)
    full_path = os.path.join(folder, valid_filename)
    with open(full_path, "w", encoding="utf-8") as file:
        file.write(response.text)
    return full_path


def download_image(url, folder):
    """
    Скачиваем изображения обложек книг
    """

    Path(folder).mkdir(parents=True, exist_ok=True)
    img_filename = url.split("/")[-1]
    valid_filename = sanitize_filename(f"{img_filename}")
    full_path = os.path.join(folder, valid_filename)
    if not Path(full_path).exists():
        response = requests.get(url)
        response.raise_for_status()
        with open(full_path, "wb") as file:
            file.write(response.content)
    return full_path


def check_for_redirect(response):
    """
    Проверяем наличие книги
    """

    if response.history:
        raise requests.HTTPError()


def main():
    parser = create_parser()
    args = parser.parse_args()
    start_page = args.start_page
    end_page = args.end_page
    folder = sanitize_filepath(args.dest_folder) if args.dest_folder else ''
    skip_imgs = args.skip_imgs
    skip_txt = args.skip_txt
    json_path = os.path.join(folder, sanitize_filename(args.json_path))

    if start_page > end_page:
        print("Номер начальной страницы не может больше номера последней")
        exit()

    if start_page == end_page:
        end_page += 1

    fantastic_url = 'https://tululu.org/l55/'
    books_description = []
    start = start_page
    finish = end_page

    while start < finish:
        try:
            for page in range(start, finish):
                if page >= (finish - 1):
                    start = finish
                page_url = urljoin(fantastic_url, str(page))
                response = requests.get(page_url)
                response.raise_for_status()

                try:
                    check_for_redirect(response)
                except requests.HTTPError:
                    print(f"Страницы с номером {page} не существует")
                    exit()

                soup = BeautifulSoup(response.text, 'lxml')
                num_pages_selector = ".ow_px_td .center .npage"
                num_pages = soup.select(num_pages_selector)[-1]
                last_page = int(num_pages.text)

                if last_page < end_page:
                    finish = last_page +1

                all_books_selector = ".d_book"
                about_books = soup.select(all_books_selector)
                for book in about_books:
                    url_selector = 'a[href]'
                    raw_book_url = book.select_one(url_selector)
                    book_url = urljoin(fantastic_url, raw_book_url['href'])
                    book_response = get_book_page(book_url)
                    book_soup = BeautifulSoup(book_response.text, 'lxml')
                    about_book = parse_book_page(book_soup)
                    title = about_book['title']
                    book_selector = ".d_book a[title$='скачать книгу txt']"
                    try:
                        rel_txt_url = book_soup.select_one(book_selector)['href']
                    except TypeError:
                        print(f'В библиотеке нет текста книги {title}')
                        continue
                    txt_url = urljoin(book_url, rel_txt_url)
                    _, book_num = urlsplit(txt_url)[3].split('=')
                    txt_filename = f'{book_num}. {title}.txt'
                    img_url = urljoin(book_url, about_book['img_scr'])
                    if not skip_txt:
                        book_folder = os.path.join(folder, 'books/')
                        book_namepath = download_txt(txt_url, txt_filename, book_folder)
                    if not skip_imgs:
                        img_folder = os.path.join(folder, 'images/')
                        cover_path = download_image(img_url, img_folder)
                    books_description.append(about_book)
                    print(book_url)
        except requests.ConnectionError as err:
            logging.exception("Проверьте соединение с сетью", exc_info=False)
            print(err)
            start = page
            time.sleep(180)
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)
    with open(json_path, 'a', encoding='utf-8') as json_file:
        json_file.seek(0, 2)
        json.dump(books_description, json_file, ensure_ascii=False)


if __name__ == '__main__':
    main()