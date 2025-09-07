from app.models.webhook_model import WebhookEvent
from pydantic import ValidationError

def validate_webhook_data(data):
    try:
        WebhookEvent(**data)
        return True, None
    except ValidationError as e:
        # Devuelve False con los errores de validación formateados
        return False, e.errors()
