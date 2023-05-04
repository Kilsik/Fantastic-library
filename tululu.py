import requests
import os
import argparse

from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filepath, sanitize_filename
from urllib.parse import urljoin


def parse_book_page(url):
    """
    Собираем информацию о книге
    """

    page_response = requests.get(url)
    page_response.raise_for_status()
    check_for_redirect(page_response)
    
    soup = BeautifulSoup(page_response.text, "lxml")
    about_book = soup.find("td", class_="ow_px_td").find("h1").text
    raw_title, raw_author = about_book.split(sep="::")

    title = raw_title.strip()
    author = raw_author.strip()
    
    rel_url = soup.find("div", class_="bookimage").find("img")["src"]
    img_url = urljoin(url, rel_url)

    raw_comments = soup.find_all("div", class_="texts")
    comments = []
    for comment in raw_comments:
        comment_text = comment.find("span", class_="black").text
        comments.append(comment_text)
    
    raw_genres = soup.find("span", class_="d_book").find_all("a")
    genres = []
    for genre in raw_genres:
        genres.append(genre.text)

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
        return True


def download_txt(url, filename, folder="books/"):
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
    if check_for_redirect(response):
        valid_folder = sanitize_filepath(folder)
        Path(valid_folder).mkdir(exist_ok=True)
        valid_filename = sanitize_filename(filename)+".txt"
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

    if not comments:
        return None
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
    parser.add_argument("start_id",
        help="Начало диапазона идентификаторов скачиваемых книг")
    parser.add_argument("end_id",
        help="Конец диапазона индентификаторов скачиваемых книг (книга с этим идентификатором скачана не будет)")
    id_range = parser.parse_args()
    from_id = int(id_range.start_id)
    to_id = int(id_range.end_id)

    lib_url = "https://tululu.org"
    for id in range(from_id, to_id):
        text_url = urljoin(lib_url, f"txt.php?id={id}")
        page_url = urljoin(lib_url, f"b{id}/")
        try:
            book_info = parse_book_page(page_url)
        except requests.HTTPError:
            continue
        title = book_info["title"]
        filename = f"{id}. {title}"
        cover_path = download_image(book_info["cover_url"])
        comments_path = save_comments(filename, book_info["comments"])
        genres_path = save_genres(filename, book_info["genres"])

        try:
            book_name = download_txt(text_url, filename)
        except requests.HTTPError:
            continue


if __name__ == "__main__":
    main()