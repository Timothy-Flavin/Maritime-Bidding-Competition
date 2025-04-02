import pytest

from mable.examples import environment
from mable.shipping_market import Contract

def test__calculate_penalty(mocker):
    mock_vessel_1 = mocker.patch('mable.extensions.fuel_emissions.VesselWithEngine')
    capacity_vessel_1 = 10
    mock_vessel_1.capacity.return_value = capacity_vessel_1
    mock_vessel_2 = mocker.patch('mable.extensions.fuel_emissions.VesselWithEngine')
    capacity_vessel_2 = 20
    mock_vessel_2.capacity.return_value = capacity_vessel_2
    mock_vessel_2.get_loading_time.return_value = 1
    mock_vessel_2.get_travel_time = lambda x: x
    mock_vessel_2.get_ballast_consumption.return_value = 2
    mock_vessel_2.get_laden_consumption = lambda x, _: x
    mock_vessel_2.get_ballast_consumption.return_value = 1
    mock_vessel_2.propelling_engine.fuel.get_cost = (
        lambda x:
            mock_vessel_2.get_ballast_consumption.return_value * 2
            + mock_vessel_2.get_laden_consumption(4, 0)
            + mock_vessel_2.get_ballast_consumption.return_value)
    mock_shipping_company = mocker.patch('mable.transport_operation.ShippingCompany')
    mock_shipping_company.fleet = [mock_vessel_1, mock_vessel_2]
    mock_simulation_engine = mocker.patch("mable.engine.SimulationEngine")
    mock_simulation_engine.shipping_companies = [mock_shipping_company]
    mock_simulation_engine.headquarters.get_network_distance = lambda x, y: y - x
    mock_trade_1 = mocker.patch("mable.shipping_market.Trade")
    mock_trade_1.x = 1
    mock_trade_1.y = 5
    mock_trade_2 = mocker.patch("mable.shipping_market.Trade")
    mock_trade_1.x = 1
    mock_trade_1.y = 2
    payment_unfulfilled = 10
    payment_fulfilled = 20
    mock_simulation_engine.market_authority.contracts_per_company = {
        mock_simulation_engine.shipping_companies[0]: [
        Contract(payment=payment_unfulfilled, trade=mock_trade_1),
        Contract(payment=payment_fulfilled, trade=mock_trade_2, fulfilled=True)]
    }
    mock_metrics_observer = mocker.patch("mable.observers.MetricsObserver")
    company_id = 0
    mock_metrics_observer.metrics.get_company_id.return_value = company_id
    penalties = environment._calculate_penalty(mock_simulation_engine, mock_metrics_observer)
    assert len(penalties) == 1
    assert penalties[company_id] == mock_vessel_2.propelling_engine.fuel.get_cost(None)
