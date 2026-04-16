import logging
import time


logger = logging.getLogger(__name__)


class WebDriverCookie:
    def __init__(self, url="https://www.wildberries.ru/", target_cookie="x_wbaas_token"):
        self.url = url
        self.target_cookie = target_cookie
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    def get_token(self):
        logger.info("Запускаем браузер для получения токена x_wbaas_token...")

        from seleniumbase import Driver

        driver = Driver(uc=True, headless=True)
        try:
            driver.open(self.url)
            for attempt in range(1, 4):
                logger.info("Попытка %s получить куки...", attempt)

                raw_cookies = driver.execute_cdp_cmd("Network.getAllCookies", {})["cookies"]
                cookie_dict = {c["name"]: c["value"] for c in raw_cookies}

                if self.target_cookie in cookie_dict:
                    logger.info("Токен %s и остальные куки успешно получены!", self.target_cookie)
                    return cookie_dict

                time.sleep(5)

            logger.warning("Токен %s не найден.", self.target_cookie)
            return None
        finally:
            driver.quit()


def fetch_wb_token():
    return WebDriverCookie().get_token()
