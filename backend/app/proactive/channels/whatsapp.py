import httpx
from app.config import settings

class WhatsAppChannel:
    def __init__(self):
        self.api_url = "https://graph.facebook.com/v17.0"
        self.phone_number_id = getattr(settings, "whatsapp_phone_number_id", None)
        self.access_token = getattr(settings, "whatsapp_access_token", None)

    async def send_message(self, to_phone: str, message: str) -> bool:
        if not self.phone_number_id or not self.access_token:
            print(f"[WhatsApp] Would send to {to_phone}: {message[:50]}...")
            return True

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": message}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/{self.phone_number_id}/messages",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=payload
                )
            return response.status_code == 200
        except Exception as e:
            print(f"[WhatsApp] Error sending message: {e}")
            return False

    async def handle_incoming(self, webhook_data: dict):
        try:
            message = webhook_data["entry"][0]["changes"][0]["value"]["messages"][0]
            from_phone = message["from"]
            text = message["text"]["body"]

            user = await self._get_user_by_phone(from_phone)
            if not user:
                return

            from app.mentor import mentor_engine
            response = await mentor_engine.process(
                user_id=str(user.get("id")),
                message=text,
                channel="whatsapp"
            )

            await self.send_message(from_phone, response.content)

        except (KeyError, IndexError) as e:
            print(f"[WhatsApp] Error parsing webhook: {e}")

    async def _get_user_by_phone(self, phone: str) -> dict:
        return None

whatsapp_channel = WhatsAppChannel()
