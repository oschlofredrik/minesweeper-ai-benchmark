# Deploying Join Service to Render

This guide explains how to deploy the join.tilts.com service as a separate Render instance.

## Why Separate Instance?

- **Independent Scaling**: Scale join service separately from main platform
- **Isolation**: Issues with one service don't affect the other
- **Cost Efficiency**: Can use free tier for lightweight join service
- **Custom Domain**: Easy to map join.tilts.com to dedicated service

## Prerequisites

1. Render account with main Tilts platform already deployed
2. Access to DNS settings for tilts.com domain
3. GitHub repository access

## Deployment Steps

### 1. Create New Render Service

#### Option A: Using Render Dashboard

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repo (oschlofredrik/tilts)
4. Configure:
   - **Name**: `tilts-join`
   - **Region**: Same as main service (oregon)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements-render.txt`
   - **Start Command**: `python -m uvicorn src.api.join_service:app --host 0.0.0.0 --port $PORT`

#### Option B: Using render-join.yaml

1. In Render Dashboard, click "New +" → "Blueprint"
2. Connect to your GitHub repo
3. Select `render-join.yaml` as the blueprint file
4. Deploy

### 2. Configure Environment Variables

In the Render service settings, add:

```
PYTHONPATH=/opt/render/project/src
MAIN_API_URL=https://minesweeper-ai-benchmark.onrender.com
ENV=production
```

**Important**: Update `MAIN_API_URL` to your actual main platform URL!

### 3. Set Up Custom Domain

1. In Render service settings, go to "Custom Domains"
2. Add `join.tilts.com`
3. Render will provide a CNAME target like: `tilts-join.onrender.com`

### 4. Configure DNS

In your DNS provider:

```
Type: CNAME
Name: join
Value: tilts-join.onrender.com  (use value from Render)
TTL: 3600
```

Or if using A record:
```
Type: A
Name: join
Value: [Render IP address]
TTL: 3600
```

### 5. Update Main Platform CORS

Add the join service URL to CORS in main platform:

1. Go to main Render service
2. Add environment variable:
   ```
   CORS_ORIGINS=https://join.tilts.com,https://tilts-join.onrender.com
   ```

Or update in code if hardcoded.

## Verification

1. **Health Check**: 
   ```bash
   curl https://tilts-join.onrender.com/health
   ```

2. **Custom Domain**:
   ```bash
   curl https://join.tilts.com/health
   ```

3. **Test Flow**:
   - Visit https://join.tilts.com
   - Enter a test PIN
   - Should validate and redirect to main platform

## Cost Considerations

### Free Tier (Recommended for Start)
- 512 MB RAM
- 0.1 CPU
- Spins down after 15 min inactivity
- Perfect for join service

### Paid Tier ($7/month)
- Always on
- Better performance
- Custom SSL certificates

## Monitoring

1. **Render Dashboard**:
   - View logs
   - Monitor metrics
   - Set up alerts

2. **Custom Monitoring**:
   ```bash
   # Simple uptime check
   while true; do
     curl -s https://join.tilts.com/health || echo "Service down"
     sleep 300
   done
   ```

## Troubleshooting

### Service Won't Start
- Check logs in Render dashboard
- Verify start command
- Ensure all imports are available

### CORS Errors
- Update MAIN_API_URL to not include /api suffix
- Add join service URL to main platform CORS

### DNS Not Working
- Wait 24-48 hours for propagation
- Use `nslookup join.tilts.com` to verify
- Check CNAME is pointing to correct Render URL

### PIN Validation Fails
- Verify MAIN_API_URL is correct
- Check main platform has check-join-code endpoint
- Look at network tab in browser for errors

## Architecture

```
User -> join.tilts.com -> Render Join Service (Port $PORT)
                                    |
                                    v
                          MAIN_API_URL/api/sessions/check-join-code/{pin}
                                    |
                                    v
                          Redirect to tilts.com/join/{pin}
```

## Next Steps

1. Set up monitoring alerts in Render
2. Add custom favicon/branding
3. Implement caching for validated PINs
4. Add analytics tracking
5. Create A/B tests for join flow

## Rollback Plan

If issues arise:

1. Update DNS to point join.tilts.com → tilts.com
2. Add redirect rule in main platform:
   ```python
   @app.get("/join")
   def redirect_join():
       return RedirectResponse("/")
   ```
3. Debug and fix join service offline
4. Restore DNS when ready