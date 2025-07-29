# rezzy_app/backend/app.py

from fastapi import FastAPI
from backend import payments, webhook

app = FastAPI()

app.include_router(payments.router, prefix="/api/payments")
app.include_router(webhook.router, prefix="/api/webhook")
