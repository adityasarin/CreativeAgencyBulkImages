import threading
from typing import Optional

_lock = threading.Lock()
_active_campaign_id: Optional[str] = None
_stop_event: Optional[threading.Event] = None


def try_start(campaign_id: str) -> Optional[threading.Event]:
    """Claims the single process-wide generation slot.

    Returns a stop Event the caller must check, or None if a job
    (possibly orphaned from a previous session/reset) is already active.
    """
    global _active_campaign_id, _stop_event
    with _lock:
        if _active_campaign_id is not None:
            return None
        _active_campaign_id = campaign_id
        _stop_event = threading.Event()
        return _stop_event


def stop_active() -> None:
    with _lock:
        if _stop_event is not None:
            _stop_event.set()


def finish(campaign_id: str) -> None:
    global _active_campaign_id, _stop_event
    with _lock:
        if _active_campaign_id == campaign_id:
            _active_campaign_id = None
            _stop_event = None


def active_campaign_id() -> Optional[str]:
    with _lock:
        return _active_campaign_id
