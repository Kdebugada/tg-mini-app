import os
import json
import uuid
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, LabeledPrice
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, PreCheckoutQueryHandler

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
        "description": "Базовый лотерейный билет с обычным шансом на выигрыш",
        "price": 1,
        "photo_url": "https://example.com/standard_ticket.jpg"
    },
    "серебряный": {
        "name": "Серебряный билет",
        "description": "Лотерейный билет с повышенным шансом на выигрыш",
        "price": 10,
        "photo_url": "https://example.com/silver_ticket.jpg"
    },
    "золотой": {
        "name": "Золотой билет",
        "description": "Лотерейный билет с высоким шансом на выигрыш",
        "price": 50,
        "photo_url": "https://example.com/gold_ticket.jpg"
    },
    "платиновый": {
        "name": "Платиновый билет",
        "description": "Лотерейный билет с максимальным шансом на выигрыш",
        "price": 100,
        "photo_url": "https://example.com/platinum_ticket.jpg"
    }
}

# Обработчик команды /start
async def start(update: Update, context: CallbackContext) -> None:
    """Отправляет приветственное сообщение и кнопку для запуска веб-приложения."""
    keyboard = [
        [InlineKeyboardButton("Открыть лотерею", web_app=WebAppInfo(url=WEBAPP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Привет! Я бот для лотереи. Нажмите кнопку ниже, чтобы открыть приложение:",
        reply_markup=reply_markup
    )

# Обработчик команды /terms
async def terms(update: Update, context: CallbackContext) -> None:
    """Отправляет пользователю условия использования."""
    await update.message.reply_text(
        "Условия использования лотереи:\n\n"
        "1. Вы должны быть старше 18 лет.\n"
        "2. Все платежи осуществляются в Telegram Stars.\n"
        "3. Мы не несем ответственности за технические сбои.\n"
        "4. Выигрыши распределяются случайным образом.\n"
        "5. Администрация оставляет за собой право изменять правила."
    )

# Обработчик команды /support
async def support(update: Update, context: CallbackContext) -> None:
    """Отправляет пользователю информацию о поддержке."""
    await update.message.reply_text(
        "Если у вас возникли вопросы или проблемы, пожалуйста, свяжитесь с нами:\n\n"
        "Email: support@example.com\n"
        "Telegram: @support_username"
    )

# Обработчик команды /paysupport
async def paysupport(update: Update, context: CallbackContext) -> None:
    """Обрабатывает запросы пользователей по вопросам оплаты."""
    await update.message.reply_text(
        "Если у вас возникли проблемы с оплатой, пожалуйста, опишите вашу проблему. "
        "Мы рассмотрим ваш запрос в течение 24 часов."
    )

# Обработчик команды /tickets
async def tickets(update: Update, context: CallbackContext) -> None:
    """Отправляет пользователю информацию о доступных билетах."""
    message = "Доступные типы билетов:\n\n"
    
    for ticket_type, info in TICKET_TYPES.items():
        message += f"🎫 {info['name']} - {info['price']} Stars\n"
        message += f"   {info['description']}\n\n"
    
    await update.message.reply_text(message)

# Обработчик данных от веб-приложения
async def web_app_data(update: Update, context: CallbackContext) -> None:
    """Обрабатывает данные, полученные от веб-приложения."""
    try:
        logger.info(f"Получено сообщение от веб-приложения: {update.message}")
        
        # Проверяем, есть ли данные веб-приложения
        if not hasattr(update.message, 'web_app_data'):
            logger.error("Сообщение не содержит данных веб-приложения")
            await update.message.reply_text("Ошибка: данные веб-приложения не получены")
            return
        
        # Получаем данные от веб-приложения
        data = json.loads(update.message.web_app_data.data)
        logger.info(f"Получены данные от веб-приложения: {data}")
        
        if data.get('action') == 'create_stars_invoice':
            # Получаем информацию о билете
            price = int(data.get('price', 1))
            ticket_type = data.get('ticketType', 'Стандартный').lower()
            
            # Проверяем, существует ли такой тип билета
            if ticket_type not in TICKET_TYPES:
                logger.warning(f"Неизвестный тип билета: {ticket_type}")
                await update.message.reply_text(f"Ошибка: неизвестный тип билета {ticket_type}")
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
                invoice = await context.bot.send_invoice(
                    chat_id=update.effective_chat.id,
                    title=ticket_info['name'],
                    description=ticket_info['description'],
                    payload=f"lottery_ticket_{ticket_type}_{uuid.uuid4()}",
                    provider_token="",  # Для цифровых товаров можно оставить пустым
                    currency="XTR",  # XTR - код валюты для Telegram Stars
                    prices=[LabeledPrice(label=ticket_info['name'], amount=price_in_min_units)],
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
                
                logger.info(f"Создан счет: {invoice}")
            except Exception as e:
                logger.error(f"Ошибка при создании счета: {e}")
                await update.message.reply_text(f"Ошибка при создании счета: {str(e)}")
        else:
            logger.warning(f"Неизвестное действие: {data.get('action')}")
            await update.message.reply_text(f"Неизвестное действие: {data.get('action')}")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке данных от веб-приложения: {e}")
        await update.message.reply_text(f"Произошла ошибка: {str(e)}")

# Обработчик pre-checkout запросов
async def pre_checkout_handler(update: Update, context: CallbackContext) -> None:
    """Обрабатывает pre-checkout запросы."""
    query = update.pre_checkout_query
    
    # Здесь можно проверить наличие товара, валидность заказа и т.д.
    # Если все в порядке, подтверждаем заказ
    try:
        await query.answer(ok=True)
        logger.info(f"Pre-checkout подтвержден: {query.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке pre-checkout: {e}")
        await query.answer(ok=False, error_message="Произошла ошибка при обработке заказа. Пожалуйста, попробуйте позже.")

# Обработчик успешных платежей
async def successful_payment(update: Update, context: CallbackContext) -> None:
    """Обрабатывает успешные платежи."""
    payment = update.message.successful_payment
    
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
    await update.message.reply_text(
        f"Спасибо за покупку! Ваш {ticket_info['name']} успешно оплачен.\n"
        f"Вы участвуете в розыгрыше призов с {'повышенным' if ticket_type != 'стандартный' else 'обычным'} шансом на выигрыш.\n"
        "Результаты будут объявлены в ближайшее время."
    )
    
    # Здесь должен быть код для выдачи цифрового товара пользователю
    # Например, генерация уникального кода билета, запись в базу данных и т.д.

# Обработчик ошибок
async def error_handler(update: Update, context: CallbackContext) -> None:
    """Логирует ошибки, вызванные обновлениями."""
    logger.error(f"Ошибка при обработке обновления {update}: {context.error}")

def main() -> None:
    """Запускает бота."""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("terms", terms))
    application.add_handler(CommandHandler("support", support))
    application.add_handler(CommandHandler("paysupport", paysupport))
    application.add_handler(CommandHandler("tickets", tickets))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()