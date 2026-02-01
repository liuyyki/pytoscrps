import requests, re, csv, json
from bs4 import BeautifulSoup

site = "https://www.testsite.testsite"
Headers = {
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    "Cache-Control": "no-cache",
    "Origin": site,
    "Referer": site,
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0",
}
Cookie = {'geo_city_id': 'a%3A2%3A%7Bs%3A7%3A%22city_id%22%3Bs%3A2%3A%2222%22%3Bs%3A13%3A%22is_determined%22%3Bb%3A1%3B%7D'}



def build_soup(url):
    """Получает урл, преобразует в страницу и возвращает объект soup"""
    page = requests.get(url, headers=Headers, cookies=Cookie)
    page = page.text
    # print(page)
    return BeautifulSoup(page, 'lxml')


def check_quant_page(url):
    """Проверяет кол-во страниц в разделе"""

    soup = build_soup(url)
    print(soup.find('button', class_="City_city__3Xy_P").text)

    try:
        page_summ = int(soup.find('div', class_='page-navigation').find('a', class_='next').find_previous('a').text)
    except Exception:
        page_summ = 1
    
    print('страниц каталога: ', page_summ)
    return page_summ


def check_quant_page_n(url):
    """Проверяет кол-во страниц в разделе"""

    soup = build_soup(url)
    print(soup.find('button', class_="City_city__3Xy_P").text)

    items_count = soup.find('span', class_="CatalogProducts_total__2tCLf").get_text().split()
    print(items_count[0])

    page_summ = int(items_count[0]) // 32 + 1

    print('страниц каталога: ', page_summ)
    return page_summ


def get_catalog_params(url):
    """возвращает параметры для запроса"""

    soup = build_soup(url)
    try:
        brand_id = soup.find('form', id="filter_form", class_="smartfilter").find('input', attrs={"name": "f[brand_id]"})['value']
    except:
        brand_id = ''

    try:
        category_id = soup.find('form', id="filter_form", class_="smartfilter").find('input', attrs={"name": "f[category_id]"})['value']
    except:
        category_id = soup.find('div', class_="i-flocktory", attrs={"data-fl-action": "track-category-view"})["data-fl-category-id"]

    return brand_id, category_id


def get_catalog_page(page_num, size, url, b_id='', c_id=''):
    """отправляет ajax запрос и возвращает soup страницы каталога из json"""
    data = {
        "page": page_num,
        "page_size": size,
        "sort_by": "",
        "sort_order": "asc",
        "f[brand_id]": b_id,
        "f[category_id]": c_id,
        "act": "Catalog.show",
    }
    Headers['Referer'] = url
    content = requests.post(site + '/ajax/?act=Catalog.show', headers=Headers, data=data, cookies=Cookie)
    json_content = content.json()
    catalog_page = json_content['data']['column_right']

    return BeautifulSoup(catalog_page, 'lxml')


def get_catalog_page_n(page_num, url, c_id=''):
    """отправляет ajax запрос и возвращает soup страницы каталога из json"""

    data = {
        "act": "Catalog.saleCatalog",
        "page_size": "undefined",
        "page": page_num,
        "sort_by": "sort",
        "sort_order": "asc",
        "f[category_id]": c_id, #id обязательно должен быть получен
        "f[prop][2][]": "3987",
    }
    if page_num > 1: data['page_size'] = "32"

    Headers['Referer'] = url
    content = requests.post(site + '/ajax/?act=Catalog.saleCatalog', headers=Headers, data=data, cookies=Cookie)
    json_content = content.json()
    catalog_page = json_content['data']['products']['products']

    return BeautifulSoup(catalog_page, 'lxml')


def get_params(url):
    ind = url.find('/?')
    params = url[ind+2:].split('&')
    return params


def get_js_string(data):
    """получает строку из тэга script"""

    b = data.find('div', id='main')
    b = re.findall(r"/testsite/product-tabs-[\da-zA-Z]*", str(b), re.MULTILINE)
    c = data.find('div', id=b).find_next('script').string
    c = c[c.find('"product":{"id":'):c.find('dataTableNorms":')].strip()
    return c


def clearing_str(a):
    """Достает из строки подстроку характеричстики"""

    a = re.findall(r'composition":"(.+?)","', a, re.MULTILINE | re.IGNORECASE)
    charact = re.sub(r"\\n|\\r|\s{2,}", "", a[0])
    charact = charact.replace('\\u003c', '<')

    return charact


def get_product_page_link(soup):
    product_links = soup.find_all('a', class_="j_product-brand j_product-link", attrs={'data-testid': 'product__item-link'})
    print(1, product_links)
    if len(product_links) == 0:
        product_links = soup.find_all('a', class_="CatalogItem_link__1znmD")
        print(2, product_links)
        
    print('обнаружено продуктов на странице:', len(product_links))
    links = [link['href'] for link in product_links]

    return links


def scan_product_page(link):
    page = build_soup(link)
    data = {'official': 'N', 'currency': 'р'}

    data['brand'] = page.find('a', class_='ProductBrand_product_card_brand_link__2s_IJ').get_text(strip=True)
    data['name'] = page.find('div', class_='inner j_product-name j_adj_subtitle').get_text(strip=True)
    data['groups'] = [a.get_text() for a in page.find('ul', class_='breadcrumbs').find_all('a')]
    data['descr'] = page.find('div', attrs={'data-testid': 'ProductDescription__content'}).get_text(strip=True)
    data['prop'] = clearing_str(get_js_string(page))




def get_offers(page):
    for offer in page.find_all('div', class_='offer-item'):
        data['art'] = offer['data-artnumber']
        try:
            data['mass'] = offer.find('span', class_='type').string.strip()
        except Exception:
            data['mass'] = ''

        try:
            data['cost'] = offer.find('span', class_='price-optimal').span.string.strip()
        except Exception:
            data['cost'] = offer.find('div', class_='price-optimal').span.string.strip()
        else:
            data['cost'] = ''


def get_product_data(soup, count=0):
    # собирает данные из карточки товара

    page_items = soup.select('ul.product-list:not(.slick-slider) li.product-item.j_product.j_adj_item')
    print('обнаружено продуктов на странице:', len(page_items))
    tmp_data = []

    for item in page_items:
        try:
            brand = item.find('h3', class_='h4 j_adj_title').a.string.strip()
        except Exception as e:
            print(e.args)
            brand = ''

        name = item.find('div', class_='inner j_product-name j_adj_subtitle').get_text(strip=True)
        prod_link = 'https://testsite.testsite' + item.find('a', class_='j_product-link image')['href']
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

        descr = product_page.find('div', attrs={'data-testid': 'ProductDescription__content'}).get_text(strip=True)

        charact = clearing_str(get_js_string(product_page))

        artic_group = item.find_all('div', class_='offer-item')[0]['data-artnumber']

        if len(item.find_all('div', class_='offer-item')) > 1:
            outer_code = item.find_all('div', class_='offer-item')[0]['data-artnumber'] + 'П'
        else:
            outer_code = ''

        for offer in item.find_all('div', class_='offer-item'):

            art = offer['data-artnumber']
            try:
                mass = offer.find('span', class_='type').string.strip()
            except Exception:
                mass = ''

            try:
                cost = offer.find('span', class_='price-optimal').span.string.strip()
            except Exception:
                cost = offer.find('div', class_='price-optimal').span.string.strip()
            else:
                cost = ''

            data = {
                'official': 'N',
                'outer_code': outer_code,
                'art': art,
                'artic_group': artic_group,
                'group1': group1,
                'group2': group2,
                'group3': group3,
                'brand': brand,
                'name': brand + ' ' + name,
                'mass': mass,
                'cost': cost,
                'currency': 'р',
                'country': '',
                'age': '',
                'size': '',
                'feature': '',
                'special': '',
                'descr': descr,
                'charact': charact,
            }
            outer_code = ''

            print(count, ' Данные товара art:', data['art'], ' - собраны')
            count += 1
            tmp_data.append(data)

    return tmp_data


def write_f(data):

    with open('base.csv', 'w', encoding='utf-8') as csv_f:
        header = {
            'official': 'АКТ. (Y/N)', 'outer_code': 'Внешний код', 'art': 'Арт.', 'artic_group': 'группа товаров', 'group1': 'Группа 1',
            'group3': 'Группа 3', 'group2': 'Группа 2', 'brand': 'Бренд', 'name': 'Название',
            'mass': 'Вес', 'cost': 'Цена', 'currency': 'Валюта', 'country': 'Страна',
            'age': 'Возраст', 'size': 'размер', 'feature': 'ингредиент',
            'special': 'серия', 'descr': 'Детальное описание', 'charact': 'Состав'
        }

        writer = csv.writer(csv_f, dialect='excel', delimiter='`')
        writer.writerow((
            header['official'], header['outer_code'], header['art'], header['artic_group'], header['group1'], header['group3'],
            header['group2'], header['brand'], header['name'], header['mass'], header['cost'],
            header['currency'], header['country'], header['age'], header['size'], header['feature'],
            header['special'], header['descr'], header['charact']
        ))

        for i in data:
            writer.writerow((
                i['official'], i['outer_code'], i['art'], i['artic_group'], i['group1'], i['group3'], i['group2'], i['brand'],
                i['name'], i['mass'], i['cost'], i['currency'], i['country'], i['age'], i['size'],
                i['feature'], i['special'], i['descr'], i['charact']
            ))
            print('Записан:', i['art'])


def main():

    url = str(input('введите URL: '))

    datas = []

    if url.find("/?") <= 0:
        print('old_list')
        page_summ = check_quant_page(url)
        size = '32'
        if page_summ > 2:
            size = '100'

        b_id, c_id = get_catalog_params(url)

        for i in range(1, page_summ + 1):
            if i == 1:
                soup = build_soup(url)
            else:
                soup = get_catalog_page(i, size, url, b_id, c_id)
            datas += get_product_data(soup)
    else:
        print('new_list')
        page_summ = check_quant_page_n(url)
        b_id, c_id = get_catalog_params(url)

        for i in range(1, page_summ + 1):
            if i == 1:
                soup = build_soup(url)
            else:
                soup = get_catalog_page_n(i, url, c_id)

            print(get_product_page_link(soup))
    write_f(datas)


if __name__ == '__main__':
    main()
