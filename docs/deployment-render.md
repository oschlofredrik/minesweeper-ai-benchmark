# Deploying to Render

This guide walks you through deploying Tilts to Render.

## Prerequisites

1. A [Render account](https://render.com/)
2. Your OpenAI and Anthropic API keys
3. A GitHub account with this repository forked or cloned

## Deployment Steps

### 1. Prepare Your Repository

First, ensure your repository is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create a New Web Service on Render

1. Log in to your [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" and select "Web Service"
3. Connect your GitHub account if not already connected
4. Select your `tilts` repository
5. Configure the service:
   - **Name**: `tilts` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements-render.txt`
   - **Start Command**: `python scripts/start_web.py`
   - **Instance Type**: Free (or upgrade for production)

### 3. Configure Environment Variables

In the Render dashboard for your service, go to "Environment" and add:

#### Required Variables
```
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
PYTHON_VERSION=3.11
```

#### Optional Variables
```
JUDGE_MODEL=gpt-4o
JUDGE_TEMPERATURE=0.3
ENVIRONMENT=production
LOG_LEVEL=info
SECRET_KEY=your-random-secret-key
```

### 4. Set Up Database (Optional)

For persistent storage of results:

1. In Render Dashboard, click "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `tilts-db`
   - **Database**: `tilts`
   - **User**: `tilts_user`
   - **Region**: Same as your web service
   - **Instance Type**: Free (or upgrade for production)
3. Once created, Render will automatically add the `DATABASE_URL` to your web service

### 5. Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Start the web server
3. Wait for the build to complete (usually 5-10 minutes)

### 6. Initialize Database (If Using)

After deployment, run the database initialization:

1. Go to your web service in Render
2. Click on "Shell" tab
3. Run: `python scripts/init_db.py`

### 7. Access Your Application

Once deployed, your application will be available at:
- `https://your-service-name.onrender.com`

Test the deployment:
- Visit the home page
- Check `/health` endpoint
- Try `/api/leaderboard`
- View API docs at `/docs`

## Using the Deployed Service

### Web Interface

Access the leaderboard and statistics at your Render URL.

### API Access

Use the API endpoints programmatically:

```python
import requests

# Get leaderboard
response = requests.get("https://your-app.onrender.com/api/leaderboard")
leaderboard = response.json()

# Get model results
response = requests.get("https://your-app.onrender.com/api/models/gpt-4/results")
results = response.json()
```

### Running Evaluations

You can still run evaluations locally and have them appear on the hosted leaderboard:

```bash
# Set your Render API endpoint
export BENCHMARK_API_URL=https://your-app.onrender.com

# Run evaluation locally
python -m src.cli.main evaluate --model gpt-4 --num-games 10

# Results will be sent to your Render instance
```

## Configuration Options

### Scaling

For production use, consider:

1. **Upgrade Instance Type**: Use Standard or Performance instances
2. **Enable Auto-Scaling**: Configure min/max instances
3. **Add Redis**: For caching frequently accessed data
4. **Configure Health Checks**: Ensure high availability

### Security

1. **API Rate Limiting**: Add rate limiting middleware
2. **CORS Configuration**: Restrict allowed origins
3. **Authentication**: Add API key authentication for write operations
4. **HTTPS**: Automatically provided by Render

### Monitoring

1. **Render Metrics**: Built-in CPU, memory, and request metrics
2. **Custom Logging**: Logs available in Render dashboard
3. **External Monitoring**: Integrate with services like Sentry

## Troubleshooting

### Build Failures

If the build fails:
1. Check the build logs in Render dashboard
2. Ensure all dependencies are in `requirements-render.txt`
3. Verify Python version compatibility

### Application Errors

If the app crashes:
1. Check the service logs
2. Verify environment variables are set correctly
3. Test locally with same environment variables

### Database Connection Issues

If database errors occur:
1. Verify `DATABASE_URL` is set
2. Check database is running
3. Run database initialization script

### Performance Issues

If the app is slow:
1. Check instance metrics
2. Consider upgrading instance type
3. Enable caching with Redis
4. Optimize database queries

## Cost Considerations

### Free Tier
- 1 web service with 512MB RAM
- 1 PostgreSQL database with 1GB storage
- 750 hours/month (sleeps after 15 min inactivity)

### Paid Plans
- Standard: $7/month per service
- Performance: Higher specs available
- Database: Scales with storage needs

## Maintenance

### Updating the Application

1. Push changes to GitHub
2. Render automatically redeploys
3. Monitor deployment in dashboard

### Database Migrations

1. Create migration scripts
2. Run via Render Shell
3. Test in staging first

### Backup Strategy

1. Use Render's database backups
2. Export results regularly
3. Store evaluations locally

## Advanced Deployment

### Custom Domain

1. Add custom domain in Render settings
2. Configure DNS records
3. SSL automatically provisioned

### CI/CD Pipeline

1. Set up GitHub Actions
2. Run tests before deployment
3. Deploy only on successful tests

### Multi-Region Deployment

1. Deploy to multiple Render regions
2. Use load balancer
3. Configure geo-routing

## Support

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com/)
- [Project Issues](https://github.com/your-username/tilts/issues)