import numpy as np

from mable.event_management import TravelEvent, CargoTransferEvent
from mable.shipping_market import TimeWindowTrade
from mable.simulation_space.universe import Port
from mable.transport_operation import SimpleCompany
from mable.transportation_scheduling import Schedule
from test_mable.test_transportation_scheduling import VESSEL


class TestSimpleCompany:

    def test_get_arrival_time(self, mocker):
        source_port = Port("A", 0, 0)
        destination_port = Port("B", 5, 5)
        trade = TimeWindowTrade(origin_port=source_port, destination_port=destination_port, amount=10,
                                  cargo_type="Oil")
        port = Port("C", 12, 11)
        vessel = VESSEL
        company = SimpleCompany([vessel], "Test")
        schedule = Schedule(VESSEL)
        mock_engine = mocker.patch("mable.engine.SimulationEngine")
        mock_engine.world.network.get_distance = lambda p1, p2: np.abs(p1.x - p2.x) + np.abs(p1.y - p2.y)
        mock_engine.world.network.get_port_or_default.return_value = port
        vessel_location = Port("X", 1, 1)
        mock_engine.world.network.get_vessel_location.return_value = vessel_location
        mock_engine.class_factory.generate_event_travel = lambda *args, **kwargs: TravelEvent(*args, **kwargs)
        mock_engine.class_factory.generate_event_cargo_transfer = lambda *args, **kwargs: CargoTransferEvent(*args, **kwargs)
        mock_engine.world.current_time = 0
        schedule.set_engine(mock_engine)
        company.set_engine(mock_engine)
        schedule.add_transportation(trade)
        arrival_time = company.get_arrival_time(port, schedule, vessel)
        travel_to_a = 1 + 1
        travel_to_b = 5 + 5
        un_loading = 2 + 2
        travel_to_c = 7 + 6
        assert arrival_time == travel_to_a + travel_to_b + un_loading + travel_to_c
