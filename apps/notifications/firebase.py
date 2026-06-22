# apps/notifications/firebase.py
import firebase_admin
from firebase_admin import credentials, messaging

if not firebase_admin._apps:
    cred = credentials.Certificate('notificacionpush-9000d-firebase-adminsdk-fbsvc-1d2083e78c.json')  # ← aquí
    firebase_admin.initialize_app(cred)

def send_push(token: str, title: str, body: str, data: dict = None):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=token,
    )
    messaging.send(message)