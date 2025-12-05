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
    level=logging.INFO
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command - begin conversation"""
    user = update.effective_user
    session = get_user_session(user.id, update.effective_chat.id, user.username)
    
    welcome_text = (
        "👋 Добро пожаловать в службу поддержки!\n\n"
        "Для начала работы нам нужна ваша контактная информация.\n\n"
        "📱 Пожалуйста, отправьте ваш номер телефона.\n"
        "Вы можете использовать кнопку ниже или написать номер вручную:"
    )
    
    # Предлагаем кнопку для отправки контакта
    keyboard = [
        [KeyboardButton("📱 Отправить мой контакт", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup
    )
    
    session.waiting_for = "phone"
    return WAITING_FOR_PHONE


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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user message/question"""
    user = update.effective_user
    session = get_user_session(user.id, update.effective_chat.id, user.username)
    
    message_text = update.message.text.strip()
    session.current_message = message_text
    
    if not session.contact_info or not session.contact_info.full_name:
        await update.message.reply_text(
            "❌ Сначала нужно заполнить контактную информацию.\n"
            "Используйте команду /start для начала."
        )
        return ConversationHandler.END
    
    # Отправляем сообщение о том, что обрабатываем
    processing_msg = await update.message.reply_text("⏳ Обрабатываю ваш запрос...")
    
    try:
        # Анализируем сообщение через RAG/AI
        contact_dict = session.contact_info.model_dump() if session.contact_info else {}
        ai_result = await api_client.analyze_message(message_text, contact_dict)
        
        if ai_result.get("can_answer", False) and ai_result.get("answer"):
            # Можем ответить сразу
            answer = ai_result["answer"]
            await processing_msg.edit_text(
                f"✅ Ответ:\n\n{answer}\n\n"
                "Если у вас есть еще вопросы, просто напишите их."
            )
            # Остаемся в состоянии ожидания сообщения
            return WAITING_FOR_MESSAGE
        else:
            # Нужно создать тикет
            subject = ai_result.get("subject") or message_text[:50] + "..."
            
            ticket_request = TicketRequest(
                source="telegram",
                subject=subject,
                description=message_text,
                contact_info=session.contact_info,
                telegram_user_id=user.id,
                telegram_chat_id=update.effective_chat.id,
                telegram_username=user.username
            )
            
            ticket_result = await api_client.create_ticket(ticket_request)
            ticket_id = ticket_result.get("ticket_id", "unknown")
            
            await processing_msg.edit_text(
                f"✅ Ваше обращение принято!\n\n"
                f"📋 Номер тикета: #{ticket_id[:8]}\n"
                f"📊 Приоритет: {ai_result.get('priority', 'medium')}\n"
                f"🏢 Отдел: {ai_result.get('department', 'TechSupport')}\n\n"
                "Наш специалист свяжется с вами в ближайшее время.\n\n"
                "Если у вас есть еще вопросы, используйте команду /start для нового обращения."
            )
            
            # Сбрасываем сессию
            session.current_message = None
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка при обработке вашего запроса.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с поддержкой напрямую."
        )
        return ConversationHandler.END


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


def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_PHONE: [
                MessageHandler(filters.CONTACT | filters.TEXT & ~filters.COMMAND, handle_contact)
            ],
            WAITING_FOR_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)
            ],
            WAITING_FOR_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)
            ],
            WAITING_FOR_USER_TYPE: [
                CallbackQueryHandler(handle_user_type, pattern="^type_")
            ],
            WAITING_FOR_COMPANY_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_company_info)
            ],
            WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Start bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()

