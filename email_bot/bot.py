"""
Email Bot for Help Desk
Обрабатывает входящие email письма и отвечает через AI с RAG
"""
import logging
import imaplib
import smtplib
import email
import sqlite3
import asyncio
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import Dict, Optional, List
from datetime import datetime
import psutil
import os

from config import settings
from models import EmailSession, ContactInfo, UserType, TicketRequest
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

# Storage for email sessions
email_sessions: Dict[str, EmailSession] = {}
api_client = APIClient()


def get_email_session(email_address: str) -> EmailSession:
    """Get or create email session"""
    if email_address not in email_sessions:
        email_sessions[email_address] = EmailSession(
            email_address=email_address,
            contact_info=ContactInfo(
                email=email_address,
                user_type=UserType.INDIVIDUAL
            )
        )
    return email_sessions[email_address]


def init_processed_emails_db():
    """Initialize SQLite database for tracking processed emails"""
    conn = sqlite3.connect(settings.PROCESSED_EMAILS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            message_id TEXT PRIMARY KEY,
            email_address TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Processed emails database initialized")


def is_email_processed(message_id: str) -> bool:
    """Check if email was already processed"""
    conn = sqlite3.connect(settings.PROCESSED_EMAILS_DB)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM processed_emails WHERE message_id = ?', (message_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def mark_email_processed(message_id: str, email_address: str):
    """Mark email as processed"""
    conn = sqlite3.connect(settings.PROCESSED_EMAILS_DB)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO processed_emails (message_id, email_address) VALUES (?, ?)',
        (message_id, email_address)
    )
    conn.commit()
    conn.close()


def decode_mime_words(s):
    """Decode MIME encoded words"""
    if s is None:
        return ""
    decoded_parts = decode_header(s)
    decoded_str = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
        else:
            decoded_str += part
    return decoded_str


def extract_text_from_email(msg: email.message.Message) -> str:
    """Extract text content from email message"""
    text_content = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Skip attachments
            if "attachment" in content_disposition:
                continue
            
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        text_content += payload.decode(charset, errors='ignore')
                except Exception as e:
                    logger.warning(f"Error decoding text/plain part: {e}")
            elif content_type == "text/html":
                # Try to extract text from HTML (simple approach)
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        html_content = payload.decode(charset, errors='ignore')
                        # Simple HTML tag removal
                        text_content += re.sub(r'<[^>]+>', '', html_content)
                except Exception as e:
                    logger.warning(f"Error decoding text/html part: {e}")
    else:
        # Not multipart
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                text_content = payload.decode(charset, errors='ignore')
        except Exception as e:
            logger.warning(f"Error decoding single part: {e}")
    
    return text_content.strip()


def send_email(to_address: str, subject: str, body: str, reply_to: Optional[str] = None):
    """Send email via SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg['To'] = to_address
        msg['Subject'] = subject
        if reply_to:
            msg['In-Reply-To'] = reply_to
            msg['References'] = reply_to
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP(settings.EMAIL_SMTP_SERVER, settings.EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent to {to_address}: {subject[:50]}")
        return True
    except Exception as e:
        logger.error(f"Error sending email to {to_address}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def process_email_message(msg: email.message.Message, message_id: str):
    """Process incoming email message"""
    try:
        # Extract email information
        from_address = decode_mime_words(msg['From'])
        to_address = decode_mime_words(msg['To'])
        subject = decode_mime_words(msg['Subject'])
        
        # Extract email address from "Name <email@example.com>" format
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_address)
        if not email_match:
            logger.warning(f"Could not extract email address from: {from_address}")
            return
        
        sender_email = email_match.group(0)
        
        # Skip if already processed
        if is_email_processed(message_id):
            logger.debug(f"Email {message_id} already processed, skipping")
            return
        
        logger.info(f"Processing email from {sender_email}: {subject[:50]}")
        
        # Extract text content
        message_text = extract_text_from_email(msg)
        
        if not message_text:
            logger.warning(f"No text content found in email from {sender_email}")
            send_email(
                sender_email,
                f"Re: {subject}",
                "К сожалению, не удалось извлечь текст из вашего письма. Пожалуйста, отправьте текст в формате plain text."
            )
            mark_email_processed(message_id, sender_email)
            return
        
        # Get or create session
        session = get_email_session(sender_email)
        
        # Update contact info if available
        if not session.contact_info:
            session.contact_info = ContactInfo(email=sender_email, user_type=UserType.INDIVIDUAL)
        else:
            session.contact_info.email = sender_email
        
        # Try to extract name from email
        name_match = re.search(r'^(.+?)\s*<', from_address)
        if name_match and not session.contact_info.full_name:
            session.contact_info.full_name = name_match.group(1).strip().strip('"\'')
        
        # Build conversation history (without current message)
        conversation_history = (session.conversation_history or []).copy()
        
        # Analyze message with RAG
        contact_info_dict = session.contact_info.model_dump() if session.contact_info else {}
        analysis = await api_client.analyze_message(
            message_text,
            contact_info=contact_info_dict,
            conversation_history=conversation_history
        )
        
        # Update conversation history
        can_answer = analysis.get("can_answer", False)
        ticket_created = analysis.get("ticketCreated", False)
        answer = analysis.get("response") or analysis.get("answer")
        ticket_draft = analysis.get("ticket_draft")
        updated_history = analysis.get("conversation_history")
        
        # Save ticket_draft in session
        if ticket_draft:
            session.ticket_draft = ticket_draft
        
        # Update conversation history from backend response
        if updated_history:
            session.conversation_history = [
                {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                }
                for msg in updated_history
            ]
        else:
            # Fallback: add current message and answer manually
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
        
        # Prepare response
        response_subject = f"Re: {subject}"
        response_body = ""
        
        if ticket_created:
            # Ticket was created automatically
            ticket_id = analysis.get("ticket_draft", {}).get("ticket_id") if ticket_draft else None
            if answer:
                response_body = f"{answer}\n\n✅ Ваш запрос зарегистрирован как тикет. Наши специалисты свяжутся с вами в ближайшее время."
            else:
                response_body = "✅ Ваш запрос зарегистрирован как тикет. Наши специалисты свяжутся с вами в ближайшее время."
            logger.info(f"✅ Ticket auto-created for {sender_email}")
        elif can_answer and answer:
            # We can answer - send the answer
            response_body = answer
            logger.info(f"✅ Answered email from {sender_email} via RAG")
        else:
            # Can't answer - offer to create ticket
            if answer:
                response_body = f"{answer}\n\nНе удалось найти полный ответ в базе знаний. Ваш запрос будет зарегистрирован как тикет."
                # Auto-create ticket if we can't answer
                try:
                    ticket_request = TicketRequest(
                        subject=subject[:100] + ("..." if len(subject) > 100 else ""),
                        description=message_text,
                        contact_info=session.contact_info or ContactInfo(email=sender_email, user_type=UserType.INDIVIDUAL),
                        email_address=sender_email,
                        email_message_id=message_id
                    )
                    result = await api_client.create_ticket(ticket_request, ticket_draft=session.ticket_draft)
                    response_body += f"\n\n✅ Тикет #{result['ticket_id'][:8]} создан. Мы свяжемся с вами в ближайшее время."
                    logger.info(f"✅ Ticket created for {sender_email}")
                except Exception as e:
                    logger.error(f"Error creating ticket: {e}")
                    response_body += "\n\nПожалуйста, обратитесь в техподдержку по телефону или через веб-интерфейс."
            else:
                response_body = "К сожалению, я не могу ответить на этот вопрос автоматически. Ваш запрос будет зарегистрирован как тикет."
                # Auto-create ticket
                try:
                    ticket_request = TicketRequest(
                        subject=subject[:100] + ("..." if len(subject) > 100 else ""),
                        description=message_text,
                        contact_info=session.contact_info or ContactInfo(email=sender_email, user_type=UserType.INDIVIDUAL),
                        email_address=sender_email,
                        email_message_id=message_id
                    )
                    result = await api_client.create_ticket(ticket_request, ticket_draft=session.ticket_draft)
                    response_body += f"\n\n✅ Тикет #{result['ticket_id'][:8]} создан. Мы свяжемся с вами в ближайшее время."
                    logger.info(f"✅ Ticket created for {sender_email}")
                except Exception as e:
                    logger.error(f"Error creating ticket: {e}")
                    response_body += "\n\nПожалуйста, обратитесь в техподдержку по телефону или через веб-интерфейс."
        
        # Send response
        send_email(sender_email, response_subject, response_body, reply_to=message_id)
        
        # Mark as processed
        mark_email_processed(message_id, sender_email)
        session.last_message_id = message_id
        
    except Exception as e:
        logger.error(f"Error processing email message: {e}", exc_info=True)


async def check_emails():
    """Check for new emails and process them"""
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(settings.EMAIL_IMAP_SERVER, settings.EMAIL_IMAP_PORT)
        mail.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        mail.select('INBOX')
        
        # Search for unread emails
        status, messages = mail.search(None, 'UNSEEN')
        
        if status != 'OK':
            logger.error("Error searching for emails")
            mail.close()
            mail.logout()
            return
        
        email_ids = messages[0].split()
        
        if not email_ids:
            logger.debug("No new emails")
            mail.close()
            mail.logout()
            return
        
        logger.info(f"Found {len(email_ids)} new email(s)")
        
        # Process each email
        for email_id in email_ids:
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)
                
                # Get message ID
                message_id = msg.get('Message-ID', email_id.decode())
                
                # Process email asynchronously
                await process_email_message(msg, message_id)
                
            except Exception as e:
                logger.error(f"Error processing email {email_id}: {e}", exc_info=True)
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        logger.error(f"Error checking emails: {e}", exc_info=True)


async def email_loop():
    """Main email checking loop"""
    logger.info("Starting email bot...")
    init_processed_emails_db()
    
    while True:
        try:
            await check_emails()
        except Exception as e:
            logger.error(f"Error in email loop: {e}", exc_info=True)
        
        # Wait before next check
        await asyncio.sleep(settings.CHECK_INTERVAL)


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
    """Start the email bot"""
    try:
        # Проверяем, не запущен ли уже другой экземпляр
        try:
            check_existing_instance()
        except Exception as e:
            logger.warning(f"Could not check for existing instances: {e}")
        
        # Run email loop
        asyncio.run(email_loop())
    except KeyboardInterrupt:
        logger.info("Email bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

