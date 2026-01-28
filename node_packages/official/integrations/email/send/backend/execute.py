"""
Email Send Node Plugin

Send emails via SMTP providers like Gmail, Outlook, or custom servers.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List
from jinja2 import Template
from fuse.workflows.engine.context import NodeContext
from fuse.workflows.engine.definitions import WorkflowItem

# Helper
from fuse.credentials.service import get_active_credential


async def execute(context: NodeContext) -> List[WorkflowItem]:
    """
    Send email via SMTP.
    """
    resolved_config = context.resolve_config()
    raw_config = context.raw_config
    items = context.input_data # List[WorkflowItem]
    
    # 1. Resolve Credentials
    cred_id = resolved_config.get("auth")
    if not cred_id:
        raise ValueError("SMTP Credentials required")

    cred = await get_active_credential(cred_id)
    if not cred:
        raise ValueError(f"Credential {cred_id} not found")

    cred_data = cred.get("data", {})
    
    # SMTP configuration (priority: resolved_config > credentials)
    # Allows overriding host/port in node config
    smtp_host = resolved_config.get("smtp_host") or cred_data.get("host") or "smtp.gmail.com"
    smtp_port = resolved_config.get("smtp_port") or cred_data.get("port") or 587
    smtp_user = cred_data.get("username") or cred_data.get("user")
    smtp_password = cred_data.get("password")
    use_tls = resolved_config.get("use_tls", True)

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP credentials (user/pass) missing")

    # 2. Batch Loop
    # Loop over items, resolve templates, send emails.
    # Note: Optimization - Open SMTP connection ONCE for the batch?
    # Yes, much better.
    
    loop_items = items if items else [WorkflowItem(json={})]
    results = []
    
    # Pre-fetch raw templates to avoid re-resolving static fields unnecessarily
    # (Though we need to resolve per item).
    to_template = raw_config.get("to", "")
    subject_template = raw_config.get("subject", "")
    body_template = raw_config.get("body", "")
    html = resolved_config.get("html", False)
    
    from_email = resolved_config.get("from_email") or smtp_user
    from_name = resolved_config.get("from_name", "")
    cc_template = raw_config.get("cc", "")
    bcc_template = raw_config.get("bcc", "")

    try:
        with smtplib.SMTP(smtp_host, int(smtp_port), timeout=30) as server:
            if use_tls:
                server.starttls()
            
            server.login(smtp_user, smtp_password)
            
            for item in loop_items:
                item_ctx = {
                    "input": item.json_data,
                    "inputs": item.json_data,
                    "workflow_id": context.workflow_id,
                    "execution_id": context.execution_id
                }
                
                # Render templates
                try:
                    to = Template(to_template).render(item_ctx)
                    subject = Template(subject_template).render(item_ctx)
                    body = Template(body_template).render(item_ctx)
                    cc = Template(cc_template).render(item_ctx) if cc_template else ""
                    bcc = Template(bcc_template).render(item_ctx) if bcc_template else ""
                except Exception as e:
                    # If template fails, fallback or error?
                    # Error entire batch? or just this item?
                    # Let's log and error item
                     results.append(WorkflowItem(
                        json={"success": False, "error": f"Template Render Error: {str(e)}"},
                        binary=item.binary_data,
                        pairedItem=item.paired_item
                    ))
                     continue

                if not to or not subject or not body:
                     results.append(WorkflowItem(
                        json={"success": False, "error": "Missing required fields (to, subject, body)"},
                        binary=item.binary_data,
                        pairedItem=item.paired_item
                    ))
                     continue

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
                
                # Send
                all_recipients = to_list + cc_list + bcc_list
                
                try:
                    server.send_message(msg)
                    results.append(WorkflowItem(
                        json={
                            "success": True,
                            "message_id": msg.get('Message-ID', ''),
                            "recipients": all_recipients
                        },
                        binary=item.binary_data,
                        pairedItem=item.paired_item
                    ))
                except Exception as e:
                    results.append(WorkflowItem(
                        json={"success": False, "error": f"SMTP Send Error: {str(e)}"},
                        binary=item.binary_data,
                        pairedItem=item.paired_item
                    ))

    except Exception as e:
        # Connection level error (Login failed, Host not found)
        raise RuntimeError(f"SMTP Connection Error: {str(e)}")

    return results


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
