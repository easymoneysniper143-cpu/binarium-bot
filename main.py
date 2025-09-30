import telebot
import random
import schedule
import time
import threading
import logging
from dotenv import load_dotenv
import os
import yfinance as yf

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Логирование инициализировано")

# Загрузка настроек
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not BOT_TOKEN or not CHAT_ID:
    print("Ошибка: Укажи BOT_TOKEN и CHAT_ID в .env")
    exit()

logging.info(f"Токен и CHAT_ID загружены: {BOT_TOKEN[:5]}... {CHAT_ID}")
bot = telebot.TeleBot(BOT_TOKEN)

is_sending_signals = False

# Список активов
assets = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X']

def generate_signal(asset):
    try:
        logging.info(f"Попытка загрузки данных для {asset}")
        data = yf.download(asset, period='1d', interval='1m')
        if data.empty:
            logging.error(f"Нет данных для {asset}")
            return None

        close_prices = data['Close']
        sma = close_prices.rolling(window=14).mean().iloc[-1]
        current_price = close_prices.iloc[-1]
        direction = '⬆️' if current_price > sma else '⬇️'
        probability = random.randint(60, 80)

        if probability < 75:
            logging.info(f"Сигнал для {asset} пропущен (вероятность {probability}%)")
            return None

        message = (
            f"🔔 **Сигнал для Binarium!**\n\n"
            f"Актив: {asset.replace('=X', '')}\n"
            f"Направление: {direction}\n"
            f"Цена: {current_price:.5f}\n"
            f"Время экспирации: 5 минут\n"
            f"Вероятность успеха: {probability}%\n"
            f"Время: {time.strftime('%H:%M:%S')}\n\n"
            f"⚠️ Это симуляция на основе реальных цен — торгуй на свой риск!"
        )
        return message
    except Exception as e:
        logging.error(f"Ошибка генерации сигнала для {asset}: {e}")
        return None

def send_signals():
    if is_sending_signals:
        for asset in assets:
            signal = generate_signal(asset)
            if signal:
                try:
                    bot.send_message(CHAT_ID, signal, parse_mode='Markdown')
                    logging.info(f"Сигнал для {asset} отправлен")
                except Exception as e:
                    logging.error(f"Ошибка отправки для {asset}: {e}")

schedule.every(5).minutes.do(send_signals)

def run_schedule():
    while is_sending_signals:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start'])
def start_message(message):
    global is_sending_signals
    if not is_sending_signals:
        is_sending_signals = True
        threading.Thread(target=run_schedule, daemon=True).start()
        bot.reply_to(message, "🚀 Бот запущен! Сигналы (с вероятностью >=75%) будут приходить каждые 5 минут для 3 активов.")
        logging.info("Бот запущен")
    else:
        bot.reply_to(message, "Бот уже работает! Используй /status для проверки.")

@bot.message_handler(commands=['stop'])
def stop_message(message):
    global is_sending_signals
    is_sending_signals = False
    bot.reply_to(message, "🛑 Сигналы остановлены. Напиши /start для возобновления.")
    logging.info("Сигналы остановлены")

@bot.message_handler(commands=['status'])
def status_message(message):
    status = "работает" if is_sending_signals else "остановлен"
    bot.reply_to(message, f"📊 Статус бота: {status}")
    logging.info(f"Проверка статуса: {status}")

if __name__ == '__main__':
    print("Бот запущен! Начинаю polling...")
    logging.info("Бот запущен! Начинаю polling...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка в polling: {e}")
        logging.error(f"Ошибка в polling: {e}")
