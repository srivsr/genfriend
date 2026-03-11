from datetime import datetime, time, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

class CheckinScheduler:
    def __init__(self):
        self.scheduler = scheduler

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def schedule_user_checkins(self, user_id: str, checkin_time: time = time(9, 0)):
        job_id = f"daily_checkin_{user_id}"

        self.scheduler.add_job(
            self._trigger_daily_checkin,
            CronTrigger(hour=checkin_time.hour, minute=checkin_time.minute),
            id=job_id,
            replace_existing=True,
            args=[user_id]
        )

    async def _trigger_daily_checkin(self, user_id: str):
        from .triggers import CheckinTrigger
        trigger = CheckinTrigger()
        await trigger.daily_plan_checkin(user_id)

    async def schedule_one_time(self, user_id: str, checkin_type: str, scheduled_at: datetime, context: dict = None):
        job_id = f"{checkin_type}_{user_id}_{scheduled_at.timestamp()}"

        self.scheduler.add_job(
            self._trigger_checkin,
            "date",
            run_date=scheduled_at,
            id=job_id,
            args=[user_id, checkin_type, context]
        )

    async def _trigger_checkin(self, user_id: str, checkin_type: str, context: dict):
        from .triggers import CheckinTrigger
        trigger = CheckinTrigger()
        await trigger.trigger_checkin(user_id, checkin_type, context)

    def cancel_user_checkins(self, user_id: str):
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if user_id in job.id:
                job.remove()

checkin_scheduler = CheckinScheduler()
