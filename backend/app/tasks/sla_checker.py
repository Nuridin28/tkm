from app.services.sla_service import sla_service
import asyncio


async def check_sla_periodically():
    while True:
        try:
            violations = await sla_service.check_sla_violations()
            if violations:
                print(f"Found {len(violations)} SLA violations")
        except Exception as e:
            print(f"SLA check error: {e}")

        await asyncio.sleep(60)

