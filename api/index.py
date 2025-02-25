from mangum import Mangum
from app.main import app

# Vercel serverless handler
handler = Mangum(app)
