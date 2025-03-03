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
            # Создаем счет для оплаты Stars
            price = int(data.get('price', 1)) * 100  # 1 Stars = 100 (в минимальных единицах)
            
            logger.info(f"Создаем счет на сумму {price} XTR")
            
            # Создаем счет через Bot API
            try:
                invoice = await context.bot.send_invoice(
                    chat_id=update.effective_chat.id,
                    title="Лотерейный билет",
                    description="Покупка лотерейного билета для участия в розыгрыше",
                    payload=f"lottery_ticket_{uuid.uuid4()}",
                    provider_token="",  # Для цифровых товаров можно оставить пустым
                    currency="XTR",  # XTR - код валюты для Telegram Stars
                    prices=[LabeledPrice(label="Лотерейный билет", amount=price)],
                    start_parameter="lottery_ticket",  # Для deep linking
                    photo_url="https://example.com/lottery_ticket.jpg",  # URL изображения товара
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
    
    # Сохраняем информацию о платеже
    payment_info = {
        "telegram_payment_charge_id": payment.telegram_payment_charge_id,
        "provider_payment_charge_id": payment.provider_payment_charge_id,
        "total_amount": payment.total_amount,
        "currency": payment.currency,
        "invoice_payload": payment.invoice_payload
    }
    
    logger.info(f"Успешный платеж: {payment_info}")
    
    # Отправляем пользователю подтверждение
    await update.message.reply_text(
        "Спасибо за покупку! Ваш лотерейный билет успешно оплачен.\n"
        "Вы участвуете в розыгрыше призов. Результаты будут объявлены в ближайшее время."
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
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()