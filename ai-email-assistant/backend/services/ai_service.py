"""
AI Service for email analysis, summarization, and reply generation.
"""
import logging
import re
import os
from typing import List, Dict, Any, Optional
import openai

from ..models.schemas import (
    Email, EmailSummary, EmailReply, EmailCategory, 
    PriorityScore, SpamDetection, PriorityLevel
)

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered email processing."""
    
    def __init__(self):
        self.openai_client = None
        
    async def initialize(self):
        """Initialize AI service."""
        try:
            logger.info("Initializing AI Service...")
            
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.AsyncOpenAI(api_key=api_key)
            else:
                logger.warning("OpenAI API key not found")
            
            logger.info("AI Service initialized successfully")
            
        except Exception as e:
            logger.error(f"AI Service initialization failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, str]:
        """Check AI service health."""
        try:
            status = "healthy"
            components = {
                "openai": "available" if self.openai_client else "unavailable",
                "fallback_analysis": "available",
            }
            return {"status": status, "components": components}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def summarize_email(self, email: Email) -> EmailSummary:
        """Generate AI summary of email."""
        try:
            # Extract key information
            content = f"Subject: {email.subject}\n\nBody: {email.body[:2000]}"
            
            if self.openai_client:
                # Use OpenAI for high-quality summarization
                response = await self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert email analyst. Provide a concise summary with key points, sentiment analysis, and urgency assessment."
                        },
                        {
                            "role": "user",
                            "content": f"Analyze this email and provide:\n1. Brief summary (1-2 sentences)\n2. Key points (bullet list)\n3. Sentiment (positive/negative/neutral)\n4. Urgency (low/medium/high/urgent)\n5. Action required (yes/no)\n\nEmail:\n{content}"
                        }
                    ],
                    max_tokens=300,
                    temperature=0.3
                )
                
                ai_response = response.choices[0].message.content
                return await self._parse_summary_response(ai_response, email)
                
            else:
                # Fallback to rule-based summarization
                return await self._generate_rule_based_summary(email)
                
        except Exception as e:
            logger.error(f"Email summarization failed: {e}")
            # Return basic summary as fallback
            return EmailSummary(
                summary=f"Email from {email.sender} about: {email.subject}",
                key_points=[email.subject],
                sentiment="neutral",
                urgency="medium",
                action_required=False
            )
    
    async def _parse_summary_response(self, ai_response: str, email: Email) -> EmailSummary:
        """Parse OpenAI summary response."""
        try:
            lines = ai_response.split('\n')
            
            summary = ""
            key_points = []
            sentiment = "neutral"
            urgency = "medium"
            action_required = False
            
            for line in lines:
                line = line.strip()
                if line.startswith("1.") or "summary" in line.lower():
                    summary = re.sub(r'^\d+\.?\s*', '', line).strip()
                elif line.startswith("2.") or line.startswith("-") or line.startswith("•"):
                    key_points.append(re.sub(r'^[\d\-•]+\.?\s*', '', line).strip())
                elif "sentiment" in line.lower():
                    if "positive" in line.lower():
                        sentiment = "positive"
                    elif "negative" in line.lower():
                        sentiment = "negative"
                elif "urgency" in line.lower() or "urgent" in line.lower():
                    if "urgent" in line.lower():
                        urgency = "urgent"
                    elif "high" in line.lower():
                        urgency = "high"
                    elif "low" in line.lower():
                        urgency = "low"
                elif "action" in line.lower():
                    action_required = "yes" in line.lower()
            
            if not summary:
                summary = f"Email from {email.sender} regarding {email.subject}"
            
            return EmailSummary(
                summary=summary,
                key_points=key_points,
                sentiment=sentiment,
                urgency=urgency,
                action_required=action_required
            )
            
        except Exception as e:
            logger.error(f"Failed to parse summary response: {e}")
            return EmailSummary(
                summary=f"Email from {email.sender} about: {email.subject}",
                key_points=[email.subject],
                sentiment="neutral",
                urgency="medium", 
                action_required=False
            )
    
    async def _generate_rule_based_summary(self, email: Email) -> EmailSummary:
        """Generate rule-based email summary."""
        try:
            # Basic rule-based analysis
            urgent_keywords = ['urgent', 'asap', 'immediate', 'emergency', 'deadline']
            action_keywords = ['please', 'request', 'need', 'required', 'action', 'respond']
            
            urgency = "low"
            action_required = False
            
            content_lower = f"{email.subject} {email.body}".lower()
            
            # Check urgency
            if any(keyword in content_lower for keyword in urgent_keywords):
                urgency = "urgent"
            elif '!' in email.subject:
                urgency = "high"
            
            # Check action required
            if any(keyword in content_lower for keyword in action_keywords):
                action_required = True
            
            # Lightweight fallback sentiment analysis.
            sentiment = "neutral"
            words = set(re.findall(r"[a-z']+", email.body[:500].lower()))
            if words & {"thanks", "great", "excellent", "happy", "appreciate"}:
                sentiment = "positive"
            elif words & {"angry", "bad", "failed", "problem", "urgent"}:
                sentiment = "negative"
            
            # Extract key points (first sentence + subject)
            key_points = [email.subject]
            if email.body:
                sentences = email.body.split('. ')
                if sentences:
                    key_points.append(sentences[0])
            
            return EmailSummary(
                summary=f"Email from {email.sender} regarding {email.subject}",
                key_points=key_points[:3],
                sentiment=sentiment,
                urgency=urgency,
                action_required=action_required
            )
            
        except Exception as e:
            logger.error(f"Rule-based summary failed: {e}")
            raise
    
    async def generate_reply(self, email: Email, context: Optional[str] = None, tone: str = "professional") -> EmailReply:
        """Generate AI-powered email reply."""
        try:
            if not self.openai_client:
                raise ValueError("OpenAI client not available")
            
            # Prepare context
            email_content = f"Subject: {email.subject}\nFrom: {email.sender}\nBody: {email.body[:1500]}"
            context_text = f"\n\nAdditional Context: {context}" if context else ""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional email assistant. Generate a {tone} email reply that is helpful, concise, and appropriate. Include a subject line and body."
                    },
                    {
                        "role": "user", 
                        "content": f"Generate a reply to this email:\n{email_content}{context_text}"
                    }
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            reply_content = response.choices[0].message.content
            
            # Parse reply
            subject = f"Re: {email.subject}"
            body = reply_content
            
            # Try to extract subject if provided
            lines = reply_content.split('\n')
            for line in lines:
                if line.strip().startswith('Subject:'):
                    subject = line.replace('Subject:', '').strip()
                    body = '\n'.join(lines[1:]).strip()
                    break
            
            return EmailReply(
                subject=subject,
                body=body,
                tone=tone,
                suggestions=[
                    "Consider adding specific details",
                    "Include a call to action if needed",
                    "Review for professional tone"
                ]
            )
            
        except Exception as e:
            logger.error(f"Reply generation failed: {e}")
            # Return a basic template reply
            return EmailReply(
                subject=f"Re: {email.subject}",
                body=f"Thank you for your email.\n\nBest regards,",
                tone=tone,
                suggestions=["AI reply generation temporarily unavailable"]
            )
    
    async def categorize_email(self, email: Email) -> EmailCategory:
        """Categorize email using AI."""
        try:
            # Define categories and keywords
            categories = {
                'work': ['meeting', 'project', 'deadline', 'report', 'team', 'business', 'office'],
                'personal': ['family', 'friend', 'birthday', 'vacation', 'personal', 'home'],
                'promotions': ['sale', 'discount', 'offer', 'deal', 'promotion', 'coupon'],
                'newsletters': ['newsletter', 'update', 'news', 'digest', 'unsubscribe'],
                'social': ['facebook', 'twitter', 'linkedin', 'instagram', 'social', 'notification'],
                'updates': ['notification', 'update', 'system', 'security', 'account'],
                'forums': ['forum', 'discussion', 'reply', 'thread', 'community']
            }
            
            content = f"{email.subject} {email.body}".lower()
            
            # Calculate category scores
            category_scores = {}
            for category, keywords in categories.items():
                score = sum(1 for keyword in keywords if keyword in content)
                if score > 0:
                    category_scores[category] = score
            
            # Determine best category
            if category_scores:
                best_category = max(category_scores.items(), key=lambda x: x[1])
                category = best_category[0]
                confidence = min(best_category[1] / 10.0, 1.0)  # Normalize to 0-1
            else:
                category = "uncategorized"
                confidence = 0.5
            
            return EmailCategory(
                category=category,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Email categorization failed: {e}")
            return EmailCategory(
                category="uncategorized",
                confidence=0.0
            )
    
    async def score_priority(self, email: Email) -> PriorityScore:
        """Calculate email priority score."""
        try:
            score = 5  # Base score
            factors = []
            
            content = f"{email.subject} {email.body}".lower()
            
            # Sender-based scoring
            if any(domain in email.sender for domain in ['@company.com', '@boss.com']):
                score += 2
                factors.append("Important sender")
            
            # Subject line indicators
            urgent_words = ['urgent', 'asap', 'emergency', 'critical', 'immediate']
            if any(word in content for word in urgent_words):
                score += 3
                factors.append("Urgent keywords")
            
            if email.subject.count('!') > 0:
                score += 1
                factors.append("Exclamation marks")
            
            # Content analysis
            action_words = ['deadline', 'meeting', 'call', 'respond', 'reply', 'action required']
            if any(word in content for word in action_words):
                score += 2
                factors.append("Action required")
            
            # Time sensitivity
            time_words = ['today', 'tomorrow', 'this week', 'end of day']
            if any(word in content for word in time_words):
                score += 2
                factors.append("Time sensitive")
            
            # Caps lock penalty/boost
            caps_ratio = sum(1 for c in email.subject if c.isupper()) / len(email.subject) if email.subject else 0
            if caps_ratio > 0.7:
                score += 1
                factors.append("High urgency formatting")
            
            # Clamp score
            score = max(1, min(10, score))
            
            # Determine priority level
            if score >= 8:
                level = PriorityLevel.URGENT
            elif score >= 6:
                level = PriorityLevel.HIGH
            elif score >= 4:
                level = PriorityLevel.MEDIUM
            else:
                level = PriorityLevel.LOW
            
            return PriorityScore(
                score=score,
                level=level,
                factors=factors
            )
            
        except Exception as e:
            logger.error(f"Priority scoring failed: {e}")
            return PriorityScore(
                score=5,
                level=PriorityLevel.MEDIUM,
                factors=[]
            )
    
    async def detect_spam(self, email: Email) -> SpamDetection:
        """Detect if email is spam."""
        try:
            spam_score = 0.0
            reasons = []
            
            content = f"{email.subject} {email.body}".lower()
            
            # Spam indicators
            spam_keywords = [
                'viagra', 'lottery', 'winner', 'congratulations', 'million dollars',
                'free money', 'click here', 'act now', 'limited time', 'urgent action',
                'nigerian prince', 'inheritance', 'tax refund'
            ]
            
            keyword_matches = sum(1 for keyword in spam_keywords if keyword in content)
            if keyword_matches > 0:
                spam_score += keyword_matches * 0.2
                reasons.append(f"Spam keywords detected ({keyword_matches})")
            
            # Suspicious patterns
            if re.search(r'\b[A-Z]{5,}\b', email.subject):
                spam_score += 0.3
                reasons.append("Excessive caps in subject")
            
            if email.subject.count('!') > 2:
                spam_score += 0.2
                reasons.append("Multiple exclamation marks")
            
            # Suspicious sender patterns
            if re.search(r'[0-9]{3,}@', email.sender):
                spam_score += 0.4
                reasons.append("Suspicious sender address")
            
            # URL analysis
            url_count = len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', email.body))
            if url_count > 3:
                spam_score += 0.3
                reasons.append("Multiple URLs")
            
            # Normalize score
            spam_score = min(spam_score, 1.0)
            is_spam = spam_score > 0.7
            
            return SpamDetection(
                is_spam=is_spam,
                confidence=spam_score,
                reasons=reasons
            )
            
        except Exception as e:
            logger.error(f"Spam detection failed: {e}")
            return SpamDetection(
                is_spam=False,
                confidence=0.0,
                reasons=[]
            )
