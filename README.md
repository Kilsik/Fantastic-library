# Парсер книг с сайта tululu.org
Пакет состоит из консольного сервиса, который скачивает книги с их обложками, списком жанров и комментарии к ним с бесплатной онлайн библиотеки [tululu.org](https://tululu.org/) в указанном диапазоне идентификаторов, и, формируемого на их основе, локального сайта с книгами.
Пример локального сайта можно посмотреть на  [GitHub Pages](https://kilsik.github.io/pages/index1.html)
![image](https://github.com/Kilsik/Fantastic-library/assets/123646405/5b608229-7088-40c6-857d-afd284731f68)

### Окружение
Рекомендуется использовать [virtualenv/venv](https://docs.python.org/3/library/venv.html) для изоляции проекта.

##### Установка
Python3 должен быть уже установлен.
Затем используйте pip (или pip3 если есть конфликт с Python2) для
установки зависимостей:
```
pip install -r requirements.txt
```
#### Работа с утилитой:
##### Скачиваем все книги по порядку - tululu.py
С помощью этого сервиса Вы можете скачать все книги всех жанров.
При запуске укажите начало и конец диапазона идентификаторов книг в качестве аргументов. Например, для скачивания книг с идентификаторами от 20 до 29 необходимо выполнить команду:
```
$ python tululu.py 20 30
```
Здесь
- 20 - начальный идентификатор
- 30 - конечный идентификатор. Книга с этим идентификатором скачана не будет!
##### Скачиваем книги жанра научной фантастики - parse_tululu_categoty.py
Этот сервис можно запускать как с параметрами, так и без них. В результате работы у Вас появится JSON-файл с описанием книг и, опционально, тексты книг и их обложки.
Список параметров (все они именованные):
- --start_page  - начало диапазона страниц скачиваемых книг;
- --end_page    - конец диапазона страниц скачиваемых книг (книги страницы с этим номером скачаны не будут);
- --dest_folder - путь к каталогу с результатами парсинга: картинкам, книгам, JSON. По умолчанию - текущий каталог;
- --skip_imgs   - при наличии этого параметра не будут скачиваться обложки книг;
- --skip_txt    - при указании этого параметра не будут скачиваться тексты книг;
- --json_path   - имя файла с описанием книг. По умолчанию 'books_descriptions.json

Например, для скачивания книг со страницы 100 до страницы 110 без обложек, с сохранением в каталог library/ выполните команду:
```
python parse_tululu_categoty.py --start_page 100 --end_page 111 --dest_folder library --skip_img
```
При запуске сервиса без каких либо параметров будут скачаны все книги жанра научной фантастики с текстами и обложками (тексты в папке book/, обложки в папке images/ текущего каталога).

### Локальный сайт
Для работы с библиотекой в режиме оффлайн скачайте репозиторий. В папке pages запустите файл index1.html

### Наполнение оффлайн-библиотеки
Скачанные книги их json-файл с их описанием положите в папку media. Для формирования новых страниц библиотеки используйте команду
```
$ python render_website.py
```
После этого Ваша библиотека будет доступна даже в отсутствии сети Интернет по адресу [http://127.0.0.1:5500/pages/index1.html](http://127.0.0.1:5500/pages/index1.html)

### Примечание
 Код написан в образовательных целях на онлайн-курсах школы [Devman](https://dvmn.org/).
