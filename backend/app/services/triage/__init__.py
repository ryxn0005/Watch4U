"""Rule-based fall-event triage service."""

from app.services.triage.triage_logic import run_triage

__all__ = ["run_triage"]
