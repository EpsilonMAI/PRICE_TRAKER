from seleniumbase import Driver
from loguru import logger
import time

class WebDriverCookie:
    def __init__(self, url="https://www.wildberries.ru/", target_cookie="x_wbaas_token"):
        self.url = url
        self.target_cookie = target_cookie
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    def get_token(self):
        # Используем uc=True для обхода защиты
        logger.info("Запускаем браузер для получения токена x_wbaas_token...")
        driver = Driver(uc=True, headless=True) # Можно поставить False для отладки
        try:
            driver.open(self.url)
            # Ждем появления токена в куках (делаем 3 попытки)
            for attempt in range(1, 4):
                logger.info(f"Попытка {attempt} получить куки...")
                
                # Получаем сырой список всех кук от браузера
                raw_cookies = driver.execute_cdp_cmd('Network.getAllCookies', {})['cookies']
                
                # Превращаем список в словарь: {'имя_куки': 'значение'}
                cookie_dict = {c['name']: c['value'] for c in raw_cookies}
                
                # Проверяем, есть ли в этом словаре антибот-токен
                if self.target_cookie in cookie_dict:
                    logger.success(f"Токен {self.target_cookie} и остальные куки успешно получены!")
                    return cookie_dict
                
                time.sleep(5)
            logger.warning(f"Токен {self.target_cookie} не найден.")
            return None
        finally:
            driver.quit()

def fetch_wb_token():
    return WebDriverCookie().get_token()
