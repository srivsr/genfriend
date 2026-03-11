class PushChannel:
    async def send_notification(self, user_id: str, title: str, body: str, data: dict = None) -> bool:
        print(f"[Push] Would send to {user_id}: {title} - {body[:50]}...")
        return True

    async def send_batch(self, user_ids: list[str], title: str, body: str) -> dict:
        results = {}
        for user_id in user_ids:
            results[user_id] = await self.send_notification(user_id, title, body)
        return results

push_channel = PushChannel()
