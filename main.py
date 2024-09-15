import os
import time
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

# Токен вашего Telegram бота
API_TOKEN = '7414208053:AAHIvpanYjxwmWRZK6Fev0F-EjaPM8B9PXg'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ID пользователя для отправки результатов (замените на свой ID)
USER_ID = 5680097082  # Замените на ваш Telegram ID

# Функция для настройки драйвера Chrome в headless режиме
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Функция для записи данных в файл
def write_to_file(text):
    with open("projects.txt", "a", encoding="utf-8") as file:
        file.write(text + "\n")

# Функция для парсинга Kwork с использованием Selenium
def parse_kwork():
    url = "https://kwork.ru/projects?c=11"
    
    # Создаем драйвер
    driver = create_driver()

    # Очищаем файл перед записью новых данных
    with open("projects.txt", "w", encoding="utf-8") as file:
        file.write("")
    with open("projects.html", "w", encoding="utf-8") as file:
        file.write("")

    try:
        driver.get(url)

        # Функция для парсинга карточек проектов на странице
        def parse_cards():
            projects = driver.find_elements(By.CLASS_NAME, "want-card")
            if projects:
                for project in projects:
                    try:
                        proposals = project.find_element(By.XPATH, ".//span[contains(text(), 'Предложений')]")
                        price = project.find_element(By.CLASS_NAME, "wants-card__price").find_element(By.CLASS_NAME, "d-inline").text
                        if proposals and "0" in proposals.text[13]:
                            with open("projects.html", "a", encoding="utf-8") as file:
                                file.write(project.get_attribute('outerHTML') + "\n")
                            title_element = project.find_element(By.CLASS_NAME, "wants-card__header-title")
                            title = title_element.text.strip()
                            link_element = title_element.find_element(By.TAG_NAME, "a")
                            project_link = link_element.get_attribute("href")

                            print(f"Проект: {title}")
                            print(f"Ссылка: {project_link}")
                            print(f"Цена: {price}")
                            print("-" * 50)

                            write_to_file(f"Проект: {title}\nСсылка: {project_link}\nЦена: {price}\n" + "-" * 50)
                    except Exception as e:
                        continue

        # Парсим первую страницу
        parse_cards()

        i = 1
        while True:
            time.sleep(5)
            try:
                next_button = driver.find_element(By.CLASS_NAME, "pagination__arrow--next")
                next_button.click()
                i += 1
                print(f"Страница {i}")
                time.sleep(5)
                parse_cards()
            except Exception as e:
                print("Ошибка при переходе на следующую страницу")
                break
        print("Парсинг закончен")

    finally:
        driver.quit()

# Функция для отправки файла с результатами пользователю
async def send_parsed_results():
    if os.path.exists("projects.txt"):
        # Отправляем файл с результатами пользователю
        await bot.send_document(chat_id=USER_ID, document=FSInputFile("projects.txt"))
        await bot.send_document(chat_id=USER_ID, document=FSInputFile("projects.html"))
    else:
        await bot.send_message(chat_id=USER_ID, text="Файл с проектами не найден.")

# Функция для периодического запуска парсинга каждые 20 минут
async def periodic_parsing():
    while True:
        print("Запускаем парсинг...")
        parse_kwork()  # Запускаем парсинг
        await send_parsed_results()  # Отправляем результаты пользователю
        await asyncio.sleep(20 * 60)  # Ждем 20 минут перед следующим запуском

# Команда для старта процесса
@dp.message(Command("start"))
async def start_parsing(message: types.Message):
    await message.answer("Парсинг будет запускаться каждые 20 минут.")
    # Запуск периодического парсинга
    asyncio.create_task(periodic_parsing())

# Запуск бота
if __name__ == "__main__":
    dp.run_polling(bot)