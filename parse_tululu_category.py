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

from tululu import (
    check_for_redirect,
    parse_book_page,
    download_txt,
    download_image
    )


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
    books_descriptions = []
    start = start_page
    finish = end_page

    trying = True
    while trying:
        try:
            last_page_response = requests.get(fantastic_url)
            last_page_response.raise_for_status()
            trying = False
        except requests.ConnectionError as err:
            logging.exception("Проверьте соединение с сетью", exc_info=False)
            print(err)
            time.sleep(180)
    soup = BeautifulSoup(last_page_response.text, 'lxml')    
    num_pages_selector = ".ow_px_td .center .npage"
    num_pages = soup.select(num_pages_selector)[-1]
    last_page = int(num_pages.text)

    if start_page > last_page:
        print("Номер стартовой страницы больше общего числа страниц.")
        exit()

    if last_page < end_page:
        finish = last_page +1

    while start < finish:
        try:
            for page in range(start, finish):
                if page >= (finish - 1):
                    start = finish
                page_url = urljoin(fantastic_url, str(page))

                try:
                    response = requests.get(page_url)
                    response.raise_for_status()
                    check_for_redirect(response)
                    soup = BeautifulSoup(response.text, 'lxml')
                    all_books_selector = ".d_book"
                    about_books = soup.select(all_books_selector)
                    for book in about_books:
                        trying = True
                        while trying:
                            try:
                                url_selector = 'a[href]'
                                raw_book_url = book.select_one(url_selector)
                                book_url = urljoin(fantastic_url, raw_book_url['href'])
                                book_response = requests.get(book_url)
                                book_response.raise_for_status()
                                check_for_redirect(book_response)
                            
                                book_soup = BeautifulSoup(book_response.text, 'lxml')
                                about_book = parse_book_page(book_soup)
                                title = about_book['title']
                                book_selector = ".d_book a[title$='скачать книгу txt']"

                                if not book_soup.select_one(book_selector):
                                    print(f'В библиотеке нет текста книги "{title}"')
                                    trying = False
                                    continue
                                rel_txt_url = book_soup.select_one(book_selector)['href']

                                txt_url = urljoin(book_url, rel_txt_url)
                                _, book_num = urlsplit(txt_url)[3].split('=')
                                txt_filename = f'{book_num}. {title}.txt'
                                img_url = urljoin(book_url, about_book['img_scr'])
                                if not skip_txt:
                                    book_folder = os.path.join(folder, 'books/')
                                    about_book["txt_path"] = download_txt(txt_url, txt_filename, book_folder)
                                    print(about_book["txt_path"])
                                if not skip_imgs:
                                    img_folder = os.path.join(folder, 'images/')
                                    about_book["img_scr"] = download_image(img_url, img_folder)
                                    print(about_book["img_scr"])
                                trying = False
                                books_descriptions.append(about_book)
                            except requests.ConnectionError as err:
                                logging.exception("Проверьте соединение с сетью", exc_info=False)
                                print(err)
                                time.sleep(180)
                except requests.HTTPError as err:
                    print("Запрашиваемый объект отсутствует\n", err)
                    continue
        except requests.ConnectionError as err:
            logging.exception("Проверьте соединение с сетью", exc_info=False)
            print(err)
            start = page
            time.sleep(180)
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)
    with open(json_path, 'a', encoding='utf-8') as json_file:
        json.dump(books_descriptions, json_file, ensure_ascii=False)


if __name__ == '__main__':
    main()