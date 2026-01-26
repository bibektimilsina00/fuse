"""
Email Send Node Plugin

Send emails via SMTP providers like Gmail, Outlook, or custom servers.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List


async def execute(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send email via SMTP.
    
    Args:
        context: Execution context with config, inputs, credentials
        
    Returns:
        Dict with success status, message_id, and recipients
    """
    config = context.get("config", {})
    inputs = context.get("inputs", {})
    credentials = context.get("credentials", {})
    
    # Get email parameters (priority: config > inputs > credentials)
    to = config.get("to") or inputs.get("to", "")
    subject = config.get("subject") or inputs.get("subject", "")
    body = config.get("body") or inputs.get("body", "")
    from_email = config.get("from_email") or credentials.get("username", "")
    from_name = config.get("from_name", "")
    html = config.get("html", False)
    
    # Optional recipients
    cc = config.get("cc", "")
    bcc = config.get("bcc", "")
    
    # SMTP configuration (from credentials or config)
    smtp_host = credentials.get("host") or config.get("smtp_host", "smtp.gmail.com")
    smtp_port = credentials.get("port") or config.get("smtp_port", 587)
    smtp_user = credentials.get("username") or config.get("smtp_user", from_email)
    smtp_password = credentials.get("password") or config.get("smtp_password", "")
    use_tls = config.get("use_tls", True)
    
    # Validate required fields
    if not to:
        raise ValueError("'to' field is required")
    if not subject:
        raise ValueError("'subject' is required")
    if not body:
        raise ValueError("'body' is required")
    if not smtp_user or not smtp_password:
        raise ValueError("SMTP credentials are required (username and password)")
    
    try:
        # Parse recipients
        to_list = [email.strip() for email in to.split(",") if email.strip()]
        cc_list = [email.strip() for email in cc.split(",") if email.strip()] if cc else []
        bcc_list = [email.strip() for email in bcc.split(",") if email.strip()] if bcc else []
        
        # Create message
        msg = MIMEMultipart('alternative') if html else MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = f"{from_name} <{from_email}>" if from_name else from_email
        msg['To'] = ", ".join(to_list)
        
        if cc_list:
            msg['Cc'] = ", ".join(cc_list)
        
        # Attach body
        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        all_recipients = to_list + cc_list + bcc_list
        
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            if use_tls:
                server.starttls()
            
            if smtp_password:
                server.login(smtp_user, smtp_password)
            
            server.send_message(msg)
        
        return {
            "success": True,
            "message_id": msg.get('Message-ID', ''),
            "recipients": all_recipients
        }
        
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(f"SMTP authentication failed: {str(e)}")
    except smtplib.SMTPException as e:
        raise RuntimeError(f"SMTP error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {str(e)}")


async def validate(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate email configuration.
    
    Returns:
        Dict with 'valid' and 'errors'
    """
    errors = []
    
    # Required fields
    if not config.get("to"):
        errors.append("'to' field is required")
    if not config.get("subject"):
        errors.append("'subject' is required")
    if not config.get("body"):
        errors.append("'body' is required")
    
    # Validate email format (basic check)
    to = config.get("to", "")
    if to and "@" not in to:
        errors.append("'to' must be a valid email address")
    
    # SMTP configuration
    smtp_port = config.get("smtp_port", 587)
    if not isinstance(smtp_port, int) or smtp_port < 1 or smtp_port > 65535:
        errors.append("'smtp_port' must be between 1 and 65535")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
