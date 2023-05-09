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


def parse_book_page(page_response):
    """
    Собираем информацию о книге
    """

    soup = BeautifulSoup(page_response.text, "lxml")
    about_book = soup.find("td", class_="ow_px_td").find("h1").text
    raw_title, raw_author = about_book.split(sep="::")

    title = raw_title.strip()
    author = raw_author.strip()
    
    img_url = soup.find("div", class_="bookimage").find("img")["src"]

    raw_comments = soup.find_all("div", class_="texts")
    comments = []
    for comment in raw_comments:
        comment_text = comment.find("span", class_="black").text
        comments.append(comment_text)
    
    raw_genres = soup.find("span", class_="d_book").find_all("a")
    genres = [genre.text for genre in raw_genres]

    return {
        "title": title,
        "author": author,
        "cover_url": img_url,
        "comments": comments,
        "genres": genres
    }


def check_for_redirect(response):
    """
    Проверяем наличие книги
    """

    if response.history:
        raise requests.HTTPError()
    else:
        return


def download_txt(url, page, filename, folder="books/"):
    """Скачиваем текстовые файлы.
    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.
    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    param = {"id": page}
    response = requests.get(url, params=param)
    response.raise_for_status()
    check_for_redirect(response)
    valid_folder = sanitize_filepath(folder)
    Path(valid_folder).mkdir(exist_ok=True)
    text_filename = sanitize_filename(filename)
    valid_filename = f"{text_filename}.txt"
    full_path = os.path.join(valid_folder, valid_filename)
    with open(full_path, "w", encoding="utf-8") as file:
        file.write(response.text)
    return full_path
    

def download_image(url, folder="images/"):
    """
    Скачиваем изображения обложек книг
    """

    valid_folder = sanitize_filepath(folder)
    Path(valid_folder).mkdir(exist_ok=True)
    img_filename = url.split("/")[-1]
    valid_filename = sanitize_filename(f"{img_filename}")
    full_path = os.path.join(valid_folder, valid_filename)
    if not Path(full_path).exists():
        response = requests.get(url)
        response.raise_for_status()
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
                    logging.exception("Настранице нет книги", exc_info=False)
                    continue
                about_book = parse_book_page(page_response)
                title = about_book["title"]
                filename = f"{page}. {title}"
                cover_path = download_image(urljoin(lib_url, about_book["cover_url"]))
                if about_book["comments"]:
                    comments_path = save_comments(filename, about_book["comments"])
                genres_path = save_genres(filename, about_book["genres"])

                try:
                    book_namepath = download_txt(url, page, filename)
                except requests.HTTPError:
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