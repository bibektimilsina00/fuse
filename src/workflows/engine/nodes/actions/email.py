"""Email sending node"""
from typing import Any, Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from src.workflows.engine.nodes.base import BaseNode, NodeSchema, NodeInput, NodeOutput
from src.workflows.engine.nodes.registry import NodeRegistry


@NodeRegistry.register
class EmailNode(BaseNode):
    """Send emails via SMTP"""
    
    @property
    def schema(self) -> NodeSchema:
        return NodeSchema(
            name="email.send",
            label="Send Email",
            type="action",
            description="Sends an email via SMTP provider.",
            category="Communication",
            inputs=[
                NodeInput(name="to", type="string", label="To", required=True),
                NodeInput(name="subject", type="string", label="Subject"),
                NodeInput(name="body", type="string", label="Body")
            ],
            outputs=[
                NodeOutput(name="success", type="boolean", label="Sent")
            ],
            error_policy="retry"
        )
    
    async def execute(self, context: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        """Send email"""
        try:
            # Config comes from node settings
            config = context.get("node_config", {})
            
            # Merge config with incoming data (config takes priority for settings, but data can override)
            # This follows Rule 12: Nodes are pure functions, but config is injected.
            
            # Strategy: config values are usually static or templated, 
            # while input_data contains dynamic values from previous nodes.
            # For email, we might want to use a mix.
            
            to = config.get("to") or input_data.get("to", "")
            subject = config.get("subject") or input_data.get("subject", "")
            body = config.get("body") or input_data.get("body", "")
            from_email = config.get("from_email") or input_data.get("from_email", "")
            from_name = config.get("from_name") or input_data.get("from_name", "")
            html = config.get("html", False)
            
            # SMTP configuration
            smtp_host = config.get("smtp_host", "smtp.gmail.com")
            smtp_port = config.get("smtp_port", 587)
            smtp_user = config.get("smtp_user", from_email)
            smtp_password = config.get("smtp_password", "")
            use_tls = config.get("use_tls", True)
            
            # Optional CC/BCC
            cc = config.get("cc", "")
            bcc = config.get("bcc", "")
            
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
            
            with smtplib.SMTP(smtp_host, smtp_port) as server:
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
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message_id": None,
                "recipients": []
            }
