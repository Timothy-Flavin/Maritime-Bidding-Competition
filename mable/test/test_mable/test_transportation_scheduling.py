"""
Tests for STN module.
"""

import copy
import pytest

import numpy as np

from mable.engine import SimulationEngine
from mable.event_management import ArrivalEvent, CargoTransferEvent, IdleEvent, TravelEvent, EventQueue, \
    EventObserver
from mable.simulation_environment import World
from mable.extensions.cargo_distributions import TimeWindowTrade
from mable.extensions.fuel_emissions import VesselWithEngine, VesselEngine, Fuel, ConsumptionRate
from mable.transportation_scheduling import (Schedule, TransportationStartFinishIndicator,
                                             TransportationSourceDestinationIndicator)
from mable.transport_operation import CargoCapacity, ShippingCompany

FUEL_MFO = Fuel(name="MFO", price=430, energy_coefficient=40, co2_coefficient=3.16)
LADEN_CONSUMPTION_RATE = ConsumptionRate(base=0.5503,
                                         speed_power=2.19201,
                                         factor=1 / 24)
BALLAST_CONSUMPTION_RATE = ConsumptionRate(base=0.1493,
                                           speed_power=2.3268,
                                           factor=1 / 24)
VESSEL = VesselWithEngine(
    [CargoCapacity("Oil", capacity=300000, loading_rate=5)], "Aberdeen-f8ea5ddd09c3",
                          speed=1,
                          propelling_engine=VesselEngine(FUEL_MFO, idle_consumption=7.13/24,
                                                         laden_consumption_rate=LADEN_CONSUMPTION_RATE,
                                                         ballast_consumption_rate=BALLAST_CONSUMPTION_RATE,
                                                         loading_consumption=15.53/24,
                                                         unloading_consumption=134.37/24),
                          name="HMS Terror")
DUMMY_TRADE = TimeWindowTrade(origin_port="A", destination_port="B", amount=10, cargo_type="Oil")


class DummyWorld(World):

    def __init__(self, distances=None, event_queue=None):
        super().__init__(self, event_queue, None)
        if distances is None:
            self._distances = {}
        else:
            self._distances = distances

    def get_distance(self, location_one, location_two):
        distance = 0
        locations_key = (location_one, location_two)
        locations_key_reverse = (location_two, location_one)
        if locations_key in self._distances:
            distance = self._distances[locations_key]
        elif locations_key_reverse in self._distances:
            distance = self._distances[locations_key_reverse]
        return distance

    @staticmethod
    def get_vessel_location(vessel, current_time):
        return vessel.location

    @staticmethod
    def get_port_or_default(name, default=None):
        return name


class DummyClassFactory:

    @staticmethod
    def generate_event_arrival(*args, **kwargs):
        return ArrivalEvent(*args, **kwargs)

    @staticmethod
    def generate_event_cargo_transfer(*args, **kwargs):
        return CargoTransferEvent(*args, **kwargs)

    @staticmethod
    def generate_event_idling(*args, **kwargs):
        return IdleEvent(*args, **kwargs)

    @staticmethod
    def generate_event_travel(*args, **kwargs):
        return TravelEvent(*args, **kwargs)


class DummyEngine(SimulationEngine):
    def __init__(self, world, class_factory=None):
        super().__init__(world, None, None, None, class_factory)

    def find_company_for_vessel(self, vessel):
        return ShippingCompany([], "TestCompany")


class StorageObserver(EventObserver):

    def __init__(self):
        self._observed_events = []

    def notify(self, engine, event, data):
        self._observed_events.append(event)


class TestSchedule:

    def test__get_distance_matrix(self):
        schedule = Schedule(VESSEL)
        distances = {
            ("A", "B"): 10,
            ("Aberdeen-f8ea5ddd09c3", "A"): 15
        }
        schedule.set_engine(DummyEngine(DummyWorld(distances)))
        schedule.add_transportation(DUMMY_TRADE, 1)
        distance_matrix = schedule._get_distance_matrix()
        assert distance_matrix.shape == (5, 5)
        assert -2 in distance_matrix
        assert -10 in distance_matrix
        assert np.inf in distance_matrix

    def test_shift_task_push(self):
        schedule = Schedule(VESSEL)
        schedule.set_engine(DummyEngine(DummyWorld()))
        schedule.add_transportation(DUMMY_TRADE, 1)
        schedule._shift_task_push(1)
        schedule._shift_task_push(3)
        for i in [2, 4]:
            assert (i, TransportationSourceDestinationIndicator.PICK_UP) in schedule._stn
            assert (i, TransportationSourceDestinationIndicator.DROP_OFF) in schedule._stn
        schedule._shift_task_push(4, False)
        schedule._shift_task_push(3, False)
        for i in [1, 2]:
            assert (i, TransportationSourceDestinationIndicator.PICK_UP) in schedule._stn
            assert (i, TransportationSourceDestinationIndicator.DROP_OFF) in schedule._stn

    def test_shift_task_pull(self):
        schedule = Schedule(VESSEL)
        schedule.set_engine(DummyEngine(DummyWorld()))
        schedule.add_transportation(DUMMY_TRADE, 1)
        schedule._shift_task_pull(2)
        for i in [2, 3]:
            assert (i, TransportationSourceDestinationIndicator.PICK_UP) in schedule._stn
            assert (i, TransportationSourceDestinationIndicator.DROP_OFF) in schedule._stn
        schedule._shift_task_pull(2, False)
        for i in [1, 2]:
            assert (i, TransportationSourceDestinationIndicator.PICK_UP) in schedule._stn
            assert (i, TransportationSourceDestinationIndicator.DROP_OFF) in schedule._stn

    def test_number_tasks(self):
        schedule = Schedule(VESSEL)
        schedule.set_engine(DummyEngine(DummyWorld(), DummyClassFactory()))
        assert schedule._number_tasks == 0
        schedule.add_transportation(DUMMY_TRADE, 1)
        assert schedule._number_tasks == 2
        schedule.add_transportation(DUMMY_TRADE, 1)
        assert schedule._number_tasks == 4
        schedule.pop()  # Travel
        assert schedule._number_tasks == 4
        schedule.pop()  # Arrival and ready for cargo transfer
        assert schedule._number_tasks == 4
        schedule.pop()  # Cargo transfer started
        assert schedule._number_tasks == 3

    def test_add_task(self):
        pass  # TODO Write test

    def test_verify_schedule(self):
        distances = {
            ("A", "B"): 10,
            ("A", "C"): 25,
            ("B", "C"): 20,
            ("C", "D"): 15,
            ("D", "A"): 20,
            ("D", "B"): 30
        }
        trade_1 = TimeWindowTrade(origin_port="A", destination_port="B", amount=10,
                                  cargo_type="Oil")
        trade_2 = TimeWindowTrade(origin_port="C", destination_port="D", amount=10,
                                  time_window=[None, 25, None, None],
                                  cargo_type="Oil")
        trade_3 = TimeWindowTrade(origin_port="A", destination_port="B", amount=10,
                                  time_window=[None, None, None, 5],
                                  cargo_type="Oil")
        trade_4 = TimeWindowTrade(origin_port="C", destination_port="D", amount=10,
                                  time_window=[5, None, None, None],
                                  cargo_type="Oil")
        trade_5 = TimeWindowTrade(origin_port="A", destination_port="B", amount=10,
                                  time_window=[None, 2, None, None],
                                  cargo_type="Oil")
        trade_6 = TimeWindowTrade(origin_port="A", destination_port="C", amount=10,
                                  cargo_type="Oil")
        trade_7 = TimeWindowTrade(origin_port="B", destination_port="D", amount=10,
                                  time_window=[None, None, None, 51],
                                  cargo_type="Oil")
        trade_8 = TimeWindowTrade(origin_port="A", destination_port="A", amount=VESSEL.capacity("Oil") + 1,
                                  cargo_type="Oil")
        schedule_valid_1 = Schedule(VESSEL)
        schedule_valid_1.set_engine(DummyEngine(DummyWorld(distances)))
        schedule_valid_1.add_transportation(trade_2, 1)
        schedule_valid_1.add_transportation(trade_1, 3)
        assert schedule_valid_1.verify_schedule() is True
        schedule_valid_2 = Schedule(VESSEL)
        schedule_valid_2.set_engine(DummyEngine(DummyWorld(distances)))
        schedule_valid_2.add_transportation(trade_5, 1)
        schedule_valid_2.add_transportation(trade_4, 3)
        assert schedule_valid_2.verify_schedule() is True
        schedule_valid_3 = Schedule(VESSEL)
        schedule_valid_3.set_engine(DummyEngine(DummyWorld(distances)))
        schedule_valid_3.add_transportation(trade_6, 1)
        schedule_valid_3.add_transportation(trade_7, 2, 3)
        assert schedule_valid_3.verify_schedule() is True
        # Invalid schedules
        schedule_invalid_0 = Schedule(VESSEL)
        schedule_invalid_0.set_engine(DummyEngine(DummyWorld(distances)))
        schedule_invalid_0.add_transportation(trade_3, 1)
        assert schedule_invalid_0.verify_schedule() is False
        schedule_invalid_1 = Schedule(VESSEL)
        schedule_invalid_1.set_engine(DummyEngine(DummyWorld(distances)))
        schedule_invalid_1.add_transportation(trade_1, 1)
        schedule_invalid_1.add_transportation(trade_2, 3)
        assert schedule_invalid_1.verify_schedule() is False
        schedule_invalid_2 = Schedule(VESSEL)
        schedule_invalid_2.set_engine(DummyEngine(DummyWorld(distances)))
        schedule_invalid_2.add_transportation(trade_4, 1)
        schedule_invalid_2.add_transportation(trade_5, 3)
        assert schedule_invalid_2.verify_schedule() is False
        schedule_invalid_3 = Schedule(VESSEL)
        schedule_invalid_3.set_engine(DummyEngine(DummyWorld(distances)))
        schedule_invalid_3.add_transportation(trade_6, 1)
        schedule_invalid_3.add_transportation(trade_7, 3)
        assert schedule_invalid_3.verify_schedule() is False
        # Invalid cargo amount
        schedule_invalid_4 = Schedule(VESSEL)
        schedule_invalid_4.set_engine(DummyEngine(DummyWorld(distances)))
        schedule_invalid_4.add_transportation(trade_8, 1)
        assert schedule_invalid_4.verify_schedule() is False
        schedule_invalid_5 = Schedule(VESSEL)
        schedule_invalid_5.set_engine(DummyEngine(DummyWorld(distances)))
        schedule_invalid_5._add_task(1, trade_8, TransportationSourceDestinationIndicator.DROP_OFF, 0)
        schedule_invalid_5._add_task(2, trade_8, TransportationSourceDestinationIndicator.PICK_UP, 0)
        assert schedule_invalid_5.verify_schedule() is False

    @staticmethod
    def get_pop_setup(setting):
        distances = {
            ("A", "B"): 10,
            ("B", "C"): 10,
            ("C", "D"): 10,
            ("D", "E"): 10,
            ("D", "F"): 20,
            ("E", "F"): 10,
            ("F", "G"): 10
        }
        trade_1 = TimeWindowTrade(origin_port="A", destination_port="B", amount=10,
                                  cargo_type="Oil")
        trade_2 = TimeWindowTrade(origin_port="C", destination_port="D", amount=10,
                                  cargo_type="Oil")
        trade_3 = TimeWindowTrade(origin_port="D", destination_port="E", amount=10,
                                  cargo_type="Oil",
                                  time_window=setting[0])
        trade_4 = TimeWindowTrade(origin_port="F", destination_port="G", amount=10,
                                  cargo_type="Oil",
                                  time_window=setting[1])
        vessel = copy.deepcopy(VESSEL)
        vessel.location = "A"
        schedule = Schedule(vessel)
        schedule.set_engine(DummyEngine(DummyWorld(distances), DummyClassFactory()))
        return trade_1, trade_2, trade_3, trade_4, vessel, schedule

    def test_add_transportation(self):
        schedule = Schedule(VESSEL)
        schedule.set_engine(DummyEngine(DummyWorld()))
        schedule.add_transportation(DUMMY_TRADE, 1)
        assert len(schedule._stn) == 5
        for i, location_type in zip(
                [1, 2],
                [TransportationSourceDestinationIndicator.PICK_UP, TransportationSourceDestinationIndicator.DROP_OFF]
        ):
            assert schedule._stn.nodes[(i, TransportationStartFinishIndicator.START)]["location_type"] == location_type
            assert schedule._stn.nodes[(i, TransportationStartFinishIndicator.START)]["trade"] is DUMMY_TRADE
            assert schedule._stn.nodes[(i, TransportationStartFinishIndicator.FINISH)]["location_type"] == location_type
            assert schedule._stn.nodes[(i, TransportationStartFinishIndicator.FINISH)]["trade"] is DUMMY_TRADE

    # TODO test schedule length with waiting times has_time_window_constraints = True
    @pytest.mark.parametrize("setting", [
                                              ([None, None, None, None],      [None, None, None, None],
                                               [12, 12, 14,
                                                24, 24, 26,
                                                36, 36, 38,
                                                38, 40,
                                                50, 50, 52,
                                                62, 62, 64,
                                                74, 74, 76],
                                               [TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent],
                                               False),
                                              ([None, 38, None, None],      [None, None, None, None],
                                               [12, 12, 14,
                                                24, 24, 26,
                                                36, 36, 38,
                                                38, 40,
                                                50, 50, 52,
                                                62, 62, 64,
                                                74, 74, 76],
                                               [TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent],
                                               False),
                                              ([38, None, None, None],      [None, None, None, None],
                                               [12, 12, 14,
                                                24, 24, 26,
                                                36, 36, 38,
                                                38, 40,
                                                50, 50, 52,
                                                62, 62, 64,
                                                74, 74, 76],
                                               [TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent],
                                               False),
                                              ([38, 38, None, None],      [None, None, None, None],
                                               [12, 12, 14,
                                                24, 24, 26,
                                                36, 36, 38,
                                                38, 40,
                                                50, 50, 52,
                                                62, 62, 64,
                                                74, 74, 76],
                                               [TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent],
                                               False),
                                              ([38 + 1, None, None, None],      [None, None, None, None],
                                               [12, 12, 14,
                                                24, 24, 26,
                                                36, 36, 38,
                                                38 + 1, 39, 41,
                                                51, 51, 53,
                                                63, 63, 65,
                                                75, 75, 77],
                                               [TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                IdleEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent],
                                               True),
                                              ([None, None, None, None], [None, 62, None, None],
                                               [12, 12, 14,
                                                24, 24, 26,
                                                36, 36, 38,
                                                38, 40,
                                                50, 50, 52,
                                                62, 62, 64,
                                                74, 74, 76],
                                               [TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent],
                                               False),
                                              ([None, None, None, None], [65, 65, None, None],
                                               [12, 12, 14,
                                                24, 24, 26,
                                                36, 36, 38,
                                                38, 40,
                                                50, 50, 52,
                                                62, 65, 65, 67,
                                                77, 77, 79],
                                               [TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, IdleEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent],
                                               True),
                                              ([None, None, 55, None], [None, 67, 82, 82],
                                               [12, 12, 14,
                                                24, 24, 26,
                                                36, 36, 38,
                                                38, 40,
                                                50, 55, 55, 57,
                                                67, 67, 69,
                                                79, 82, 82, 84],
                                               [TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, IdleEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, ArrivalEvent, CargoTransferEvent,
                                                TravelEvent, IdleEvent, ArrivalEvent, CargoTransferEvent],
                                               True),
                            ])
    def test_pop_sequence(self, setting):
        """
        :param setting:
        :type setting: (list, list, list, list)
        :return:
        """
        trade_1, trade_2, trade_3, trade_4, vessel, schedule = self.get_pop_setup(setting)
        time = 0
        has_time_window_constraints = setting[4]
        assert schedule.completion_time() == time
        schedule.add_transportation(trade_1, 1)
        time += 10 + 2 + 2
        assert schedule.completion_time() == time
        assert schedule.get_simple_schedule() == [
            ("PICK_UP", trade_1),
            ("DROP_OFF", trade_1)
        ]
        schedule.add_transportation(trade_2, 3)
        time += 10 + 2 + 10 + 2
        assert schedule.completion_time() == time
        assert schedule.get_simple_schedule() == [
            ("PICK_UP", trade_1),
            ("DROP_OFF", trade_1),
            ("PICK_UP", trade_2),
            ("DROP_OFF", trade_2),
        ]
        engine = DummyEngine(DummyWorld(event_queue=EventQueue()))
        engine.event_queue.set_engine(engine)
        vessel.set_engine(engine)
        vessel.schedule = schedule
        event, _ = engine._process_next_event()
        assert schedule.completion_time() == time
        assert isinstance(event, ArrivalEvent)
        assert event.time == 0
        assert (1, TransportationStartFinishIndicator.START) not in schedule._stn.nodes
        with pytest.raises(ValueError):
            schedule.add_transportation(trade_4, 1)
        schedule.add_transportation(trade_4, 5)
        time += 20 + 2 + 10 + 2
        assert schedule.completion_time() == time
        assert schedule.get_simple_schedule() == [
            ("PICK_UP", trade_1),
            ("DROP_OFF", trade_1),
            ("PICK_UP", trade_2),
            ("DROP_OFF", trade_2),
            ("PICK_UP", trade_4),
            ("DROP_OFF", trade_4),
        ]
        event, _ = engine._process_next_event()
        time -= 2
        assert schedule.completion_time() == time
        assert isinstance(event, CargoTransferEvent)
        assert event.time == 2
        assert schedule.get_simple_schedule() == [
            ("DROP_OFF", trade_1),
            ("PICK_UP", trade_2),
            ("DROP_OFF", trade_2),
            ("PICK_UP", trade_4),
            ("DROP_OFF", trade_4),
        ]
        task_indices = list(set([n[0] for n in schedule._stn.nodes if isinstance(n, tuple)]))
        assert task_indices == list(range(1, 6))
        schedule.add_transportation(trade_3, 4)
        time += - 20 + 10 + 10 + 2 + 2
        assert schedule.completion_time() == time
        assert schedule.get_simple_schedule() == [
            ("DROP_OFF", trade_1),
            ("PICK_UP", trade_2),
            ("DROP_OFF", trade_2),
            ("PICK_UP", trade_3),
            ("DROP_OFF", trade_3),
            ("PICK_UP", trade_4),
            ("DROP_OFF", trade_4),
        ]
        assert schedule.verify_schedule()
        # (trades)      1     1     2     2     3     3     4     4
        # (location)    A ->  B ->  C ->  D  |  D ->  E ->  F ->  G
        # (un/loading)  L ->  U ->  L ->  U  |  L ->  U ->  L ->  U
        # (task time)   2-10- 2-10- 2-10- 2- 0- 2-10- 2-10- 2-10- 2
        # (total time)  0- 2-12-14-24-26-36-38-38-40-50-52-62-64-74-76
        all_expected_event_times = setting[2]
        all_expected_event_types = setting[3]
        expected_schedule_simple_tasks = [
            ("DROP_OFF", trade_1),
            ("PICK_UP", trade_2),
            ("DROP_OFF", trade_2),
            ("PICK_UP", trade_3),
            ("DROP_OFF", trade_3),
            ("PICK_UP", trade_4),
            ("DROP_OFF", trade_4),
        ]
        for expected_event_time, expected_event_type in zip(all_expected_event_times, all_expected_event_types):
            event, _ = engine._process_next_event()
            assert isinstance(event, expected_event_type)
            if isinstance(event, TravelEvent):
                time -= 10
            elif isinstance(event, CargoTransferEvent):
                time -= 2
                expected_schedule_simple_tasks.pop(0)
            if not has_time_window_constraints:
                assert schedule.completion_time() == time
            assert event.time == expected_event_time
            assert schedule.verify_schedule()
            assert schedule.get_simple_schedule() == expected_schedule_simple_tasks
        assert schedule.completion_time() == time

    @pytest.mark.parametrize("setting", [
        ([None, None, None, None], [None, None, None, None],
         [12, 12, 14,
          24, 24, 26,
          36, 36, 38,
          38, 40,
          50, 50, 52,
          62, 62, 64,
          74, 74, 76],
         [TravelEvent, ArrivalEvent, CargoTransferEvent,
          TravelEvent, ArrivalEvent, CargoTransferEvent,
          TravelEvent, ArrivalEvent, CargoTransferEvent,
          ArrivalEvent, CargoTransferEvent,
          TravelEvent, ArrivalEvent, CargoTransferEvent,
          TravelEvent, ArrivalEvent, CargoTransferEvent,
          TravelEvent, ArrivalEvent, CargoTransferEvent],
         False),])
    def test_pop_sequence_2(self, setting):
        """
        :param setting:
        :type setting: (list, list, list, list)
        :return:
        """
        trade_1, trade_2, trade_3, trade_4, vessel, schedule = self.get_pop_setup(setting)
        additional_time = 5
        schedule._engine.world._current_time = additional_time
        time = 0
        has_time_window_constraints = setting[4]
        assert schedule.completion_time() == time
        schedule.add_transportation(trade_1, 1)
        time += 10 + 2 + 2 + additional_time
        assert schedule.completion_time() == time
        schedule.add_transportation(trade_2, 3)
        time += 10 + 2 + 10 + 2
        assert schedule.completion_time() == time
        engine = DummyEngine(DummyWorld(event_queue=EventQueue()))
        engine.event_queue.set_engine(engine)
        vessel.set_engine(engine)
        vessel.schedule = schedule
        event, _ = engine._process_next_event()
        assert schedule.completion_time() == time
        assert isinstance(event, ArrivalEvent)
        assert event.time == 0 + additional_time
        assert (1, TransportationStartFinishIndicator.START) not in schedule._stn.nodes
        with pytest.raises(ValueError):
            schedule.add_transportation(trade_4, 1)
        schedule.add_transportation(trade_4, 5)
        time += 20 + 2 + 10 + 2
        schedule.completion_time()
        event, _ = engine._process_next_event()
        time -= 2
        assert schedule.completion_time() == time
        assert isinstance(event, CargoTransferEvent)
        assert event.time == 2 + additional_time
        task_indices = list(set([n[0] for n in schedule._stn.nodes if isinstance(n, tuple)]))
        assert task_indices == list(range(1, 6))
        schedule.add_transportation(trade_3, 4)
        time += - 20 + 10 + 10 + 2 + 2
        assert schedule.completion_time() == time
        assert schedule.verify_schedule()
        # (trades)      1     1     2     2     3     3     4     4
        # (location)    A ->  B ->  C ->  D  |  D ->  E ->  F ->  G
        # (un/loading)  L ->  U ->  L ->  U  |  L ->  U ->  L ->  U
        # (task time)   2-10- 2-10- 2-10- 2- 0- 2-10- 2-10- 2-10- 2
        # (total time)  0- 2-12-14-24-26-36-38-38-40-50-52-62-64-74-76
        all_expected_event_times = setting[2]
        all_expected_event_types = setting[3]
        for expected_event_time, expected_event_type in zip(all_expected_event_times, all_expected_event_types):
            event, _ = engine._process_next_event()
            assert isinstance(event, expected_event_type)
            if isinstance(event, TravelEvent):
                time -= 10
            elif isinstance(event, CargoTransferEvent):
                time -= 2
            if not has_time_window_constraints and len(schedule) > 0:
                assert schedule.completion_time() == time
            assert event.time == expected_event_time + additional_time
            assert schedule.verify_schedule()
        assert schedule.completion_time() == 0

    @pytest.mark.parametrize("setting", [
        ([None, 35, None, None], [None, None, None, None]),
        ([39, None, None, 50], [None, None, None, None]),
        ([None, None, None, None], [None, None, None, 73]),
    ])
    def test_pop_negative(self, setting):
        """
        :param setting:
        :type setting: (list, list)
        :return:
        """
        trade_1, trade_2, trade_3, trade_4, vessel, schedule = self.get_pop_setup(setting)
        schedule.add_transportation(trade_1, 1)
        schedule.add_transportation(trade_2, 3)
        schedule.add_transportation(trade_4, 5)
        schedule.add_transportation(trade_3, 4)
        assert not schedule.verify_schedule()

    def test_copy(self):
        no_time_windows = ([None] * 4, [None] * 4)
        trade_1, trade_2, trade_3, _, _, schedule = self.get_pop_setup(no_time_windows)
        backup_schedule = schedule.copy()
        schedule.add_transportation(trade_1)
        new_schedule_1 = schedule.copy()
        new_schedule_2 = schedule.copy()
        new_schedule_1.add_transportation(trade_2, 1, 3)
        new_schedule_2.add_transportation(trade_3)
        assert len(backup_schedule) == 0
        assert schedule._number_tasks == 2
        assert schedule.get_simple_schedule()[0][1] == trade_1
        assert new_schedule_1._number_tasks == 4
        assert new_schedule_1.get_simple_schedule()[0][1] == trade_2
        assert new_schedule_2._number_tasks == 4
        assert new_schedule_2.get_simple_schedule()[0][1] == trade_1
        assert new_schedule_2.get_simple_schedule()[-1][1] == trade_3

    def test_get_simple_schedule(self):
        no_time_windows = ([None]*4, [None]*4)
        trade_1, trade_2, _, _, _, schedule = self.get_pop_setup(no_time_windows)
        schedule.add_transportation(trade_1)
        schedule.add_transportation(trade_2, 1, 3)
        simple_schedule = schedule.get_simple_schedule()
        assert ([x[0] for x in simple_schedule]
                == [
                    TransportationSourceDestinationIndicator.PICK_UP.name,
                    TransportationSourceDestinationIndicator.PICK_UP.name,
                    TransportationSourceDestinationIndicator.DROP_OFF.name,
                    TransportationSourceDestinationIndicator.DROP_OFF.name])
        assert ([x[1] for x in simple_schedule]
                == [
                    trade_2,
                    trade_1,
                    trade_1,
                    trade_2])
