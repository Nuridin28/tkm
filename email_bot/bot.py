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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

email_sessions: Dict[str, EmailSession] = {}
api_client = APIClient()


def get_email_session(email_address: str) -> EmailSession:
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
    conn = sqlite3.connect(settings.PROCESSED_EMAILS_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            message_id TEXT PRIMARY KEY,
            email_address TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )


































































