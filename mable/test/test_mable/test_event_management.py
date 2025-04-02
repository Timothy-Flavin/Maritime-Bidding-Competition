"""
Tests for management module.
"""

import mable.event_management as em


class TestEventQueue:

    def test_queue(self):
        event_1 = em.Event(1, "Load")
        event_2 = em.Event(5, "Unload")
        event_3 = em.Event(3, "New Cargo")
        events = em.EventQueue()
        events.put(event_1)
        events.put(event_2)
        events.put(event_3)
        return_event_1 = events.get()
        assert return_event_1.time == 1
        assert return_event_1.info == "Load"
        return_event_2 = events.get()
        assert return_event_2.time == 3
        assert return_event_2.info == "New Cargo"
        return_event_3 = events.get()
        assert return_event_3.time == 5
        assert return_event_3.info == "Unload"
