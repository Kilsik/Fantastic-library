import requests
import os

from pathlib import Path
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filepath, sanitize_filename
from urllib.parse import urljoin


def check_for_redirect(response):
    """ Check the availability of the book """
    if response.history:
        raise requests.HTTPError()
    else:
        return True


def download_txt(url, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
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
        with open(full_path, "w") as file:
            file.write(response.text)
        return full_path
    

def download_image(url, filename, folder='images/'):
    """
    Функция для скачивания изображений обложек книг
    """

    valid_folder = sanitize_filepath(folder)
    Path(valid_folder).mkdir(exist_ok=True)
    valid_filename = sanitize_filename(filename)
    full_path = os.path.join(valid_folder, valid_filename)
    if not Path(full_path).exists():
        response = requests.get(url)
        response.raise_for_status()
        with open(full_path, "wb") as file:
            file.write(response.content)
    return full_path


def main():
    lib_url = "https://tululu.org/txt.php"
    for id in range(1, 11):
        url = f"{lib_url}?id={id}"
        page_url = f"https://tululu.org/b{id}"
        page_response = requests.get(page_url)
        page_response.raise_for_status()
        soup = BeautifulSoup(page_response.text, "lxml")
        about_book = soup.find('td', class_='ow_px_td').find("h1").text
        try:
            title, author = about_book.split(sep='::')
        except ValueError:
            continue
        stripped_title = title.strip()
        stripped_author = author.strip()
        filename = f"{id}. {stripped_title}"
        try:
            book_name = download_txt(url, filename)
        except requests.HTTPError:
            continue
        rel_url = soup.find("div", class_="bookimage").find("img")['src']
        img_url = urljoin(page_url, rel_url)
        img_filename = rel_url.split('/')[-1]
        book_cover = download_image(img_url, img_filename)
        print(book_name)
        print(book_cover)
        

if __name__ == "__main__":
    main()