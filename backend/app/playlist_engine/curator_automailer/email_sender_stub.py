"""
Curator AutoMailer — Email Sender STUB

Simulates email sending.
STUB MODE: No real emails sent.
"""

from typing import Dict, Any, List
from datetime import datetime
import uuid


class EmailSenderStub:
    """
    STUB: Email sending interface.
    
    In LIVE mode, this would use:
    - SendGrid/AWS SES for transactional emails
    - Email tracking and analytics
    - Bounce/spam detection
    - Rate limiting and scheduling
    
    Phase 3: Simulates sending, logs to memory only.
    """
    
    def __init__(self):
        self.stub_mode = True
        self._sent_emails = []
        
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str = "noreply@stakazo.stub",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        STUB: Send email to curator.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
            from_email: Sender email
            metadata: Additional tracking metadata
            
        Returns:
            Send result dict
        """
        email_id = str(uuid.uuid4())
        
        email_record = {
            "email_id": email_id,
            "status": "sent_stub",
            "to": to_email,
            "from": from_email,
            "subject": subject,
            "body_length": len(body),
            "sent_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "stub_mode": True
        }
        
        # Store in memory
        self._sent_emails.append(email_record)
        
        return {
            "success": True,
            "email_id": email_id,
            "status": "sent_stub",
            "message": "Email sent successfully (STUB MODE)",
            "sent_at": email_record["sent_at"]
        }
    
    def send_batch(
        self,
        emails: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        STUB: Send batch of emails.
        
        Args:
            emails: List of email dicts (to, subject, body)
            
        Returns:
            Batch send results
        """
        results = []
        
        for email in emails:
            result = self.send_email(
                to_email=email["to"],
                subject=email["subject"],
                body=email["body"],
                metadata=email.get("metadata")
            )
            results.append(result)
        
        return {
            "success": True,
            "total_sent": len(results),
            "results": results,
            "stub_mode": True
        }
    
    def get_sent_emails(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent sent emails (STUB)"""
        return self._sent_emails[-limit:]
    
    def get_email_status(self, email_id: str) -> Dict[str, Any]:
        """
        STUB: Check email delivery status.
        
        Args:
            email_id: Email ID to check
            
        Returns:
            Status dict
        """
        for email in self._sent_emails:
            if email["email_id"] == email_id:
                return {
                    "email_id": email_id,
                    "status": "delivered_stub",
                    "opened": False,  # Would track in LIVE mode
                    "clicked": False,  # Would track in LIVE mode
                    "bounced": False,
                    "stub_mode": True
                }
        
        return {
            "email_id": email_id,
            "status": "not_found",
            "stub_mode": True
        }
    
    def schedule_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        send_at: str  # ISO format datetime
    ) -> Dict[str, Any]:
        """
        STUB: Schedule email for future sending.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
            send_at: ISO datetime for sending
            
        Returns:
            Schedule result dict
        """
        email_id = str(uuid.uuid4())
        
        return {
            "success": True,
            "email_id": email_id,
            "status": "scheduled_stub",
            "to": to_email,
            "send_at": send_at,
            "message": "Email scheduled (STUB MODE)",
            "stub_mode": True
        }
