import requests
import os
import argparse
import logging
import time

from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filepath, sanitize_filename
from urllib.parse import urljoin


def get_book_page(url):
    """
    Получаем страницу книги
    """
    
    page_response = requests.get(url)
    page_response.raise_for_status()
    check_for_redirect(page_response)
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


def check_for_redirect(response):
    """
    Проверяем наличие книги
    """

    if response.history:
        raise requests.HTTPError()
    

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
    check_for_redirect(response)
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
        check_for_redirect(response)
        with open(full_path, "wb") as file:
            file.write(response.content)
    return full_path


def save_comments(filename, comments, folder="comments/"):
    """
    Сохраняем комментарии в файл
    """

    valid_folder = sanitize_filepath(folder)
    Path(valid_folder).mkdir(exist_ok=True)
    valid_filename = sanitize_filename(f"{filename}_comments.txt")
    full_path = os.path.join(valid_folder, valid_filename)
    with open(full_path, "w") as file:
        file.writelines(comments)
    return full_path


def save_genres(filename, genres, folder="genres/"):
    """
    Сохраняем список жанров книги в файл
    """

    valid_folder = sanitize_filepath(folder)
    Path(valid_folder).mkdir(exist_ok=True)
    valid_filename = sanitize_filename(f"{filename}_genress.txt")
    full_path = os.path.join(valid_folder, valid_filename)
    with open(full_path, "w") as file:
        file.writelines(genres)
    return full_path


def main():
    parser = argparse.ArgumentParser(
        description="Скачивает информацию о книгах и их текст"
        )
    parser.add_argument("start_id", type=int,
        help="Начало диапазона идентификаторов скачиваемых книг")
    parser.add_argument("end_id", type=int,
        help="Конец диапазона индентификаторов скачиваемых книг (книга с этим идентификатором скачана не будет)")
    id_range = parser.parse_args()
    
    lib_url = "https://tululu.org"
    start = id_range.start_id
    finish = id_range.end_id
    while start < finish:
        try:
            for page in range(start, finish):
                if page >= (finish - 1):
                    start = finish
                url = urljoin(lib_url, "txt.php")
                page_url = urljoin(lib_url, f"b{page}/")
                try:
                    page_response = get_book_page(page_url)
                except requests.HTTPError as err:
                    logging.exception(f"На странице {page} нет книги", exc_info=False)
                    continue
                soup = BeautifulSoup(page_response.text, "lxml")
                about_book = parse_book_page(soup)
                title = about_book["title"]
                filename = f"{page}. {title}"
                txt_selector = ".d_book a[title$='скачать книгу txt']"
                try:
                    rel_txt_url = soup.select_one(txt_selector)["href"]
                except TypeError:
                        print(f'В библиотеке нет текста книги {title}')
                        continue
                txt_url = urljoin(page_url, rel_txt_url)

                if about_book["comments"]:
                    comments_path = save_comments(filename, about_book["comments"])
                genres_path = save_genres(filename, about_book["genres"])

                try:
                    cover_path = download_image(urljoin(page_url, about_book["img_scr"]), "images/")
                    book_namepath = download_txt(txt_url, filename, "books/")
                except requests.HTTPError as err:
                    logging.exception(f'В библиотеке нет текста книги "{title}"',
                        exc_info=False)
                    continue
        except requests.ConnectionError as err:
            logging.exception("Проверьте соединение с сетью", exc_info=False)
            print(err)
            start = page
            time.sleep(180)


if __name__ == "__main__":
    main()