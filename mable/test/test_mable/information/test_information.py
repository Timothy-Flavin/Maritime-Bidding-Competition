import csv
from unittest.mock import PropertyMock

from mable import global_setup
from mable.cargo_bidding import TradingCompany
from mable.competition.information import CompanyHeadquarters
from mable.extensions.fuel_emissions import VesselWithEngine, ConsumptionRate, VesselEngine, Fuel
from mable.extensions.world_ports import LatLongPort, LatLongShippingNetwork, LatLongLocation
from mable.simulation_de_serialisation import SimulationSpecification
from mable.simulation_space.universe import OnJourney
from mable.transport_operation import CargoCapacity


class TestCompanyHeadquarters:

    @staticmethod
    def get_fuel_mfo():
        return Fuel(name="MFO", price=1, energy_coefficient=40, co2_coefficient=3.16)

    @staticmethod
    def setup(pytestconfig, mocker):
        asset_path = pytestconfig.rootpath / "test" / "test_assets"
        with open(asset_path / "ports.csv", "r") as f:
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
        global_setup.abc["fuels"] = [TestCompanyHeadquarters.get_fuel_mfo()]
        SimulationSpecification.register(VesselWithEngine.__name__, VesselWithEngine)
        location = ports[0]
        journey = OnJourney(ports[1], ports[2], 0)
        schema = VesselWithEngine.Data.Schema()
        vessel = schema.load(schema.dump(TestCompanyHeadquarters.test_fleet_of_one_vessel()[0]))
        vessel.location = location
        mock_world_class = mocker.patch("mable.simulation_environment.World")
        mock_world = mock_world_class.return_value
        mock_world._current_time = 50
        def current_time():
            return mock_world._current_time
        type(mock_world).current_time = PropertyMock(side_effect=current_time)
        mock_world.network = long_lat_shipping_network
        mock_engine = mocker.patch("mable.engine.SimulationEngine")
        mock_engine.world = mock_world
        shipping_companies = [TradingCompany([vessel], "Test")]
        mock_engine.shipping_companies = shipping_companies
        company_headquarters = CompanyHeadquarters(mock_engine)
        return company_headquarters, journey, vessel, location

    @staticmethod
    def test_fleet_of_one_vessel():
        laden_consumption_rate = ConsumptionRate.Data(
            ConsumptionRate,
            base=0.5503,
            speed_power=2.19201,
            factor=1 / 24)
        ballast_consumption_rate = ConsumptionRate.Data(
            ConsumptionRate,
            base=0.1493,
            speed_power=2.3268,
            factor=1 / 24)
        fleet = [VesselWithEngine.Data(
            VesselWithEngine,
            [CargoCapacity.Data(CargoCapacity, cargo_type="Oil", capacity=300000, loading_rate=5000)],
            "Aberdeen-f8ea5ddd09c3",
            speed=14,
            propelling_engine=VesselEngine.Data(
                VesselEngine,
                fuel=f"{TestCompanyHeadquarters.get_fuel_mfo().name}",
                idle_consumption=7.13 / 24,
                laden_consumption_rate=laden_consumption_rate,
                ballast_consumption_rate=ballast_consumption_rate,
                loading_consumption=15.53 / 24,
                unloading_consumption=134.37 / 24),
            name="HMS Terror",
            keep_journey_log=True)]
        return fleet

    def test_get_journey_location(self, pytestconfig, mocker):
        company_headquarters, journey, vessel, _ = self.setup(pytestconfig, mocker)
        journey_location = company_headquarters.get_journey_location(journey, vessel)
        assert isinstance(journey_location, LatLongLocation)
        assert isinstance(journey.origin, LatLongPort)
        assert isinstance(journey.destination, LatLongPort)
        assert journey_location.latitude != journey.origin.latitude
        assert journey_location.latitude != journey.destination.latitude
        assert journey_location.longitude != journey.origin.longitude
        assert journey_location.longitude != journey.destination.longitude

    def test_get_network_distance(self, pytestconfig, mocker):
        company_headquarters, journey, vessel, location = self.setup(pytestconfig, mocker)
        journey_location_1 = company_headquarters.get_journey_location(journey, vessel, 10)
        journey_location_2 = company_headquarters.get_journey_location(journey, vessel)
        distance_1 = company_headquarters.get_network_distance(location, journey_location_1)
        assert distance_1 > 0
        distance_2 = company_headquarters.get_network_distance(location, journey_location_2)
        assert distance_2 > 0
        assert distance_1 > distance_2

    def test_get_companies(self, pytestconfig, mocker):
        # Setup
        company_headquarters, journey, vessel, location = self.setup(pytestconfig, mocker)
        start_time = company_headquarters.current_time
        company = company_headquarters._engine.shipping_companies[0]
        company.headquarters = company_headquarters
        # Test
        sanitised_companies = company.headquarters.get_companies()
        assert len(sanitised_companies) == 1
        the_company = sanitised_companies[0]
        assert the_company.pre_inform is None
        assert the_company.inform is None
        assert the_company.receive is None
        assert the_company.fleet[0].location == location
        assert company_headquarters._shipping_companies_update_time == start_time
        ## Test Port Change
        port_singapore = company_headquarters.get_network_port_or_default(
            "Singapore-bfe15a9e31a0", None)
        company._fleet[0].location = port_singapore
        ### No update without progress in time
        the_company = company.headquarters.get_companies()[0]
        assert the_company.fleet[0].location == location
        assert company_headquarters._shipping_companies_update_time == start_time
        ### Time Progression -> new port
        company_headquarters._engine.world._current_time = start_time + 1
        the_company = company.headquarters.get_companies()[0]
        assert the_company.fleet[0].location == port_singapore
