{
    "_info": None,
    "_event_observer": [
        "mable.observers.AuctionMetricsObserver object at 0x000002973C00C850",
        "mable.observers.EventFuelPrintObserver object at 0x000002973E84B4D0",
        "mable.observers.AuctionOutcomePrintObserver object at 0x00000297583CEFD0",
        "mable.observers.AuctionOutcomeObserver object at 0x000002975D404650",
        "mable.observers.TradeDeliveryObserver object at 0x000002973CF9AC50",
    ],
    "_world": "mable.simulation_environment.World object at 0x000002973CEB7E90",
    "_shipping_companies": [
        "group8.Group8Company object at 0x000002973CF3E890",
        "mable.examples.companies.MyArchEnemy object at 0x000002977B2A9150",
        "mable.examples.companies.TheScheduler object at 0x000002973E98F7D0",
    ],
    "_shipping": "mable.extensions.cargo_distributions.DistributionShipping object at 0x000002973CEF5650",
    "_market": "mable.shipping_market.AuctionMarket object at 0x000002973FD684D0",
    "_class_factory": "mable.competition.generation.AuctionClassFactory object at 0x000002973C67D410",
    "_pre_run_cmds": [
        "mable.observers.LogRunner object at 0x000002973CEDDE90",
        "function pre_run_place_vessels at 0x000002973A1F98A0",
        "function pre_run_inform_vessel_locations at 0x000002972AF560C0",
        "mable.observers.LogRunner object at 0x000002973CEDDE50",
    ],
    "_post_run_cmds": [
        "mable.observers.LogRunner object at 0x000002973CFA1CD0",
        "function _export_stats at 0x000002973BFEBB00",
    ],
    "_output_directory": ".",
    "_headquarters": "mable.competition.information.CompanyHeadquarters object at 0x000002973EDD10D0",
    "_global_agent_timeout": 60,
    "_market_authority": "mable.competition.information.MarketAuthority object at 0x000002973FC743D0",
    "_new_schedules": {},
}

from mable.examples import environment, fleets, companies
from structured_logger_observer import StructuredLoggerObserver
import group8
from mable.shipping_market import TimeWindowTrade

number_of_month = 12
trades_per_auction = 5
specifications_builder = environment.get_specification_builder(
    trades_per_occurrence=trades_per_auction, num_auctions=number_of_month
)
# Companies
my_fleet = fleets.mixed_fleet(num_suezmax=1, num_aframax=1, num_vlcc=1)
specifications_builder.add_company(
    group8.Group8Company.Data(
        group8.Group8Company, my_fleet, group8.Group8Company.__name__
    )
)
arch_enemy_fleet = fleets.mixed_fleet(num_suezmax=1, num_aframax=1, num_vlcc=1)
specifications_builder.add_company(
    companies.MyArchEnemy.Data(
        companies.MyArchEnemy,
        arch_enemy_fleet,
        "Arch Enemy Ltd.",
        profit_factor=1.5,
    )
)
the_scheduler_fleet = fleets.mixed_fleet(num_suezmax=1, num_aframax=1, num_vlcc=1)
specifications_builder.add_company(
    companies.TheScheduler.Data(
        companies.TheScheduler,
        the_scheduler_fleet,
        "The Scheduler LP",
        profit_factor=1.4,
    )
)
# Build simulation
sim = environment.generate_simulation(
    specifications_builder,
    show_detailed_auction_outcome=True,
    global_agent_timeout=60,
)

sim._pre_run_cmds[1](sim)
sim._pre_run_cmds[2](sim)
gp8 = sim._shipping_companies[0]
s1 = gp8.fleet[0]
sched = s1.schedule.copy()
# usefull live code snippets
tr = TimeWindowTrade(
    origin_port="Aberdeen-f8ea5ddd09c3",
    destination_port="Abidjan-ef95aea8399b",
    amount=6969,
    cargo_type="Oil",
    time_window=[0, 500, 700, 1000],
)

tr2 = TimeWindowTrade(
    origin_port="Balikpapan-5fa8d362a22a",
    destination_port="Balongan-1fd4b61205b9",
    amount=1738,
    cargo_type="Oil",
    time_window=[100, 600, 900, 1500],
)

sched = s1.schedule.copy()
sched.get_simple_schedule()
sched.get_insertion_points()
sched.add_transportation(tr2)
sched.get_simple_schedule()
sched.get_insertion_points()
# def _ensure_location_validity(self, location_pick_up, location_drop_off):
#     if location_pick_up > location_drop_off:
#         raise ValueError(
#             "Schedule locations are not compatible with the current schedule:"
#             " Trying to drop of cargo before picking it up."
#         )
#     elif (
#         location_pick_up == 1
#         and len(self) > 0
#         and (1, TransportationStartFinishIndicator.START) not in self._stn
#     ):
#         print(f"First elif: {self._stn}")
#         print(
#             f"location_pick_up: {location_pick_up}, location_drop_off: {location_drop_off}"
#         )
#         # TODO Write better error!
#         raise ValueError(
#             "One or both schedule locations are not compatible with the current schedule."
#         )
#     elif location_pick_up > self._number_tasks + 1:
#         # TODO Write better error!
#         print(f"Second elif: {self._stn}")
#         print(
#             f"location_pick_up: {location_pick_up}, num tasks + 1: {self._number_tasks + 1}"
#         )
#         raise ValueError(
#             "One or both schedule locations are not compatible with the current schedule."
#         )
#     elif (
#         location_pick_up != self._number_tasks + 1
#         and location_drop_off > self._number_tasks + 1
#     ):
#         print(f"Third elif: {self._stn}")
#         print(
#             f"location_pick_up: {location_pick_up}, location_drop_off: {location_drop_off}, num tasks +1: {self._number_tasks + 1}"
#         )
#         # TODO Write better error!
#         raise ValueError(
#             "One or both schedule locations are not compatible with the current schedule."
#         )
#     elif (
#         location_pick_up == self._number_tasks + 1
#         and location_drop_off > self._number_tasks + 2
#     ):
#         print(f"Fourth elif: {self._stn}")
#         print(
#             f"location_pick_up: {location_pick_up}, location_drop_off: {location_drop_off}, num tasks +1: {self._number_tasks + 1}"
#         )
#         # TODO Write better error!
#         raise ValueError(
#             "One or both schedule locations are not compatible with the current schedule."
#         )
