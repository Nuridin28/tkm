"""
Telegram Bot for Help Desk
"""
import logging
import re
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
from config import settings
from models import UserSession, ContactInfo, UserType, TicketRequest
from api_client import APIClient

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Conversation states
(
    WAITING_FOR_PHONE,
    WAITING_FOR_EMAIL,
    WAITING_FOR_NAME,
    WAITING_FOR_USER_TYPE,
    WAITING_FOR_COMPANY_INFO,
    WAITING_FOR_MESSAGE
) = range(6)

# Storage for user sessions
user_sessions: Dict[int, UserSession] = {}
api_client = APIClient()


def get_user_session(user_id: int, chat_id: int, username: Optional[str] = None) -> UserSession:
    """Get or create user session"""
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession(
            user_id=user_id,
            chat_id=chat_id,
            username=username
        )
    return user_sessions[user_id]


def validate_phone(phone: str) -> bool:
    """Validate phone number"""
    # Простая валидация - можно улучшить
    phone_clean = re.sub(r'[^\d+]', '', phone)
    return len(phone_clean) >= 10


def validate_email(email: str) -> bool:
    """Validate email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - просто отвечает привет"""
    try:
        await update.message.reply_text("👋 Привет! Чем могу помочь?")
    except Exception as e:
        logger.error(f"Error in start: {e}", exc_info=True)


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle contact information"""
    user = update.effective_user
    session = get_user_session(user.id, update.effective_chat.id, user.username)
    
    contact = update.message.contact
    if contact:
        phone = contact.phone_number
        # Если есть имя в контакте, используем его
        if contact.first_name:
            if not session.contact_info:
                session.contact_info = ContactInfo(
                    phone=phone,
                    full_name=contact.first_name + (f" {contact.last_name}" if contact.last_name else ""),
                    user_type=UserType.INDIVIDUAL
                )
            else:
                session.contact_info.phone = phone
                if not session.contact_info.full_name:
                    session.contact_info.full_name = contact.first_name + (f" {contact.last_name}" if contact.last_name else "")
    else:
        phone = update.message.text.strip()
    
    if not validate_phone(phone):
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте корректный номер телефона.\n"
            "Формат: +7XXXXXXXXXX или 8XXXXXXXXXX\n\n"
            "Или используйте кнопку '📱 Отправить мой контакт'"
        )
        return WAITING_FOR_PHONE
    
    if not session.contact_info:
        session.contact_info = ContactInfo(phone=phone, full_name="", user_type=UserType.INDIVIDUAL)
    else:
        session.contact_info.phone = phone
    
    session.waiting_for = "email"
    
    # Убираем клавиатуру
    remove_keyboard = ReplyKeyboardMarkup([[]], resize_keyboard=True)
    
    await update.message.reply_text(
        "✅ Номер телефона сохранен!\n\n"
        "📧 Теперь отправьте ваш email (или напишите 'пропустить', если не хотите указывать):",
        reply_markup=remove_keyboard
    )
    
    return WAITING_FOR_EMAIL


async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle email"""
    user = update.effective_user
    session = get_user_session(user.id, update.effective_chat.id, user.username)
    
    email_text = update.message.text.strip().lower()
    
    if email_text in ['пропустить', 'skip', 'нет', 'no']:
        email = None
    elif validate_email(email_text):
        email = email_text
    else:
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте корректный email адрес или напишите 'пропустить'"
        )
        return WAITING_FOR_EMAIL
    
    if session.contact_info:
        session.contact_info.email = email
    
    session.waiting_for = "name"
    
    await update.message.reply_text(
        "✅ Email сохранен!\n\n"
        "👤 Теперь отправьте ваше полное имя:"
    )
    
    return WAITING_FOR_NAME


async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle full name"""
    user = update.effective_user
    session = get_user_session(user.id, update.effective_chat.id, user.username)
    
    name = update.message.text.strip()
    
    if len(name) < 2:
        await update.message.reply_text("❌ Пожалуйста, отправьте ваше полное имя (минимум 2 символа)")
        return WAITING_FOR_NAME
    
    if session.contact_info:
        session.contact_info.full_name = name
    
    session.waiting_for = "type"
    
    # Спрашиваем тип лица
    keyboard = [
        [
            InlineKeyboardButton("👤 Физическое лицо", callback_data="type_individual"),
            InlineKeyboardButton("🏢 Юридическое лицо", callback_data="type_legal")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✅ Имя сохранено!\n\n"
        "📋 Выберите тип лица:",
        reply_markup=reply_markup
    )
    
    return WAITING_FOR_USER_TYPE


async def handle_user_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user type selection"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    session = get_user_session(user.id, query.message.chat_id, user.username)
    
    user_type_str = query.data.replace("type_", "")
    user_type = UserType.INDIVIDUAL if user_type_str == "individual" else UserType.LEGAL
    
    if session.contact_info:
        session.contact_info.user_type = user_type
    
    if user_type == UserType.LEGAL:
        session.waiting_for = "company"
        await query.edit_message_text(
            "✅ Тип лица: Юридическое лицо\n\n"
            "🏢 Отправьте название компании:"
        )
        return WAITING_FOR_COMPANY_INFO
    else:
        session.waiting_for = "message"
        await query.edit_message_text(
            "✅ Тип лица: Физическое лицо\n\n"
            "💬 Теперь опишите вашу проблему или вопрос:"
        )
        return WAITING_FOR_MESSAGE


async def handle_company_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle company information for legal entities"""
    user = update.effective_user
    session = get_user_session(user.id, update.effective_chat.id, user.username)
    
    company_name = update.message.text.strip()
    
    if session.contact_info:
        session.contact_info.company_name = company_name
    
    session.waiting_for = "message"
    
    await update.message.reply_text(
        f"✅ Компания: {company_name}\n\n"
        "💬 Теперь опишите вашу проблему или вопрос:"
    )
    
    return WAITING_FOR_MESSAGE


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user message/question - упрощенная версия: просто отвечает привет"""
    try:
        if not update.message or not update.message.text:
            logger.warning("Received update without message text")
            return
        
        # Просто отвечаем "привет" на любое сообщение
        await update.message.reply_text("👋 Привет!")
        
    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        try:
            if update.message:
                await update.message.reply_text("👋 Привет!")
        except:
            pass


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation"""
    user = update.effective_user
    if user.id in user_sessions:
        del user_sessions[user.id]
    
    await update.message.reply_text(
        "❌ Диалог отменен.\n"
        "Используйте /start для начала нового обращения."
    )
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors that occur during update processing"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    # Try to send error message to user if update is available
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Пожалуйста, используйте команду /start для начала заново."
            )
        except:
            pass


def main():
    """Start the bot"""
    try:
        # Create application
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        
        # Упрощенная версия: просто отвечаем на сообщения
        # Create simple message handler
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Start bot
        logger.info("Starting bot...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

