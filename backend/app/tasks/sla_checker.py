"""
SLA Checker Task - Background task for SLA monitoring
"""
from app.services.sla_service import sla_service
import asyncio


async def check_sla_periodically():
    """Periodic SLA check (run every minute)"""
    while True:
        try:
            violations = await sla_service.check_sla_violations()
            if violations:
                print(f"Found {len(violations)} SLA violations")
                # In production, send notifications here
        except Exception as e:
            print(f"SLA check error: {e}")
        
        await asyncio.sleep(60)  # Check every minute

