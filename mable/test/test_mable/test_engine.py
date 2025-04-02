"""
Tests for engine module.
"""

import mable.engine as sim_engine
from mable.event_management import EventObserver, Event


class DummyObserver(EventObserver):

    def __init__(self):
        self.observations = []

    def notify(self, engine, event, data):
        self.observations.append((event, data))


class TestSimulationEngine:

    def test_observer(self):
        test_engine = sim_engine.SimulationEngine(None, None, None, None, None)
        test_observer = DummyObserver()
        test_engine.register_event_observer(test_observer)
        test_engine.notify_event_observer(Event(1, "A"), "B")
        test_engine.unregister_event_observer(test_observer)
        test_engine.notify_event_observer(Event(2, "X"), "Y")
        assert len(test_observer.observations) == 1
        assert isinstance(test_observer.observations[0][0], Event)
        assert test_observer.observations[0][0].time == 1
        assert test_observer.observations[0][0].info == "A"
        assert test_observer.observations[0][1] == "B"
