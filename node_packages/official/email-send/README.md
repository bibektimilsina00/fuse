# Email Send Plugin

Send emails via SMTP providers.

## Supported Providers

- Gmail (smtp.gmail.com:587)
- Outlook (smtp.office365.com:587)
- Custom SMTP servers

## Configuration

### Required
- **to**: Recipient email(s) (comma-separated)
- **subject**: Email subject
- **body**: Email content
- **SMTP credentials**: Username and password

### Optional
- **from_email**: Sender email (defaults to SMTP username)
- **from_name**: Sender display name
- **cc**: CC recipients
- **bcc**: BCC recipients
- **html**: Send as HTML email
- **smtp_host**: SMTP server (default: smtp.gmail.com)
- **smtp_port**: SMTP port (default: 587)
- **use_tls**: Enable TLS (default: true)

## Usage Example

```json
{
  "to": "user@example.com",
  "subject": "Hello from Fuse!",
  "body": "This is an automated email.",
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_user": "your@gmail.com",
  "smtp_password": "your-app-password",
  "use_tls": true
}
```

## Gmail Setup

1. Enable 2-factor authentication
2. Generate an App Password
3. Use the app password (not your regular password)

## Outputs

- **success**: Boolean indicating if email was sent
- **message_id**: Email message ID
- **recipients**: Array of all recipients

## Version History

- **1.0.0**: Initial plugin release
