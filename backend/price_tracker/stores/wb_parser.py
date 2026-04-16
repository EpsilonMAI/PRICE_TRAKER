"""Парсер товаров с Wildberries.

Поддерживает два режима:
- Парсинг по URL товара через официальное API WB (быстро, без браузера)
- Поиск лучшего предложения по поисковому запросу через браузер (Selenium)
"""
import logging
import re
import time
import urllib.parse

import requests

logger = logging.getLogger(__name__)

# Шаблон для извлечения артикула из URL WB
_WB_ARTICLE_RE = re.compile(r"/catalog/(\d+)/")


def extract_wb_article(url: str) -> str | None:
    """Извлечь артикул товара из URL Wildberries.

    Args:
        url: Ссылка вида https://www.wildberries.ru/catalog/12345678/detail.aspx

    Returns:
        str | None: Артикул товара или None если не удалось распознать
    """
    match = _WB_ARTICLE_RE.search(url)
    return match.group(1) if match else None


def fetch_wb_product_by_url(url: str) -> dict | None:
    """Получить данные о товаре WB по ссылке через официальное API.

    Не использует браузер — работает быстро (~1 сек).

    Args:
        url: Прямая ссылка на товар Wildberries

    Returns:
        dict | None: Данные о товаре или None при ошибке
    """
    article = extract_wb_article(url)
    if not article:
        logger.warning("Не удалось извлечь артикул из URL: %s", url)
        return None

    logger.info("Запрашиваем данные товара WB, артикул: %s", article)

    # WB перешёл на API v4 — структура ответа изменилась:
    # products[] теперь в корне (не внутри data), цена в sizes[].price.product
    api_url = (
        f"https://card.wb.ru/cards/v4/detail"
        f"?appType=1&curr=rub&dest=-1257786&spp=30&nm={article}"
    )

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.error("Ошибка запроса к WB API: %s", e)
        return None

    try:
        # v4: products[] прямо в корне ответа, не внутри data
        products = data.get("products") or data.get("data", {}).get("products", [])
        if not products:
            logger.warning("Товар с артикулом %s не найден в ответе API", article)
            return None

        product = products[0]
        name = product.get("name", "")
        brand = product.get("brand", "")
        in_stock = product.get("totalQuantity", 0) > 0

        sizes = product.get("sizes", [])
        price = None
        old_price = None

        for size in sizes:
            price_data = size.get("price", {})
            if not price_data:
                continue
            # v4: price.product = продажная цена в копейках
            #     price.basic   = оригинальная (зачёркнутая) цена в копейках
            product_price = price_data.get("product")
            basic_price = price_data.get("basic")
            if product_price:
                price = product_price // 100
                old_price = basic_price // 100 if basic_price else price
                break

        if price is None:
            logger.warning("Цена для артикула %s не найдена (нет в наличии?)", article)
            return None

        logger.info("Получен товар: %s, цена: %s RUB, в наличии: %s", name, price, in_stock)

        return {
            "id": article,
            "name": name,
            "brand": brand,
            "price": price,
            "old_price": old_price,
            "in_stock": in_stock,
            "url": url,
        }

    except (KeyError, IndexError, TypeError) as e:
        logger.error("Ошибка разбора ответа WB API: %s", e)
        return None


def is_exact_model(query: str, product_name: str) -> bool:
    """Проверяет, не подсунул ли маркетплейс улучшенную/другую модель.

    Args:
        query: Поисковый запрос пользователя
        product_name: Название найденного товара

    Returns:
        bool: True если товар соответствует запросу
    """
    modifiers = {"pro", "plus", "max", "ultra", "mini", "lite", "fe", "se", "5g", "4g", "xt", "ti"}
    query_words = set(re.findall(r"[a-z0-9а-яё]+", query.lower()))
    name_words = set(re.findall(r"[a-z0-9а-яё]+", product_name.lower()))

    for mod in modifiers:
        if mod in name_words and mod not in query_words:
            return False
    return True


def fetch_best_wb_offer(query: str) -> dict | None:
    """Выполняет поиск на Wildberries через браузер.

    Использует веб-фильтр оригинальности и сортировку по возрастанию цены.

    Args:
        query: Поисковый запрос

    Returns:
        dict | None: Лучшее найденное предложение или None
    """
    logger.info("Начинаем поиск лучшего предложения WB для: '%s'", query)

    from seleniumbase import Driver

    driver = Driver(uc=True, headless=True)

    try:
        safe_query = urllib.parse.quote_plus(query)
        search_url = (
            "https://www.wildberries.ru/catalog/0/search.aspx"
            f"?page=1&sort=priceup&search={safe_query}&foriginal=1&meta_charcs=true"
        )

        driver.uc_open_with_reconnect(search_url, 4)
        time.sleep(5)

        for _ in range(4):
            driver.execute_script("window.scrollBy(0, 1500);")
            time.sleep(1.5)

        cards = driver.find_elements("css selector", "article.product-card")

        if not cards:
            logger.warning("Товары по запросу '%s' не найдены.", query)
            return None

        for card in cards[:50]:
            try:
                name_el = card.find_element("css selector", "span.product-card__name")
                name = name_el.text.strip()

                if not is_exact_model(query, name):
                    continue

                brand_el = card.find_element("css selector", "span.product-card__brand")
                brand = brand_el.text.strip()

                price_el = card.find_element("css selector", "ins.price__lower-price")
                price_text = (
                    price_el.text.replace("\u00a0", "")
                    .replace(" ", "")
                    .replace("₽", "")
                    .replace("₸", "")
                    .strip()
                )

                if not price_text.isdigit():
                    continue
                price = int(price_text)

                old_price = price
                try:
                    old_price_el = card.find_element("css selector", "del")
                    old_price_text = (
                        old_price_el.text.replace("\u00a0", "")
                        .replace(" ", "")
                        .replace("₽", "")
                        .replace("₸", "")
                        .strip()
                    )
                    if old_price_text.isdigit():
                        old_price = int(old_price_text)
                except Exception:
                    pass

                link_el = card.find_element("css selector", "a.product-card__link")
                url = link_el.get_attribute("href")
                item_id = (
                    url.split("catalog/")[1].split("/detail")[0]
                    if "catalog/" in url
                    else "Unknown"
                )

                logger.info("Найдено лучшее предложение: %s за %s RUB", name, price)

                return {
                    "id": item_id,
                    "name": name,
                    "brand": brand,
                    "price": price,
                    "old_price": old_price,
                    "url": url,
                }

            except Exception:
                continue

        logger.warning("Среди просмотренных товаров для '%s' не нашлось точного совпадения.", query)
        return None

    finally:
        driver.quit()
