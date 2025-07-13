# Render Deployment Checklist

## Quick Deploy to Render

### 1. Prerequisites
- [ ] Render account created
- [ ] GitHub repository ready
- [ ] OpenAI API key obtained
- [ ] Anthropic API key obtained

### 2. Deploy via Render Dashboard

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect GitHub account
   - Select your repository
   
3. **Configure Service**:
   ```
   Name: minesweeper-benchmark
   Environment: Python 3
   Build Command: pip install -r requirements-render.txt
   Start Command: python scripts/start_web.py
   ```

4. **Add Environment Variables**:
   ```
   OPENAI_API_KEY=<your-key>
   ANTHROPIC_API_KEY=<your-key>
   PYTHON_VERSION=3.11
   ```

5. **Click "Create Web Service"**

### 3. Verify Deployment

Once deployed (usually 5-10 minutes), check:

- [ ] Visit `https://your-app.onrender.com/`
- [ ] Check health: `https://your-app.onrender.com/health`
- [ ] View API docs: `https://your-app.onrender.com/docs`
- [ ] Test leaderboard: `https://your-app.onrender.com/api/leaderboard`

### 4. Optional: Database Setup

If you want persistent storage:

1. **Create PostgreSQL Database**:
   - In Render: New + → PostgreSQL
   - Name: minesweeper-db
   - This auto-connects to your web service

2. **Initialize Database**:
   - Go to Web Service → Shell
   - Run: `python scripts/init_db.py`

### 5. Run Evaluations

After deployment, you can:

1. **Use the Web Interface**: Visit your Render URL
2. **Run Locally**: Results will show on the hosted leaderboard
3. **Use the API**: Integrate with your applications

## Troubleshooting

### If deployment fails:
1. Check build logs in Render dashboard
2. Verify all files are committed to Git
3. Ensure environment variables are set

### If app doesn't load:
1. Check service logs
2. Verify `/health` endpoint
3. Check API keys are valid

### Common Issues:
- **Module not found**: Check requirements-render.txt
- **Port error**: Ensure using $PORT environment variable
- **API errors**: Verify API keys in environment variables

## Next Steps

1. **Custom Domain**: Add in Render settings
2. **Monitoring**: Set up alerts
3. **Scaling**: Upgrade instance type for production
4. **Security**: Add rate limiting and authentication

## Support

- Render Docs: https://render.com/docs
- Project Issues: Create issue on GitHub
- Render Community: https://community.render.com/