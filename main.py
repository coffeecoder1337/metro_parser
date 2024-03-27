# Для каждой торговой площадки требования одни и те же. Спарсить любую категорию, где более 100 товаров, для городов Москва и Санкт-Петербург и выгрузить в любой удобный формат(csv, json, xlsx). Важно, чтобы товары были в наличии.
# Необходимые данные: 
# - id товара из сайта/приложения
# - наименование
# - ссылка на товар
# - регулярная цена
# - промо цена
# - бренд


from bs4 import BeautifulSoup as BS
import asyncio
import aiohttp
import json
import requests
import time
import headers


base_url = 'https://online.metro-cc.ru'
category_url = '/category/myasnye/myaso'
request_headers = headers.headers_msc # headers_msc - Москва, headers_spb - Санкт-Петербуг

all_links = []
all_goods = dict()


def get_data(soup, link):
	''' Дополняет all_goods названием, брендом, ссылкой и id конкретного товара '''
	title = soup.find('h1', class_='product-page-content__product-name').span.text.strip()
	good_id = soup.find('p', class_='product-page-content__article').text.replace('Артикул: ', '').strip()
	brand = get_brand(soup)

	all_goods[good_id]['title'] = title
	all_goods[good_id]['brand'] = brand
	all_goods[good_id]['link'] = link
	all_goods[good_id]['id'] = good_id


def get_goods_id_and_price(item):
	''' Возвращает id товара, актуальную цену и старую цену (если есть) '''
	actual_price_penny = None
	actual_price_tag = item.find('div', class_='product-unit-prices__actual-wrapper')
	actual_price_rubles = actual_price_tag.find('span', class_='product-price__sum-rubles').text
	actual_price_rubles = actual_price_rubles.strip().replace('\xa0', '')
	price_unit = actual_price_tag.find('span', class_='product-price__unit').text

	old_price_penny = None
	old_price = None
	try:
		old_price_tag = item.find('div', class_='product-unit-prices__old-wrapper')
		old_price_rubles = old_price_tag.find('span', class_='product-price__sum-rubles').text
		old_price_rubles = old_price_rubles.strip().replace('\xa0', '')
	except:
		# нет старой цены
		pass
	else:
		
		try:
			old_price_penny = old_price_tag.find('span', class_='product-price__sum-penny').text
		except:
			# нет копеек в цене
			old_price = f"{old_price_rubles} руб.{price_unit.strip()}"
		else:
			old_price = f"{old_price_rubles}{old_price_penny} руб.{price_unit.strip()}"


	try:
		actual_price_penny = actual_price_tag.find('span', class_='product-price__sum-penny').text
	except:
		# нет копеек в цене
		actual_price = f"{actual_price_rubles} руб.{price_unit.strip()}"
	else:
		actual_price = f"{actual_price_rubles}{actual_price_penny} руб.{price_unit.strip()}"
	

	goods_id = item.get('id')
	return goods_id, actual_price, old_price


def get_brand(soup):
	''' Возвращает бренд товара '''
	attrs = soup.find_all('li', class_='product-attributes__list-item')
	brand = 'Нет бренда'
	for attr in attrs:
		attr_name = attr.find('span', class_='product-attributes__list-item-name-text')
		attr_name_text = attr_name.text
		attr_name_text = attr_name_text.strip().lower()
		if 'бренд' in attr_name_text:
			try:
				brand = attr_name.parent.parent.a.text.strip().capitalize()
			except Exception as e:
				pass

	return brand


def get_all_links_and_init_goods(soup):
	''' Заполняет all_links ссылками на все товары с сайта. Заполняет all_goods значениями. Ключ id товара, занчение словарь с ценами '''
	items = soup.find(id="products-inner").find_all('div', class_='product-card')
	for item in items:
		try:
			title_tag = item.find('a', class_='product-card-name')
			link = title_tag.get('href')
			goods_id, goods_actual_price, goods_old_price = get_goods_id_and_price(item)

		except:
			# товар раскупили
			continue
		else:
			all_goods[goods_id] = dict()
			all_goods[goods_id]['price'] = goods_actual_price
			if goods_old_price is not None:
				all_goods[goods_id]['old_price'] = goods_old_price
			all_links.append(link)


async def parse_links_and_prices(session, page):
	url = f"{base_url}{category_url}?page={page}"

	async with session.get(url=url, headers=request_headers) as response:
		response_text = await response.text()
		soup = BS(response_text, 'lxml')
		get_all_links_and_init_goods(soup)

	print(f'Page {page} completed.')


async def links_gather_data():
	goods_list_url = f"{base_url}{category_url}"

	async with aiohttp.ClientSession() as session:
		response = await session.get(url=goods_list_url, headers=request_headers)
		soup = BS(await response.text(), 'lxml')
		pages_count = soup.find_all('a', class_='v-pagination__item catalog-paginate__item')[-1].text # получаем последнее число из пагинатора

		tasks = []

		for page in range(1, int(pages_count) + 1):
			task = asyncio.create_task(parse_links_and_prices(session, page))
			tasks.append(task)

		await asyncio.gather(*tasks)


async def get_goods_data(session, link):
	goods_url = base_url + link

	async with session.get(url=goods_url, headers=request_headers) as response:
		response_text = await response.text()

		soup = BS(response_text, 'lxml')
		get_data(soup, goods_url)
	print(f'Item {link} completed.')


async def goods_gather_data():
	myaso_url = f"{base_url}{category_url}"

	async with aiohttp.ClientSession() as session:
		tasks = []

		for link in all_links:
			task = asyncio.create_task(get_goods_data(session, link))
			tasks.append(task)

		await asyncio.gather(*tasks)


def main():
	start = time.time()
	asyncio.run(links_gather_data())
	asyncio.run(goods_gather_data())
	end = time.time() - start
	filename = 'data.json'

	with open(filename, 'wb') as f:
		f.write(json.dumps(all_goods, sort_keys=True, indent=4, ensure_ascii=False).encode('utf-8'))
	print(f'Product data is recorded in a file: {filename}. Total products count is {len(all_goods)}. Execution time: {end} seconds')


if __name__ == '__main__':
	main()

