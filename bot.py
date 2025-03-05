import os
import json
import uuid
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command
from aiogram.types.web_app_info import WebAppInfo

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "7665197621:AAFWLa0ljKEelnsjbioIeyqXUHfP3X0JOkk"

# ID администратора
ADMIN_ID = 1621625897

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
dp = Dispatcher()

# Хранилище для данных пользователей
user_data = {}

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обрабатывает команду /start."""
    # Создаем клавиатуру с кнопкой для открытия мини-приложения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🎮 Открыть лотерею",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]])
    
    await message.answer(
        "Добро пожаловать в лотерею! Нажмите на кнопку ниже, чтобы открыть мини-приложение.",
        reply_markup=keyboard
    )

# Обработчик команды /terms
@dp.message(Command("terms"))
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
@dp.message(Command("support"))
async def cmd_support(message: types.Message):
    """Отправляет пользователю информацию о поддержке."""
    await message.answer(
        "Если у вас возникли вопросы или проблемы, пожалуйста, свяжитесь с нами:\n\n"
        "Email: support@example.com\n"
        "Telegram: @support_username"
    )

# Обработчик команды /paysupport
@dp.message(Command("paysupport"))
async def cmd_paysupport(message: types.Message):
    """Обрабатывает запросы пользователей по вопросам оплаты."""
    await message.answer(
        "Если у вас возникли проблемы с оплатой, пожалуйста, опишите вашу проблему. "
        "Мы рассмотрим ваш запрос в течение 24 часов."
    )

# Обработчик команды /tickets
@dp.message(Command("tickets"))
async def cmd_tickets(message: types.Message):
    """Отправляет пользователю информацию о доступных билетах."""
    ticket_message = "Доступные типы билетов:\n\n"
    
    for ticket_type, info in TICKET_TYPES.items():
        ticket_message += f"🎫 {info['name']} - {info['price']} Stars\n"
        ticket_message += f"   {info['description']}\n\n"
    
    await message.answer(ticket_message)

# Обработчик веб-приложения
@dp.message(F.web_app_data)
async def web_app_data(message: types.Message):
    """Обрабатывает данные, полученные от веб-приложения."""
    try:
        logger.info(f"Получены данные от веб-приложения: {message.web_app_data.data}")
        data = json.loads(message.web_app_data.data)
        user_id = message.from_user.id
        
        if data.get('action') == 'create_invoice':
            # Обрабатываем создание счета
            tickets = data.get('tickets', [])
            ticket_type = data.get('ticketType', '').lower()
            total_price = data.get('totalPrice', 0)
            
            if not tickets:
                await message.answer("Не выбраны билеты.")
                return
            
            if ticket_type not in TICKET_TYPES:
                await message.answer("Неизвестный тип билета.")
                return
            
            ticket_info = TICKET_TYPES[ticket_type]
            price = total_price
            
            # Проверяем соответствие цены
            expected_total = ticket_info['price'] * len(tickets)
            if price != expected_total:
                logger.warning(f"Несоответствие цены: ожидается {expected_total}, получено {price}")
                price = expected_total
            
            # Конвертируем цену в минимальные единицы
            price_in_min_units = price * 100  # 1 Stars = 100 (в минимальных единицах)
            
            logger.info(f"Создаем счет на сумму {price_in_min_units} XTR для билетов типа {ticket_type}")
            
            # Сохраняем информацию о выбранных билетах
            if user_id not in user_data:
                user_data[user_id] = {}
            
            if 'pending_tickets' not in user_data[user_id]:
                user_data[user_id]['pending_tickets'] = {}
            
            # Создаем уникальный идентификатор для этого набора билетов
            invoice_payload = f"lottery_ticket_{ticket_type}_{uuid.uuid4()}"
            user_data[user_id]['pending_tickets'][invoice_payload] = tickets
            
            # Создаем счет через Stars Payment API
            try:
                logger.info(f"Отправляем запрос на создание счета: {ticket_info}")
                
                # Проверка URL фото
                photo_url = ticket_info.get('photo_url', "")
                # Если ссылка относительная, делаем ее абсолютной
                if photo_url and not photo_url.startswith(('http://', 'https://')):
                    photo_url = f"{WEBAPP_URL}{photo_url.lstrip('./')}"
                    photo_url = "https://kdebugada.github.io/tg-mini-app/foto/loto_glav_menu.jpg"  # Гарантированно работающий URL
                
                logger.info(f"Используем URL фото: {photo_url}")
                
                # Отправляем сообщение-уведомление о формировании счета
                await message.answer(f"Формирую счет на оплату {len(tickets)} билетов типа '{ticket_type}' за {price} Stars...")
                
                # Прямое уведомление для отладки
                await message.answer(f"DEBUG INFO: Стоимость: {price} Stars, Тип: {ticket_type}, Количество: {len(tickets)}")
                
                # Проверяем токен бота
                if not TOKEN:
                    logger.error("Токен бота не определен")
                    await message.answer("Ошибка: Токен бота не определен. Обратитесь к администратору.")
                    return
                
                # Создаем счет
                try:
                    # Проверяем правильность валюты и суммы
                    if price_in_min_units <= 0:
                        logger.error(f"Неверная сумма для счета: {price_in_min_units}")
                        await message.answer("Ошибка: Неверная сумма для счета. Попробуйте выбрать билеты заново.")
                        return
                    
                    # Создаем счет с минимальными аргументами
                    invoice_message = await bot.send_invoice(
                        chat_id=message.chat.id,
                        title=f"{ticket_info['name']} ({len(tickets)} шт.)",
                        description=f"Лотерейные билеты: {ticket_info['description']}",
                        payload=invoice_payload,
                        provider_token="",  # Для Stars можно оставить пустым
                        currency="XTR",
                        prices=[LabeledPrice(label=f"{ticket_info['name']} x{len(tickets)}", amount=int(price_in_min_units))],
                        protect_content=True
                    )
                    
                    logger.info(f"Создан счет с payload: {invoice_payload}, message_id: {invoice_message.message_id}")
                    
                    # Отправляем пользователю дополнительную информацию о выбранных билетах
                    selected_numbers_message = data.get('selectedNumbersMessage', '')
                    if selected_numbers_message:
                        await message.answer(f"Ваш заказ:\n\n{selected_numbers_message}\n\nПожалуйста, нажмите на кнопку 'Оплатить' в счете выше.")
                    
                    # Отправка уведомления для отладки
                    await message.answer("Счет создан! Если вы не видите кнопку 'Оплатить', обновите чат (потяните экран вниз).")
                
                except Exception as send_invoice_error:
                    logger.error(f"Ошибка при отправке invoice: {send_invoice_error}", exc_info=True)
                    await message.answer(f"Ошибка при создании платежа: {str(send_invoice_error)}")
                    await message.answer("Пожалуйста, попробуйте еще раз или обратитесь к поддержке.")
                
            except Exception as e:
                logger.error(f"Общая ошибка при создании счета Stars: {e}", exc_info=True)
                await message.answer(f"Ошибка при создании счета: {str(e)}\n\nПожалуйста, сообщите об этой ошибке администратору.")
                # Отправляем уведомление администратору
                try:
                    await bot.send_message(ADMIN_ID, f"❌ Ошибка при создании счета:\n\nПользователь: {message.from_user.full_name} (@{message.from_user.username})\nОшибка: {str(e)}")
                except Exception as admin_msg_error:
                    logger.error(f"Не удалось отправить уведомление администратору: {admin_msg_error}")
                
        else:
            logger.warning(f"Неизвестное действие: {data.get('action')}")
            await message.answer(f"Неизвестное действие: {data.get('action')}")
    
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON")
        await message.answer("Ошибка декодирования данных. Пожалуйста, попробуйте еще раз.")
    except Exception as e:
        logger.error(f"Ошибка при обработке данных от веб-приложения: {e}")
        await message.answer(f"Произошла ошибка: {str(e)}")

# Обработчик pre-checkout запросов
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Обрабатывает pre-checkout запросы для платежей Stars."""
    try:
        logger.info(f"Получен pre-checkout запрос: {pre_checkout_query}")
        
        # Проверяем, есть ли у пользователя ожидающие билеты
        user_id = pre_checkout_query.from_user.id
        payload = pre_checkout_query.invoice_payload
        
        if (user_id in user_data and 
            'pending_tickets' in user_data[user_id] and
            payload in user_data[user_id]['pending_tickets']):
            
            # Если всё в порядке, подтверждаем платеж
            await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
            logger.info(f"Pre-checkout подтвержден: {pre_checkout_query.id}")
        else:
            # Если что-то не так, отклоняем платеж
            logger.warning(f"Неизвестный payload: {payload} для пользователя {user_id}")
            await bot.answer_pre_checkout_query(
                pre_checkout_query.id, 
                ok=False, 
                error_message="Ошибка проверки платежа. Пожалуйста, попробуйте заново."
            )
    except Exception as e:
        logger.error(f"Ошибка при обработке pre-checkout: {e}")
        await bot.answer_pre_checkout_query(
            pre_checkout_query.id, 
            ok=False, 
            error_message="Произошла ошибка при обработке заказа. Пожалуйста, попробуйте позже."
        )

# Обработчик успешных платежей
@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    """Обрабатывает успешные платежи Stars."""
    try:
        payment = message.successful_payment
        logger.info(f"Получено подтверждение успешного платежа: {payment}")
        
        # Получаем данные о платеже
        payload = payment.invoice_payload
        user_id = message.from_user.id
        total_amount = payment.total_amount / 100  # Конвертируем обратно из минимальных единиц
        
        # Проверяем, есть ли информация о билетах с выбранными номерами
        pending_tickets = None
        if user_id in user_data and 'pending_tickets' in user_data[user_id]:
            pending_tickets = user_data[user_id]['pending_tickets'].get(payload)
        
        if pending_tickets:
            # Формируем сообщение с подтверждением покупки
            confirmation_message = f"✅ Платеж успешно выполнен!\n\n"
            confirmation_message += f"💰 Сумма: {total_amount} Stars\n"
            confirmation_message += f"🎫 Тип билета: {payload.split('_')[2].capitalize()}\n\n"
            
            # Добавляем информацию о выбранных номерах
            confirmation_message += "Ваши выбранные номера:\n\n"
            for i, ticket in enumerate(pending_tickets):
                confirmation_message += f"Билет {i + 1}: {', '.join(map(str, sorted(ticket['numbers'])))}\n"
            
            # Отправляем подтверждение пользователю
            await message.answer(confirmation_message)
            
            # Отправляем уведомление администратору
            admin_message = f"💵 НОВАЯ ПОКУПКА STARS!\n\n"
            admin_message += f"👤 Пользователь: {message.from_user.full_name} (@{message.from_user.username})\n"
            admin_message += f"🆔 ID: {user_id}\n"
            admin_message += f"💰 Сумма: {total_amount} Stars\n"
            admin_message += f"🎫 Тип билета: {payload.split('_')[2].capitalize()}\n\n"
            
            # Добавляем информацию о выбранных номерах
            admin_message += "Выбранные номера:\n\n"
            for i, ticket in enumerate(pending_tickets):
                admin_message += f"Билет {i + 1}: {', '.join(map(str, sorted(ticket['numbers'])))}\n"
            
            try:
                await bot.send_message(ADMIN_ID, admin_message)
                logger.info(f"Уведомление о покупке отправлено администратору")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления администратору: {e}")
            
            # Удаляем информацию о билетах из ожидающих
            if payload in user_data[user_id]['pending_tickets']:
                del user_data[user_id]['pending_tickets'][payload]
                
        else:
            # Если информации о билетах нет, отправляем общее подтверждение
            await message.answer(
                f"✅ Платеж на сумму {total_amount} Stars успешно выполнен!\n\n"
                f"Спасибо за вашу покупку!"
            )
            
            # Также отправляем уведомление администратору
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"💵 НОВАЯ ПОКУПКА STARS!\n\n"
                    f"👤 Пользователь: {message.from_user.full_name} (@{message.from_user.username})\n"
                    f"🆔 ID: {user_id}\n"
                    f"💰 Сумма: {total_amount} Stars\n"
                    f"🧾 Payload: {payload}"
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления администратору: {e}")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке успешного платежа: {e}")
        await message.answer("Произошла ошибка при обработке платежа. Пожалуйста, свяжитесь с поддержкой.")

# Обработчик ошибок
@dp.error()
async def error_handler(update, exception):
    """Логирует ошибки, вызванные обновлениями."""
    logger.error(f"Ошибка при обработке обновления {update}: {exception}")
    return True

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())