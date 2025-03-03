import os
import json
import uuid
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiogram.types.web_app_info import WebAppInfo

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "7665197621:AAFWLa0ljKEelnsjbioIeyqXUHfP3X0JOkk"

# Путь к веб-приложению
WEBAPP_URL = "https://kdebugada.github.io/tg-mini-app/"  # URL вашего веб-приложения

# Информация о билетах
TICKET_TYPES = {
    "стандартный": {
        "name": "Стандартный билет",
        "description": "Базовый лотерейный билет",
        "price": 1,
        "photo_url": "./foto/loto_glav_menu.jpg"
    },
    "серебряный": {
        "name": "Серебряный билет",
        "description": "Серебряный лотерейный билет",
        "price": 10,
        "photo_url": "./foto/loto_glav_menu.jpg"
    },
    "золотой": {
        "name": "Золотой билет",
        "description": "Золотой лотерейный билет",
        "price": 50,
        "photo_url": "./foto/loto_glav_menu.jpg"
    },
    "платиновый": {
        "name": "Платиновый билет",
        "description": "Платиновый лотерейный билет",
        "price": 100,
        "photo_url": "./foto/loto_glav_menu.jpg"
    }
}

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Хранилище для данных пользователей
user_data = {}

# Обработчик команды /start
@dp.message_handler(Command("start"))
async def cmd_start(message: types.Message):
    """Отправляет приветственное сообщение и кнопку для запуска веб-приложения."""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Открыть лотерею", web_app=WebAppInfo(url=WEBAPP_URL)))
    
    await message.answer(
        "Привет! Я бот для лотереи. Нажмите кнопку ниже, чтобы открыть приложение:",
        reply_markup=keyboard
    )

# Обработчик команды /terms
@dp.message_handler(Command("terms"))
async def cmd_terms(message: types.Message):
    """Отправляет пользователю условия использования."""
    await message.answer(
        "Условия использования лотереи:\n\n"
        "1. Вы должны быть старше 18 лет.\n"
        "2. Все платежи осуществляются в Telegram Stars.\n"
        "3. Мы не несем ответственности за технические сбои.\n"
        "4. Выигрыши распределяются случайным образом.\n"
        "5. Администрация оставляет за собой право изменять правила."
    )

# Обработчик команды /support
@dp.message_handler(Command("support"))
async def cmd_support(message: types.Message):
    """Отправляет пользователю информацию о поддержке."""
    await message.answer(
        "Если у вас возникли вопросы или проблемы, пожалуйста, свяжитесь с нами:\n\n"
        "Email: support@example.com\n"
        "Telegram: @support_username"
    )

# Обработчик команды /paysupport
@dp.message_handler(Command("paysupport"))
async def cmd_paysupport(message: types.Message):
    """Обрабатывает запросы пользователей по вопросам оплаты."""
    await message.answer(
        "Если у вас возникли проблемы с оплатой, пожалуйста, опишите вашу проблему. "
        "Мы рассмотрим ваш запрос в течение 24 часов."
    )

# Обработчик команды /tickets
@dp.message_handler(Command("tickets"))
async def cmd_tickets(message: types.Message):
    """Отправляет пользователю информацию о доступных билетах."""
    ticket_message = "Доступные типы билетов:\n\n"
    
    for ticket_type, info in TICKET_TYPES.items():
        ticket_message += f"🎫 {info['name']} - {info['price']} Stars\n"
        ticket_message += f"   {info['description']}\n\n"
    
    await message.answer(ticket_message)

# Обработчик данных от веб-приложения
@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def web_app_data(message: types.Message):
    """Обрабатывает данные, полученные от веб-приложения."""
    try:
        logger.info(f"Получено сообщение от веб-приложения: {message}")
        
        # Получаем данные от веб-приложения
        data = json.loads(message.web_app_data.data)
        logger.info(f"Получены данные от веб-приложения: {data}")
        
        if data.get('action') == 'open_number_selection':
            # Обработка запроса на открытие страницы выбора номеров
            price = int(data.get('price', 1))
            ticket_type = data.get('ticketType', 'Стандартный')
            
            # Создаем URL для веб-приложения с выбором номеров
            number_selection_url = f"{WEBAPP_URL}number_selection.html?type={ticket_type}&price={price}"
            
            # Отправляем пользователю кнопку для открытия страницы выбора номеров
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton(
                f"Выбрать номера для {ticket_type} билета", 
                web_app=WebAppInfo(url=number_selection_url)
            ))
            
            await message.answer(
                f"Выберите 8 номеров для вашего {ticket_type} билета (цена: {price} Stars):",
                reply_markup=keyboard
            )
        elif data.get('action') == 'create_stars_invoice':
            # Проверяем, есть ли информация о билетах с выбранными номерами
            if 'tickets' in data:
                # Обработка нескольких билетов с выбранными номерами
                tickets = data.get('tickets', [])
                total_price = data.get('totalPrice', 0)
                
                if not tickets:
                    logger.warning("Получен пустой список билетов")
                    await message.answer("Ошибка: не выбраны билеты")
                    return
                
                # Формируем описание для счета
                ticket_descriptions = []
                for i, ticket in enumerate(tickets):
                    ticket_type = ticket.get('type', 'Стандартный')
                    numbers = ticket.get('numbers', [])
                    numbers_str = ', '.join(map(str, numbers))
                    ticket_descriptions.append(f"{i+1}. {ticket_type} билет: {numbers_str}")
                
                description = "Покупка лотерейных билетов:\n" + "\n".join(ticket_descriptions)
                
                # Конвертируем цену в минимальные единицы
                price_in_min_units = total_price * 100  # 1 Stars = 100 (в минимальных единицах)
                
                logger.info(f"Создаем счет на сумму {price_in_min_units} XTR для {len(tickets)} билетов")
                
                # Создаем счет через Bot API
                try:
                    invoice_payload = f"lottery_tickets_{uuid.uuid4()}"
                    
                    # Сохраняем информацию о билетах в данных пользователя
                    if message.from_user.id not in user_data:
                        user_data[message.from_user.id] = {}
                    
                    if 'pending_tickets' not in user_data[message.from_user.id]:
                        user_data[message.from_user.id]['pending_tickets'] = {}
                    
                    user_data[message.from_user.id]['pending_tickets'][invoice_payload] = {
                        'tickets': tickets,
                        'total_price': total_price
                    }
                    
                    await bot.send_invoice(
                        chat_id=message.chat.id,
                        title=f"Лотерейные билеты ({len(tickets)} шт.)",
                        description=description,
                        payload=invoice_payload,
                        provider_token="",  # Для цифровых товаров можно оставить пустым
                        currency="XTR",  # XTR - код валюты для Telegram Stars
                        prices=[
                            LabeledPrice(
                                label=f"Лотерейные билеты ({len(tickets)} шт.)", 
                                amount=price_in_min_units
                            )
                        ],
                        start_parameter="lottery_tickets",  # Для deep linking
                        photo_url="./foto/loto_glav_menu.jpg",  # URL изображения товара
                        photo_width=512,
                        photo_height=512,
                        need_name=False,
                        need_phone_number=False,
                        need_email=False,
                        need_shipping_address=False,
                        is_flexible=False
                    )
                    
                    logger.info(f"Создан счет с payload: {invoice_payload}")
                except Exception as e:
                    logger.error(f"Ошибка при создании счета: {e}")
                    await message.answer(f"Ошибка при создании счета: {str(e)}")
            else:
                # Старый формат для обратной совместимости
                # Получаем информацию о билете
                price = int(data.get('price', 1))
                ticket_type = data.get('ticketType', 'Стандартный').lower()
                
                # Проверяем, существует ли такой тип билета
                if ticket_type not in TICKET_TYPES:
                    logger.warning(f"Неизвестный тип билета: {ticket_type}")
                    await message.answer(f"Ошибка: неизвестный тип билета {ticket_type}")
                    return
                
                # Получаем информацию о билете
                ticket_info = TICKET_TYPES[ticket_type]
                
                # Проверяем, соответствует ли цена
                if price != ticket_info['price']:
                    logger.warning(f"Несоответствие цены: ожидается {ticket_info['price']}, получено {price}")
                    price = ticket_info['price']
                
                # Конвертируем цену в минимальные единицы
                price_in_min_units = price * 100  # 1 Stars = 100 (в минимальных единицах)
                
                logger.info(f"Создаем счет на сумму {price_in_min_units} XTR для билета типа {ticket_type}")
                
                # Создаем счет через Bot API
                try:
                    invoice_payload = f"lottery_ticket_{ticket_type}_{uuid.uuid4()}"
                    
                    await bot.send_invoice(
                        chat_id=message.chat.id,
                        title=ticket_info['name'],
                        description=ticket_info['description'],
                        payload=invoice_payload,
                        provider_token="",  # Для цифровых товаров можно оставить пустым
                        currency="XTR",  # XTR - код валюты для Telegram Stars
                        prices=[
                            LabeledPrice(
                                label=ticket_info['name'], 
                                amount=price_in_min_units
                            )
                        ],
                        start_parameter=f"lottery_ticket_{ticket_type}",  # Для deep linking
                        photo_url=ticket_info['photo_url'],  # URL изображения товара
                        photo_width=512,
                        photo_height=512,
                        need_name=False,
                        need_phone_number=False,
                        need_email=False,
                        need_shipping_address=False,
                        is_flexible=False
                    )
                    
                    logger.info(f"Создан счет с payload: {invoice_payload}")
                except Exception as e:
                    logger.error(f"Ошибка при создании счета: {e}")
                    await message.answer(f"Ошибка при создании счета: {str(e)}")
        else:
            logger.warning(f"Неизвестное действие: {data.get('action')}")
            await message.answer(f"Неизвестное действие: {data.get('action')}")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке данных от веб-приложения: {e}")
        await message.answer(f"Произошла ошибка: {str(e)}")

# Обработчик pre-checkout запросов
@dp.pre_checkout_query_handler()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Обрабатывает pre-checkout запросы."""
    # Здесь можно проверить наличие товара, валидность заказа и т.д.
    # Если все в порядке, подтверждаем заказ
    try:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        logger.info(f"Pre-checkout подтвержден: {pre_checkout_query.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке pre-checkout: {e}")
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id, 
            ok=False, 
            error_message="Произошла ошибка при обработке заказа. Пожалуйста, попробуйте позже."
        )

# Обработчик успешных платежей
@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    """Обрабатывает успешные платежи."""
    payment = message.successful_payment
    
    # Проверяем, есть ли информация о билетах с выбранными номерами
    user_id = message.from_user.id
    pending_tickets = None
    
    if user_id in user_data and 'pending_tickets' in user_data[user_id]:
        pending_tickets = user_data[user_id]['pending_tickets'].get(payment.invoice_payload)
    
    if pending_tickets:
        # Обработка платежа для билетов с выбранными номерами
        tickets = pending_tickets.get('tickets', [])
        
        # Формируем сообщение о покупке
        ticket_descriptions = []
        for i, ticket in enumerate(tickets):
            ticket_type = ticket.get('type', 'Стандартный')
            numbers = ticket.get('numbers', [])
            numbers_str = ', '.join(map(str, numbers))
            ticket_descriptions.append(f"{i+1}. {ticket_type} билет: {numbers_str}")
        
        # Сохраняем информацию о платеже
        payment_info = {
            "telegram_payment_charge_id": payment.telegram_payment_charge_id,
            "provider_payment_charge_id": payment.provider_payment_charge_id,
            "total_amount": payment.total_amount,
            "currency": payment.currency,
            "invoice_payload": payment.invoice_payload,
            "tickets": tickets
        }
        
        logger.info(f"Успешный платеж за билеты с номерами: {payment_info}")
        
        # Отправляем пользователю подтверждение
        await message.answer(
            f"Спасибо за покупку! Ваши лотерейные билеты ({len(tickets)} шт.) успешно оплачены.\n\n"
            f"Выбранные номера:\n" + "\n".join(ticket_descriptions) + "\n\n"
            "Результаты будут объявлены в ближайшее время."
        )
        
        # Удаляем информацию о билетах из данных пользователя
        if payment.invoice_payload in user_data[user_id]['pending_tickets']:
            del user_data[user_id]['pending_tickets'][payment.invoice_payload]
    else:
        # Старый формат для обратной совместимости
        # Извлекаем информацию о типе билета из payload
        payload = payment.invoice_payload
        ticket_type = "стандартный"  # По умолчанию
        
        # Пытаемся извлечь тип билета из payload
        if "_" in payload:
            parts = payload.split("_")
            if len(parts) >= 3 and parts[0] == "lottery" and parts[1] == "ticket":
                ticket_type = parts[2]
        
        # Получаем информацию о билете
        ticket_info = TICKET_TYPES.get(ticket_type, TICKET_TYPES["стандартный"])
        
        # Сохраняем информацию о платеже
        payment_info = {
            "telegram_payment_charge_id": payment.telegram_payment_charge_id,
            "provider_payment_charge_id": payment.provider_payment_charge_id,
            "total_amount": payment.total_amount,
            "currency": payment.currency,
            "invoice_payload": payment.invoice_payload,
            "ticket_type": ticket_type
        }
        
        logger.info(f"Успешный платеж: {payment_info}")
        
        # Отправляем пользователю подтверждение
        await message.answer(
            f"Спасибо за покупку! Ваш {ticket_info['name']} успешно оплачен.\n"
            "Результаты будут объявлены в ближайшее время."
        )
    
    # Здесь должен быть код для выдачи цифрового товара пользователю
    # Например, генерация уникального кода билета, запись в базу данных и т.д.

# Обработчик ошибок
@dp.errors_handler()
async def error_handler(update, exception):
    """Логирует ошибки, вызванные обновлениями."""
    logger.error(f"Ошибка при обработке обновления {update}: {exception}")
    return True

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)