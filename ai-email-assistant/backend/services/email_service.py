"""
Email Service for connecting to Gmail/Outlook and managing emails.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Outlook imports
from exchangelib import Credentials as ExchangeCredentials, Account, Configuration, DELEGATE
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter

from ..models.schemas import Email, EmailProvider, WebhookPayload

logger = logging.getLogger(__name__)

class EmailService:
    """Service for email operations across different providers."""
    
    def __init__(self):
        self.connected_accounts = {}
        self.gmail_service = None
        self.outlook_account = None
        
    async def initialize(self):
        """Initialize email service."""
        logger.info("Initializing Email Service...")
        # Any initialization logic here
        
    async def cleanup(self):
        """Cleanup email service resources."""
        logger.info("Cleaning up Email Service...")
        self.connected_accounts.clear()
        
    async def health_check(self) -> Dict[str, str]:
        """Check email service health."""
        try:
            # Test basic connectivity
            return {"status": "healthy", "accounts": len(self.connected_accounts)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def connect_account(
        self, 
        user_id: str, 
        provider: str, 
        credentials: Dict[str, Any]
    ) -> str:
        """Connect email account."""
        try:
            if provider.lower() == "gmail":
                account_id = await self._connect_gmail(user_id, credentials)
            elif provider.lower() == "outlook":
                account_id = await self._connect_outlook(user_id, credentials)
            else:
                raise ValueError(f"Unsupported email provider: {provider}")
                
            self.connected_accounts[account_id] = {
                "user_id": user_id,
                "provider": provider,
                "connected_at": datetime.utcnow(),
                "status": "active"
            }
            
            logger.info(f"Connected {provider} account for user {user_id}")
            return account_id
            
        except Exception as e:
            logger.error(f"Failed to connect {provider} account: {e}")
            raise
    
    async def _connect_gmail(self, user_id: str, credentials: Dict[str, Any]) -> str:
        """Connect to Gmail account."""
        try:
            # OAuth2 flow for Gmail
            creds = None
            if 'token' in credentials:
                creds = Credentials.from_authorized_user_info(credentials['token'])
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Need to implement OAuth flow
                    raise ValueError("Valid Gmail credentials required")
            
            service = build('gmail', 'v1', credentials=creds)
            self.gmail_service = service
            
            # Get user profile for account ID
            profile = service.users().getProfile(userId='me').execute()
            account_id = f"gmail_{user_id}_{profile['emailAddress']}"
            
            return account_id
            
        except Exception as e:
            logger.error(f"Gmail connection failed: {e}")
            raise
    
    async def _connect_outlook(self, user_id: str, credentials: Dict[str, Any]) -> str:
        """Connect to Outlook account."""
        try:
            # Exchange/Outlook connection
            username = credentials.get('username')
            password = credentials.get('password')
            server = credentials.get('server', 'outlook.office365.com')
            
            if not username or not password:
                raise ValueError("Username and password required for Outlook")
            
            exchange_creds = ExchangeCredentials(username=username, password=password)
            config = Configuration(server=server, credentials=exchange_creds)
            account = Account(primary_smtp_address=username, config=config, 
                            autodiscover=False, access_type=DELEGATE)
            
            self.outlook_account = account
            account_id = f"outlook_{user_id}_{username}"
            
            return account_id
            
        except Exception as e:
            logger.error(f"Outlook connection failed: {e}")
            raise
    
    async def get_inbox(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        category: Optional[str] = None
    ) -> List[Email]:
        """Get inbox emails."""
        try:
            # Find user's connected accounts
            user_accounts = [
                acc for acc in self.connected_accounts.values() 
                if acc["user_id"] == user_id and acc["status"] == "active"
            ]
            
            if not user_accounts:
                return []
            
            emails = []
            for account in user_accounts:
                if account["provider"].lower() == "gmail":
                    emails.extend(await self._get_gmail_emails(limit, offset))
                elif account["provider"].lower() == "outlook":
                    emails.extend(await self._get_outlook_emails(limit, offset))
            
            # Filter by category if specified
            if category:
                emails = [e for e in emails if e.category == category]
            
            return emails[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get inbox: {e}")
            raise
    
    async def _get_gmail_emails(self, limit: int, offset: int) -> List[Email]:
        """Get Gmail emails."""
        try:
            if not self.gmail_service:
                return []
            
            # Get message IDs
            results = self.gmail_service.users().messages().list(
                userId='me', maxResults=limit, q='in:inbox'
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages[offset:offset+limit]:
                # Get full message
                message = self.gmail_service.users().messages().get(
                    userId='me', id=msg['id'], format='full'
                ).execute()
                
                email = await self._parse_gmail_message(message)
                emails.append(email)
            
            return emails
            
        except Exception as e:
            logger.error(f"Failed to get Gmail emails: {e}")
            return []
    
    async def _parse_gmail_message(self, message: Dict) -> Email:
        """Parse Gmail message to Email model."""
        headers = {h['name']: h['value'] for h in message['payload']['headers']}
        
        # Extract body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode()
        elif message['payload']['body'].get('data'):
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode()
        
        return Email(
            id=message['id'],
            subject=headers.get('Subject', 'No Subject'),
            sender=headers.get('From', ''),
            recipient=headers.get('To', ''),
            body=body,
            received_at=datetime.fromtimestamp(int(message['internalDate'])/1000),
            is_read='UNREAD' not in message.get('labelIds', [])
        )
    
    async def _get_outlook_emails(self, limit: int, offset: int) -> List[Email]:
        """Get Outlook emails."""
        try:
            if not self.outlook_account:
                return []
            
            emails = []
            items = self.outlook_account.inbox.all().order_by('-datetime_received')[offset:offset+limit]
            
            for item in items:
                email = Email(
                    id=str(item.id),
                    subject=item.subject or "No Subject",
                    sender=str(item.sender),
                    recipient=str(item.to_recipients[0] if item.to_recipients else ''),
                    body=item.text_body or "",
                    html_body=item.body,
                    received_at=item.datetime_received,
                    is_read=item.is_read
                )
                emails.append(email)
            
            return emails
            
        except Exception as e:
            logger.error(f"Failed to get Outlook emails: {e}")
            return []
    
    async def get_email(self, user_id: str, email_id: str) -> Optional[Email]:
        """Get specific email by ID."""
        try:
            # This is a simplified implementation
            # In production, you'd track which account each email belongs to
            inbox_emails = await self.get_inbox(user_id, limit=1000)
            for email in inbox_emails:
                if email.id == email_id:
                    return email
            return None
            
        except Exception as e:
            logger.error(f"Failed to get email {email_id}: {e}")
            return None
    
    async def update_email_category(self, email_id: str, category: str):
        """Update email category."""
        # In production, store in database
        logger.info(f"Updated email {email_id} category to {category}")
    
    async def update_email_priority(self, email_id: str, priority_score: int):
        """Update email priority score."""
        # In production, store in database
        logger.info(f"Updated email {email_id} priority to {priority_score}")
    
    async def mark_as_spam(self, email_id: str):
        """Mark email as spam."""
        # In production, move to spam folder and update database
        logger.info(f"Marked email {email_id} as spam")
    
    async def bulk_process_emails(self, user_id: str, limit: int):
        """Process multiple emails in background."""
        try:
            logger.info(f"Starting bulk processing for user {user_id}, limit {limit}")
            
            emails = await self.get_inbox(user_id, limit=limit)
            
            # Import here to avoid circular imports
            from .ai_service import AIService
            ai_service = AIService()
            
            for email in emails:
                try:
                    # Process each email
                    if not email.category:
                        category = await ai_service.categorize_email(email)
                        await self.update_email_category(email.id, category.category)
                    
                    if not email.priority_score:
                        priority = await ai_service.score_priority(email)
                        await self.update_email_priority(email.id, priority.score)
                    
                    # Check for spam
                    spam_result = await ai_service.detect_spam(email)
                    if spam_result.is_spam:
                        await self.mark_as_spam(email.id)
                    
                    await asyncio.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Failed to process email {email.id}: {e}")
                    continue
            
            logger.info(f"Completed bulk processing for user {user_id}")
            
        except Exception as e:
            logger.error(f"Bulk processing failed: {e}")
            raise
    
    async def get_analytics(self, user_id: str, days: int) -> Dict[str, Any]:
        """Get email analytics."""
        try:
            # Get recent emails
            emails = await self.get_inbox(user_id, limit=1000)
            
            # Filter by date range
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_emails = [e for e in emails if e.received_at >= cutoff_date]
            
            # Calculate analytics
            analytics = {
                "total_emails": len(recent_emails),
                "unread_count": len([e for e in recent_emails if not e.is_read]),
                "spam_count": len([e for e in recent_emails if e.is_spam]),
                "category_breakdown": {},
                "priority_breakdown": {},
                "daily_volume": [],
                "top_senders": []
            }
            
            # Category breakdown
            for email in recent_emails:
                category = email.category or "uncategorized"
                analytics["category_breakdown"][category] = analytics["category_breakdown"].get(category, 0) + 1
            
            # Priority breakdown
            for email in recent_emails:
                if email.priority_score:
                    if email.priority_score >= 8:
                        level = "urgent"
                    elif email.priority_score >= 6:
                        level = "high"
                    elif email.priority_score >= 4:
                        level = "medium"
                    else:
                        level = "low"
                    analytics["priority_breakdown"][level] = analytics["priority_breakdown"].get(level, 0) + 1
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}
    
    async def process_webhook_email(self, payload: WebhookPayload) -> Dict[str, Any]:
        """Process webhook email notification."""
        try:
            event_data = payload.data
            user_id = event_data.get("user_id")
            email_id = event_data.get("email_id")
            
            if not user_id or not email_id:
                raise ValueError("user_id and email_id required in webhook payload")
            
            # Get the email
            email = await self.get_email(user_id, email_id)
            if not email:
                raise ValueError(f"Email {email_id} not found")
            
            # Process with AI
            from .ai_service import AIService
            ai_service = AIService()
            
            results = {}
            
            # Auto-categorize
            if not email.category:
                category = await ai_service.categorize_email(email)
                await self.update_email_category(email_id, category.category)
                results["category"] = category.category
            
            # Auto-priority
            if not email.priority_score:
                priority = await ai_service.score_priority(email)
                await self.update_email_priority(email_id, priority.score)
                results["priority"] = priority.score
            
            # Spam check
            spam_result = await ai_service.detect_spam(email)
            if spam_result.is_spam:
                await self.mark_as_spam(email_id)
                results["spam_detected"] = True
            
            return results
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise