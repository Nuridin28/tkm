from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.core.database import get_supabase_admin
from app.models.schemas import TicketStatus


class SLAService:

    def __init__(self):
        self.supabase = get_supabase_admin()

    async def check_sla_violations(self) -> List[Dict[str, Any]]:
        violations = []
        now = datetime.utcnow()

        tickets_result = self.supabase.table("tickets").select("*").lte("sla_accept_deadline", now.isoformat()).eq("status", TicketStatus.NEW.value).execute()

        tickets = tickets_result.data if tickets_result.data else []

        for ticket in tickets:
            await self._escalate_ticket(ticket["id"], "SLA accept deadline passed")
            violations.append({
                "ticket_id": ticket["id"],
                "violation_type": "accept_deadline",
                "deadline": ticket["sla_accept_deadline"]
            })

        remote_tickets_result = self.supabase.table("tickets").select("*").lte("sla_remote_deadline", now.isoformat()).in_("status", [TicketStatus.ACCEPTED.value, TicketStatus.IN_PROGRESS.value]).execute()

        remote_tickets = remote_tickets_result.data if remote_tickets_result.data else []

        for ticket in remote_tickets:
            await self._flag_for_on_site(ticket["id"])
            violations.append({
                "ticket_id": ticket["id"],
                "violation_type": "remote_deadline",
                "deadline": ticket["sla_remote_deadline"]
            })

        return violations

    async def _escalate_ticket(self, ticket_id: str, reason: str):
        update_data = {
            "status": TicketStatus.ESCALATED.value,
            "updated_at": datetime.utcnow().isoformat()
        }

        self.supabase.table("tickets").update(update_data).eq("id", ticket_id).execute()

        self._log_ticket_history(ticket_id, "status", TicketStatus.IN_PROGRESS.value, TicketStatus.ESCALATED.value, reason)

    async def _flag_for_on_site(self, ticket_id: str):
        update_data = {
            "need_on_site": True,
            "status": TicketStatus.ON_SITE.value,
            "updated_at": datetime.utcnow().isoformat()
        }

        self.supabase.table("tickets").update(update_data).eq("id", ticket_id).execute()

    def _log_ticket_history(self, ticket_id: str, field_name: str, old_value: str, new_value: str, changed_by: str = "system"):
        history_data = {
            "ticket_id": ticket_id,
            "field_name": field_name,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "changed_by": None,
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            self.supabase.table("ticket_history").insert(history_data).execute()
        except Exception as e:
            print(f"Failed to log ticket history: {e}")


sla_service = SLAService()

