import requests
from bs4 import BeautifulSoup
import csv

Headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    "Cache-Control": "no-cache",
    "Origin": "https://www.testsite.testsite",
    "Referer": "https://www.testsite.testsite/",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0"
}
Cookie = {'geo_city_id': 'a%3A2%3A%7Bs%3A7%3A%22city_id%22%3Bs%3A2%3A%2222%22%3Bs%3A13%3A%22is_determined%22%3Bb%3A1%3B%7D'}


def build_soup(url):
    """Получает страницу, преобразует и возвращает объект soup"""
    page = requests.get(url, headers=Headers, cookies=Cookie)
    page = page.text
    return BeautifulSoup(page, 'lxml')


def check_quant_page(url):
    """Проверяет кол-во страниц в разделе"""
    soup = build_soup(url)
    print(soup.find('button', class_="City_city__3Xy_P undefined action-header-city").text)

    try:
        page_summ = int(soup.find('div', class_='page-navigation').find('a', class_='next').find_previous('a').text)
        print('страниц каталога: ', page_summ)
    except Exception:
        page_summ = 1
        print('страниц каталога: ', page_summ)

    return page_summ


def get_catalog_params(url):
    """возвращает параметры для запроса"""
    soup = build_soup(url)
    brand_id = soup.find('form', id="filter_form", class_="smartfilter").find('input', attrs={"name": "f[brand_id]"})['value']
    category_id = soup.find('form', id="filter_form", class_="smartfilter").find('input', attrs={"name": "f[category_id]"})['value']
    return brand_id, category_id


def get_catalog_page(page_num, size, url, b_id='', c_id=''):
    """отправляет ajax запрос и возвращает soup страницы каталога из json"""
    data = {
        "page": page_num, "page_size": size,
        "sort_by": "", "sort_order": "asc",
        "f[brand_id]": b_id, "f[category_id]": c_id,
        "act": "Catalog.show",
    }
    Headers['Referer'] = url
    content = requests.post('https://www.testsite.testsite/ajax/?act=Catalog.show', headers=Headers, data=data, cookies=Cookie)
    json_content = content.json()
    catalog_page = json_content['data']['column_right']
    return BeautifulSoup(catalog_page, 'lxml')


def get_product_data(soup, count=0):
    # собирает данные из карточки товара
    print('обнаружено продуктов на странице:', len(soup.find('div', id='products-wrapper').find_all('li', class_='product-item j_product j_adj_item')))
    tmp_data = []

    for item in soup.find('div', id='products-wrapper').find_all('li', class_='product-item j_product j_adj_item'):
        count += 1
        try:
            brand = item.find('h3', class_='h4 j_adj_title').a.string.strip()
        except Exception:
            brand = ''
        name = item.find('div', class_='inner j_product-name j_adj_subtitle').a.string.strip()

        prod_link = 'https://www.testsite.testsite' + item.find('a', class_='j_product-link image')['href']
        product_page = build_soup(prod_link)

        try:
            group1 = product_page.find('ul', class_='breadcrumbs').find_all('li', class_='')[2].a.string.strip()
        except Exception:
            group1 = ''
        try:
            group2 = product_page.find('ul', class_='breadcrumbs').find_all('li', class_='')[3].a.string.strip()
        except Exception:
            group2 = ''
        try:
            group3 = product_page.find('ul', class_='breadcrumbs').find_all('li', class_='')[4].a.string.strip()
        except Exception:
            group3 = ''
        descr = product_page.find('div', attrs={'data-testid': 'ProductDescription__content'}).get_text(
            strip=True)

        for offer in item.find_all('div', class_='offer-item'):
            outer_code = offer['data-id']
            art = offer['data-artnumber']
            try:
                mass = offer.find('span', class_='type').string.strip()
            except Exception:
                mass =''

            try:
                cost = offer.find('span', class_='price-optimal').span.string.strip()
            except Exception:
                cost = offer.find('div', class_='price-optimal').span.string.strip()
            except Exception:
                cost = ''

            data = {
                'official': 'N', 'outer_code': outer_code, 'art': art,
                'group1': group1, 'group2': group2, 'group3': group3,
                'brand': brand, 'name': brand + ' ' + name, 'mass': mass,
                'cost': cost, 'currency': 'RUB', 'country': '',
                'age': '', 'size': '', 'feature': '',
                'special': '', 'descr': descr, 'charact': '',
            }

            print(count, ' Данные товара art:', data['art'], ' - собраны')
            tmp_data.append(data)

    return tmp_data


def write_f(data):

   with open('base.csv', 'w', encoding='utf-8') as csv_f:
        header = {
            'official': 'АКТ. (Y/N)', 'outer_code': 'Внешний код', 'art': 'Арт.', 'group1': 'Группа 1',
            'group3': 'Группа 3', 'group2': 'Группа 2', 'brand': 'Брэнд', 'name': 'Название',
            'mass': 'Вес', 'cost': 'Цена', 'currency': 'Валюта', 'country': 'Страна',
            'age': 'Возраст', 'size': 'размер', 'feature': 'Основной',
            'special': 'Особая серия', 'descr': 'Детальное описание', 'charact': 'Состав'
        }

        writer = csv.writer(csv_f, dialect='excel', delimiter=',')
        writer.writerow((
            header['official'], header['outer_code'], header['art'], header['group1'], header['group3'],
            header['group2'], header['brand'], header['name'], header['mass'], header['cost'],
            header['currency'], header['country'], header['age'], header['size'], header['feature'],
            header['special'], header['descr'], header['charact']
        ))

        for i in data:
            writer.writerow((
                i['official'], i['outer_code'], i['art'], i['group1'], i['group3'], i['group2'], i['brand'],
                i['name'], i['mass'], i['cost'], i['currency'], i['country'], i['age'], i['size'],
                i['feature'], i['special'], i['descr'], i['charact']
            ))
            print('Записан:', i['art'])



def main():
    url = str(input('введите URL: '))
    page_summ = check_quant_page(url)
    size = '32'
    if page_summ > 2:
        size = '100'

    b_id, c_id = get_catalog_params(url)
    datas = []

    for i in range(page_summ+1):
        if i == 0:
            soup = build_soup(url)
        elif i == 1:
            continue
        else:
            soup = get_catalog_page(i, size, url, b_id, c_id)

        datas += get_product_data(soup)
    write_f(datas)

if __name__ == '__main__':
    main()
