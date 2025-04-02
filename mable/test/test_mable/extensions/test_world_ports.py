import csv

from pathlib import Path

from mable import global_setup
from mable.examples.fleets import example_fleet_1, get_fuel_mfo
from mable.extensions.fuel_emissions import VesselWithEngine
from mable.extensions.world_ports import LatLongShippingNetwork, LatLongPort, LatLongLocation
from mable.simulation_de_serialisation import SimulationSpecification
from mable.simulation_space.universe import OnJourney


class TestLatLongShippingNetwork:

    @staticmethod
    def setup(pytestconfig):
        asset_path = pytestconfig.rootpath / "test" / "test_assets"
        with open(asset_path/ "ports.csv", "r") as f:
            csv_reader = csv.reader(f)
            ports_data = list(csv_reader)
        ports = []
        for one_ports_args in ports_data[1:]:
            one_port = LatLongPort(
                name=one_ports_args[0],
                latitude=float(one_ports_args[1]),
                longitude=float(one_ports_args[2]))
            ports.append(one_port)
        long_lat_shipping_network = LatLongShippingNetwork(
            ports=ports,
            precomputed_routes_file=asset_path / "precomputed_routes.pickle",
            graph_file=asset_path / "routing_graph_world_mask.pkl")
        global_setup.abc["fuels"] = [get_fuel_mfo()]
        SimulationSpecification.register(VesselWithEngine.__name__, VesselWithEngine)
        return long_lat_shipping_network, ports

    def test_get_distance(self, pytestconfig):
        long_lat_shipping_network, ports = self.setup(pytestconfig)
        location = ports[0]
        journey = OnJourney(ports[1], ports[2], 0)
        schema = VesselWithEngine.Data.Schema()
        vessel =  schema.load(schema.dump(example_fleet_1()[0]))
        current_location = long_lat_shipping_network.get_journey_location(journey, vessel, 50)
        distance = long_lat_shipping_network.get_distance(location, current_location)
        assert distance > 0

    def test_get_all_routes_between_points(self, pytestconfig):
        long_lat_shipping_network, ports = self.setup(pytestconfig)
        location_1 = ports[0]
        location_2 = ports[1]
        shortest_routes_port_to_port = long_lat_shipping_network.get_all_stored_routes_between_points(location_1, location_2)
        assert shortest_routes_port_to_port is not None
        shortest_routes_port_to_port_outer_call = long_lat_shipping_network.get_all_routes_between_points(location_1, location_2)
        assert shortest_routes_port_to_port_outer_call is not None
        assert shortest_routes_port_to_port == shortest_routes_port_to_port_outer_call
        random_location_on_route = shortest_routes_port_to_port_outer_call[0].route[1]
        location_3 = LatLongLocation(
            random_location_on_route[1],
            random_location_on_route[0],
            f"<{random_location_on_route[1]}, {random_location_on_route[0]}>"
        )
        shortest_routes_nowhere_to_port_call_1 = long_lat_shipping_network.get_all_stored_routes_between_points(
            location_3, location_2)
        assert shortest_routes_nowhere_to_port_call_1 is None
        shortest_routes_nowhere_to_port_outer_call = long_lat_shipping_network.get_all_routes_between_points(
            location_3, location_2)
        assert shortest_routes_nowhere_to_port_outer_call is not None
        shortest_routes_nowhere_to_port_call_2 = long_lat_shipping_network.get_all_stored_routes_between_points(
            location_3, location_2)
        assert shortest_routes_nowhere_to_port_call_2 is not None
        assert shortest_routes_nowhere_to_port_call_2 == shortest_routes_nowhere_to_port_outer_call
