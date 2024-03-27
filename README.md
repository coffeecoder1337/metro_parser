# Парсер для сайта Metro

## Библиотеки
- requests
- BeautifulSoup4
- asyncio
- aiohttp

## Установка

Клоинруем проект
```
git clone https://github.com/coffeecoder1337/metro_parser
```
```
cd metro_parser
```

Ставим виртуальное окружение
```
python -m venv venv
```

Активируем виртуальное окружение

Windows:
```
cd venv/Scripts/
```
```
activate
```
```
cd ../..
```

Linux:
```
source venv/bin/activate
```

Установка библиотек:
```
pip install requirements.txt
```

## Запуск
```
python main.py
```

## Использование
По умолчанию парсер собирает данные в Москве. Для смены региона на Санкт-Петербург нужно изменить значение переменной `request_headers` на `headers.headers_spb`.
<br><br>
Данные сохраняются в файл `data.json`. [Категория для парсинга по умолчанию](https://online.metro-cc.ru/category/myasnye/myaso).


