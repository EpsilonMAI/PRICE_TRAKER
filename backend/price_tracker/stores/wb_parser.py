import logging
import re
import time
import urllib.parse


logger = logging.getLogger(__name__)


def is_exact_model(query: str, product_name: str) -> bool:
    """
    Проверяет, не подсунул ли маркетплейс улучшенную/другую модель (Pro, Max, Plus и т.д.).
    """
    modifiers = {"pro", "plus", "max", "ultra", "mini", "lite", "fe", "se", "5g", "4g", "xt", "ti"}

    query_words = set(re.findall(r"[a-z0-9а-яё]+", query.lower()))
    name_words = set(re.findall(r"[a-z0-9а-яё]+", product_name.lower()))

    for mod in modifiers:
        if mod in name_words and mod not in query_words:
            return False

    return True


def fetch_best_wb_offer(query: str):
    """
    Выполняет поиск на Wildberries через браузер.
    Использует веб-фильтр оригинальности и сортировку по возрастанию цены.
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
                    price_el.text.replace(" ", "")
                    .replace("₽", "")
                    .replace("₸", "")
                    .replace(" ", "")
                    .strip()
                )

                if not price_text.isdigit():
                    continue
                price = int(price_text)

                old_price = price
                try:
                    old_price_el = card.find_element("css selector", "del")
                    old_price_text = (
                        old_price_el.text.replace(" ", "")
                        .replace("₽", "")
                        .replace("₸", "")
                        .replace(" ", "")
                        .strip()
                    )
                    if old_price_text.isdigit():
                        old_price = int(old_price_text)
                except Exception:
                    pass

                link_el = card.find_element("css selector", "a.product-card__link")
                url = link_el.get_attribute("href")
                item_id = url.split("catalog/")[1].split("/detail")[0] if "catalog/" in url else "Unknown"

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
