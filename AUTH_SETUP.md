# Authentication Setup

The Tilts benchmark platform now includes basic authentication to protect API endpoints that consume API credits.

## Quick Start

Set these environment variables on Render:

```bash
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_secure_password
```

## Environment Variables

- `AUTH_USERNAME` - Username for basic auth (default: "admin")
- `AUTH_PASSWORD` - Password for basic auth (required - generates random if not set)
- `DISABLE_AUTH` - Set to "true" to disable auth (not recommended in production)

## Protected Endpoints

The following endpoints require authentication:
- `/` - Main interface
- `/admin` - Admin interface  
- `/summary/{job_id}` - Game summary pages
- `/api/play` - Play endpoint (consumes API credits)

## Local Development

For local development, you can either:

1. Set credentials in `.env`:
```
AUTH_USERNAME=dev
AUTH_PASSWORD=localpassword
```

2. Or disable auth:
```
DISABLE_AUTH=true
```

## Security Notes

- Uses HTTP Basic Authentication
- Passwords are compared using `secrets.compare_digest` to prevent timing attacks
- If no password is set, a secure random password is generated and printed to logs
- Always use HTTPS in production (Render provides this automatically)

## Testing Authentication

```bash
# With curl
curl -u username:password https://your-app.onrender.com/api/play

# With Python requests
import requests
response = requests.get(
    'https://your-app.onrender.com/api/play',
    auth=('username', 'password')
)
```