import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from src.domain.scan_job import ScanJob
from src.infrastructure.storage import Storage

logger = logging.getLogger(__name__)

class ScanScheduler:
    def __init__(self, storage: Storage, scan_func, schedule: str = None):
        self.storage = storage
        self.scan_func = scan_func
        self.schedule = schedule or "0 8 * * *"  # default: daily at 8:00 UTC
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    def start(self):
        """Запускає планувальник."""
        if self._is_running:
            logger.warning("Scheduler already running")
            return

        # Визначаємо тригер залежно від формату
        if self.schedule.isdigit():
            # Інтервал у хвилинах
            trigger = IntervalTrigger(minutes=int(self.schedule))
            logger.info(f"Scheduler: interval {self.schedule} minutes")
        else:
            # Cron-вираз
            trigger = CronTrigger.from_crontab(self.schedule)
            logger.info(f"Scheduler: cron {self.schedule}")

        self.scheduler.add_job(
            self._run_scan,
            trigger=trigger,
            id="scheduled_scan",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300
        )
        self.scheduler.start()
        self._is_running = True
        logger.info("✅ Scheduler started")

    def stop(self):
        """Зупиняє планувальник."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Scheduler stopped")

    async def _run_scan(self):
        """Запускає сканування, якщо попереднє завершено."""
        # Перевіряємо, чи не виконується сканування
        latest = await self.storage.get_latest_scan_job()
        if latest and latest["status"] == "running":
            logger.info("Skipping scheduled scan: previous scan still running")
            return

        logger.info("🔄 Scheduled scan started")
        try:
            await self.scan_func(self.storage)
            logger.info("✅ Scheduled scan completed")
        except Exception as e:
            logger.error(f"❌ Scheduled scan failed: {e}")
