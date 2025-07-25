export default function handler(req, res) {
  res.status(200).json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'tilts-frontend',
    version: process.env.VERCEL_GIT_COMMIT_SHA || '1.0.0'
  })
}