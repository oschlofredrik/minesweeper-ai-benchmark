# Join Service for Tilts Platform

## Overview

The join service provides a minimal, Kahoot-style interface for joining Tilts competitions using a game PIN. It's designed to be deployed on a subdomain (join.tilts.com) for a clean, focused user experience.

## Features

- **Minimal UI**: Clean, distraction-free interface
- **Mobile Optimized**: Works great on phones and tablets
- **Auto-Uppercase**: PINs automatically convert to uppercase
- **Fast Validation**: Instant PIN checking via API
- **Seamless Redirect**: Joins directly to the main platform

## Architecture

```
join.tilts.com (port 8001) --> tilts.com (port 8000)
     |                              |
     v                              v
Join Service                   Main Platform
     |                              |
     +-------- API Check -----------+
```

## Running Locally

### Development Mode

```bash
# Start join service
./scripts/start-join-service.sh

# In another terminal, start main platform
python -m src.cli.main serve
```

Visit http://localhost:8001 for join service
Visit http://localhost:8000 for main platform

### Docker Mode

```bash
docker-compose up
```

## Production Deployment

### 1. DNS Setup
Add A record: `join.tilts.com -> [Your Server IP]`

### 2. SSL Certificate
```bash
sudo certbot certonly --nginx -d tilts.com -d join.tilts.com
```

### 3. Nginx Configuration
```bash
sudo cp nginx/tilts-join.conf /etc/nginx/sites-available/tilts
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Systemd Service
```bash
sudo cp systemd/tilts-join.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tilts-join
sudo systemctl start tilts-join
```

## API Integration

The join service communicates with the main platform via:

### PIN Validation Endpoint
```
GET /api/sessions/check-join-code/{pin}
```

Response:
```json
{
  "valid": true,
  "session_id": "sess_123",
  "session_name": "Friday AI Challenge",
  "status": "waiting",
  "player_count": 5,
  "max_players": 20
}
```

## User Flow

1. User visits join.tilts.com
2. Enters game PIN (e.g., "PLAY123")
3. Service validates PIN with main platform
4. On success, redirects to tilts.com/join/PLAY123
5. Main platform handles session joining

## Customization

### Branding
Edit the HTML in `src/api/join_service.py`:
- Logo text
- Colors
- Footer message

### Validation Rules
Modify PIN validation in `check_pin()`:
- Length requirements
- Character restrictions
- Custom validation logic

## Security

- HTTPS enforced via nginx
- CORS configured for main domain only
- Input sanitization for PINs
- No data storage (stateless service)
- Rate limiting recommended for production

## Monitoring

Check service health:
```bash
curl https://join.tilts.com/health
```

View logs:
```bash
sudo journalctl -u tilts-join -f
```

## Future Enhancements

1. **QR Code Support**: Generate QR codes for easy mobile joining
2. **Custom Themes**: Allow session creators to customize join page
3. **Analytics**: Track join attempts and success rates
4. **Caching**: Cache valid PINs for faster validation
5. **WebSocket**: Real-time validation without page reload