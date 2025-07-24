# Join Service Deployment Guide

This guide explains how to deploy the join.tilts.com subdomain service.

## Overview

The join service provides a minimal, Kahoot-style interface for joining competitions using a game PIN. It runs as a separate service on port 8001 and is designed to be deployed on the join.tilts.com subdomain.

## Architecture

- **Main Platform**: tilts.com (port 8000)
- **Join Service**: join.tilts.com (port 8001)
- **Nginx**: Routes subdomains to appropriate services

## Deployment Steps

### 1. DNS Configuration

Add an A record for the subdomain:
```
join.tilts.com -> [Your Server IP]
```

### 2. SSL Certificate

Expand your existing certificate to include the subdomain:
```bash
sudo certbot certonly --nginx -d tilts.com -d www.tilts.com -d join.tilts.com
```

Or create a wildcard certificate:
```bash
sudo certbot certonly --nginx -d tilts.com -d *.tilts.com
```

### 3. Nginx Configuration

Copy the nginx configuration:
```bash
sudo cp nginx/tilts-join.conf /etc/nginx/sites-available/tilts
sudo ln -s /etc/nginx/sites-available/tilts /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Systemd Service

Install the join service:
```bash
sudo cp systemd/tilts-join.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tilts-join
sudo systemctl start tilts-join
```

### 5. Environment Variables

Create or update `.env` file:
```bash
MAIN_API_URL=https://tilts.com
ENV=production
```

### 6. Firewall Rules

Ensure port 8001 is only accessible locally:
```bash
# Block external access to 8001
sudo ufw deny 8001

# Allow nginx to proxy
sudo ufw allow 'Nginx Full'
```

## Testing

1. **Local Test**:
   ```bash
   ./scripts/start-join-service.sh
   ```
   Visit http://localhost:8001

2. **Production Test**:
   - Visit https://join.tilts.com
   - Enter a game PIN
   - Should redirect to https://tilts.com/join/{PIN}

## Docker Deployment

Alternatively, use Docker Compose:
```bash
docker-compose up -d
```

## Monitoring

Check service status:
```bash
sudo systemctl status tilts-join
sudo journalctl -u tilts-join -f
```

## Troubleshooting

1. **502 Bad Gateway**:
   - Check if join service is running
   - Verify port 8001 is correct
   - Check nginx error logs

2. **CORS Issues**:
   - Ensure main platform URL is in CORS allowed origins
   - Check browser console for specific errors

3. **PIN Validation Fails**:
   - Verify MAIN_API_URL environment variable
   - Check network connectivity between services
   - Ensure /api/sessions/check-join-code/{pin} endpoint exists

## Security Considerations

1. **Rate Limiting**: Add rate limiting to prevent PIN guessing
2. **Input Validation**: PINs are validated for length and format
3. **HTTPS Only**: All traffic is encrypted
4. **No Data Storage**: Join service doesn't store any data

## Future Enhancements

1. **Caching**: Cache valid PINs for faster validation
2. **Analytics**: Track join attempts and success rates
3. **Custom Branding**: Allow session creators to customize join page
4. **QR Codes**: Generate QR codes for easy mobile joining