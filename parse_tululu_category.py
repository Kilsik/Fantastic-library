import requests
import os
import json

from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from pathvalidate import sanitize_filepath, sanitize_filename


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
        "img_scr": img_url,
        "comments": comments,
        "genres": genres
    }


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
    # check_for_redirect(response)
    valid_folder = sanitize_filepath(folder)
    Path(valid_folder).mkdir(exist_ok=True)
    valid_filename = sanitize_filename(filename)
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


def main():
    fantastic_url = 'https://tululu.org/l55/'
    books_description = []
    for page in range(1,5):
        page_url = urljoin(fantastic_url, str(page))
        response = requests.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        about_books = soup.find_all('table', class_='d_book')
        for book in about_books:
            # book_title = 
            book_url = urljoin(fantastic_url, book.find('a')['href'])
            book_response = get_book_page(book_url)
            book_soup = BeautifulSoup(book_response.text, 'lxml')
            about_book = parse_book_page(book_soup)
            title = about_book['title']
            try:
                rel_txt_url = book_soup.find('table', class_='d_book').find('a', string='скачать txt')['href']
            except TypeError:
                print(f'В библиотеке нет текста книги {title}')
                continue
            txt_url = urljoin(book_url, rel_txt_url)
            _, book_num = urlsplit(txt_url)[3].split('=')
            txt_filename = f'{book_num}. {title}.txt'
            img_url = urljoin(book_url, about_book['img_scr'])
            book_namepath = download_txt(txt_url, txt_filename)
            cover_path = download_image(img_url)
            books_description.append(about_book)
    books_description_json = json.dumps(books_description, ensure_ascii=False).encode('utf-8')
    with open('books_description.json', 'w', encoding='utf-8') as json_file:
        json.dump(books_description, json_file, ensure_ascii=False)


if __name__ == '__main__':
    main()