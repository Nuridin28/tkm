"""
Telegram Bot for Help Desk
"""
import logging
import re
import os
import psutil
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import Conflict
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
    """Handle user message/question with RAG"""
    try:
        if not update.message or not update.message.text:
            logger.warning("Received update without message text")
            return
        
        user = update.effective_user
        session = get_user_session(user.id, update.effective_chat.id, user.username)
        
        message_text = update.message.text.strip()
        
        # Build conversation history from session (БЕЗ текущего сообщения)
        # Текущее сообщение будет добавлено в историю только после получения ответа
        conversation_history = (session.conversation_history or []).copy()
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Analyze message with RAG
        # Передаем историю БЕЗ текущего сообщения - backend сам добавит его при обработке
        contact_info = session.contact_info.model_dump() if session.contact_info else {}
        analysis = await api_client.analyze_message(
            message_text,
            contact_info=contact_info,
            conversation_history=conversation_history
        )
        
        # Update conversation history and send answer
        can_answer = analysis.get("can_answer", False)
        ticket_created = analysis.get("ticketCreated", False)
        answer = analysis.get("response") or analysis.get("answer")
        ticket_draft = analysis.get("ticket_draft")
        updated_history = analysis.get("conversation_history")
        
        # Сохраняем ticket_draft в сессии для возможного создания тикета
        if ticket_draft:
            session.ticket_draft = ticket_draft
        
        # Используем обновленную историю из ответа backend, если она есть
        # Это предотвращает дублирование сообщений
        if updated_history:
            # Конвертируем формат из backend в формат бота
            session.conversation_history = [
                {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                }
                for msg in updated_history
            ]
        else:
            # Fallback: добавляем текущее сообщение и ответ вручную
            conversation_history.append({
                "role": "user",
                "content": message_text
            })
            if answer:
                conversation_history.append({
                    "role": "assistant",
                    "content": answer
                })
            session.conversation_history = conversation_history
        
        if ticket_created:
            # Тикет уже создан автоматически
            ticket_id = analysis.get("ticket_draft", {}).get("ticket_id") if ticket_draft else None
            if answer:
                
                try:
                    await update.message.reply_text(
                        f"{answer}\n\n✅ Тикет создан автоматически. Мы свяжемся с вами в ближайшее время.",
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.warning(f"Markdown parse error, sending plain text: {e}")
                    await update.message.reply_text(
                        f"{answer}\n\n✅ Тикет создан автоматически. Мы свяжемся с вами в ближайшее время."
                    )
            else:
                await update.message.reply_text(
                    "✅ Ваш запрос зарегистрирован как тикет. Мы свяжемся с вами в ближайшее время."
                )
            logger.info(f"✅ Ticket auto-created for user {user.id}")
        elif can_answer and answer:
            # We can answer - send the answer
            # Добавляем ответ ассистента в историю
            conversation_history.append({
                "role": "assistant",
                "content": answer
            })
            session.conversation_history = conversation_history
            
            # Send answer with Markdown formatting
            try:
                await update.message.reply_text(
                    answer,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            except Exception as e:
                # Если Markdown не работает, отправляем без форматирования
                logger.warning(f"Markdown parse error, sending plain text: {e}")
                await update.message.reply_text(answer)
            logger.info(f"✅ Answered message from {user.id} via RAG")
        else:
            # Can't answer - offer to create ticket
            session.current_message = message_text
            keyboard = [
                [InlineKeyboardButton("✅ Создать тикет", callback_data=f"create_ticket_{user.id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if answer:
                # There's an answer but it's not sufficient (can_answer=False)
                try:
                    await update.message.reply_text(
                        f"{answer}\n\nНе удалось найти полный ответ в базе знаний. Хотите создать тикет?",
                        reply_markup=reply_markup,
                        parse_mode='Markdown',
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.warning(f"Markdown parse error, sending plain text: {e}")
                    await update.message.reply_text(
                        f"{answer}\n\nНе удалось найти полный ответ в базе знаний. Хотите создать тикет?",
                        reply_markup=reply_markup
                    )
            else:
                # No answer at all
                await update.message.reply_text(
                    "К сожалению, я не могу ответить на этот вопрос автоматически. Хотите создать тикет для обращения в техподдержку?",
                    reply_markup=reply_markup
                )
        
    except Exception as e:
        logger.error(f"Error in handle_message: {e}", exc_info=True)
        try:
            if update.message:
                await update.message.reply_text(
                    "❌ Произошла ошибка при обработке вашего сообщения. "
                    "Пожалуйста, попробуйте еще раз или используйте /start для начала заново."
                )
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
    error = context.error
    
    # Обработка конфликта - несколько экземпляров бота
    if isinstance(error, Conflict) or (isinstance(error, Exception) and "Conflict" in str(error) and "getUpdates" in str(error)):
        logger.warning(f"Conflict detected - another bot instance may be running: {error}")
        logger.warning("This instance will attempt to reconnect. Make sure only one bot instance is running.")
        # Не логируем как ошибку, так как это ожидаемое поведение при конфликте
        return
    
    logger.error(f"Exception while handling an update: {error}", exc_info=error)
    
    # Try to send error message to user if update is available
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Пожалуйста, используйте команду /start для начала заново."
            )
        except:
            pass


def check_existing_instance():
    """Проверить, не запущен ли уже другой экземпляр бота"""
    current_pid = os.getpid()
    script_name = os.path.basename(__file__)
    
    # Ищем процессы с тем же скриптом
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] == current_pid:
                continue  # Пропускаем текущий процесс
            
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any(script_name in str(arg) for arg in cmdline):
                # Найден другой процесс с тем же скриптом
                old_pid = proc.info['pid']
                logger.warning(f"Found existing bot instance with PID {old_pid}. Terminating...")
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    logger.info(f"Successfully terminated old instance (PID: {old_pid})")
                except psutil.TimeoutExpired:
                    proc.kill()
                    logger.info(f"Force killed old instance (PID: {old_pid})")
                except psutil.NoSuchProcess:
                    logger.info(f"Old instance already terminated (PID: {old_pid})")
                except Exception as e:
                    logger.error(f"Error terminating old instance: {e}")
                # Даем время на завершение
                import time
                time.sleep(2)
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            logger.debug(f"Error checking process {proc.info.get('pid')}: {e}")


def main():
    """Start the bot"""
    try:
        # Проверяем, не запущен ли уже другой экземпляр
        try:
            check_existing_instance()
        except Exception as e:
            logger.warning(f"Could not check for existing instances: {e}")
            # Продолжаем запуск, так как это не критично
        
        # Create application
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Add callback query handler for ticket creation
        async def handle_ticket_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()
            
            if query.data.startswith("create_ticket_"):
                # Extract user_id from callback_data
                user_id_str = query.data.replace("create_ticket_", "")
                try:
                    user_id = int(user_id_str)
                except ValueError:
                    await query.message.reply_text("❌ Ошибка: неверный формат данных.")
                    return
                
                user = update.effective_user
                session = get_user_session(user.id, query.message.chat_id, user.username)
                
                # Get message from session
                message_text = session.current_message or "Запрос от пользователя"
                
                try:
                    # Create ticket request
                    from models import TicketRequest
                    ticket_request = TicketRequest(
                        subject=message_text[:50] + "..." if len(message_text) > 50 else message_text,
                        description=message_text,
                        contact_info=session.contact_info or ContactInfo(phone="", full_name="", user_type=UserType.INDIVIDUAL),
                        telegram_user_id=user.id,
                        telegram_chat_id=query.message.chat_id,
                        telegram_username=user.username
                    )
                    
                    # Используем ticket_draft из сессии если есть, иначе создаем новый
                    ticket_draft = getattr(session, 'ticket_draft', None)
                    result = await api_client.create_ticket(ticket_request, ticket_draft=ticket_draft)
                    
                    await query.message.reply_text(
                        f"✅ Тикет #{result['ticket_id'][:8]} создан!\n\n"
                        f"Приоритет: {result.get('priority', 'medium')}\n"
                        f"Департамент: {result.get('department', 'TechSupport')}\n\n"
                        f"Мы свяжемся с вами в ближайшее время."
                    )
                    
                    # Clear current message
                    session.current_message = None
                except Exception as e:
                    logger.error(f"Error creating ticket: {e}")
                    await query.message.reply_text("❌ Ошибка при создании тикета. Попробуйте еще раз.")
        
        application.add_handler(CallbackQueryHandler(handle_ticket_callback))
        
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

