# HTTP Request Node

Make HTTP requests to external APIs and services.

## Description

The HTTP Request node allows you to send HTTP requests (GET, POST, PUT, PATCH, DELETE) to any URL. It's perfect for:

- Calling external APIs
- Webhooks
- Data fetching
- Integration with third-party services

## Inputs

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| url | string | Yes | - | The URL to send the request to |
| method | select | Yes | GET | HTTP method (GET, POST, PUT, PATCH, DELETE) |
| headers | json | No | {} | HTTP headers to include in the request |
| body | json | No | {} | Request body (for POST, PUT, PATCH) |

## Outputs

| Name | Type | Description |
|------|------|-------------|
| status | number | HTTP response status code (200, 404, etc.) |
| data | json | Response body (parsed JSON or text) |
| headers | json | Response headers |

## Usage Examples

### Example 1: GET Request

```json
{
  "url": "https://api.example.com/users",
  "method": "GET"
}
```

### Example 2: POST with JSON Body

```json
{
  "url": "https://api.example.com/users",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer {{credentials.api_token}}"
  },
  "body": {
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

### Example 3: Using Template Variables

```json
{
  "url": "https://api.example.com/users/{{previous_node.outputs.user_id}}",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer {{credentials.api_token}}"
  }
}
```

## Error Handling

The node will throw an error if:
- URL is missing
- Request times out (30 second limit)
- Network error occurs
- Invalid method specified

## Tips

- Always include `https://` or `http://` in your URL (or it will default to https)
- Use template variables `{{}}` to reference outputs from previous nodes
- Check the `status` output to handle different response codes
- For APIs requiring authentication, use the `headers` input with your credentials

## Version History

- **1.0.0** (2026-01-26): Initial plugin release
