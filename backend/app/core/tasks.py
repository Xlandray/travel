import asyncio
import logging

from app.db.session import AsyncSessionLocal
from app.services.cleanup_service import release_expired_bookings

logger = logging.getLogger(__name__)


async def start_booking_sweeper(interval_seconds: int = 60) -> None:
    """Her interval_seconds saniyede bir supurme islemini tetikler."""
    logger.info(f"Booking sweeper background task started (interval: {interval_seconds}s).")
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            async with AsyncSessionLocal() as db:
                count = await release_expired_bookings(db)
                if count > 0:
                    logger.info(f"Booking sweeper cleared {count} expired booking(s).")
        except asyncio.CancelledError:
            logger.info("Booking sweeper task cancelled.")
            break
        except Exception as e:
            logger.error(f"Supurucu hatasi: {e}", exc_info=True)
