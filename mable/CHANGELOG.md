## [0.0.13] - 2025-02-05
### Changed
- Changing a vessel's schedule purges the event queue of all of the vessel's events.

## [0.0.12] - 2025-01-29
### Fixed
- Old schedules being applied after a 'receive' had a timeout.

## [0.0.11] - 2024-12-29
### Added
- Prevent schedules containing unallocated trades to be applied.
- Prevent schedules containing one trade that is allocated to several vessels.
- The simulation continues after an exception in any agent's code.
An exception in an agent's code will end that agent's run of
pre_inform, inform or receive for the current auction.
- Info field for simulation export.
### Fixed
- Problems with vessel's OnJourney in SimpleCompany.get_arrival_time.

## [0.0.10] - 2024-12-11
### Fixed
- Schedules not detecting time window violations in some cases.

## [0.0.9] - 2024-12-09
### Added
- Penalty calculation for unfulfilled contracts. The penalty is the transportation
cost of using the biggest ship in the agent's fleet.
- The SimulationEngine applies new Schedules via apply_new_schedules. This function
also logs any rejected schedules.
- Function to format time (format_time in Mable.util)
### Changed
- Arrival time windows for all trades of an auction are between the auction time and
the next auction time.
For example, for monthly (every 30 days) auctions, trades at the auction on day 60
will have a pick-up window between 60 and 90.
- SimpleCompany.apply_schedules
  - The function now defers the application of schedules. This means
  that schedules are not applied immediately and the function will not return a list of
  rejected schedules.
  - The function is no longer static but an instance function. 
- Refactored simulation_space into a package that has
dedicated modules for the dataclasses and the network structure.
  - New modules simulation_space.structure, simulation_space.universe
### Removed
- Events (event_management.Event) no longer have a format_time function,
use Mable.util.format_time.

## [0.0.8] - 2024-12-4
### Changed
- Changed default of use_only_precomputed_routes in examples.environment.get_specification_builder
to True

## [0.0.7] - 2024-12-3
### Added
- Routes that are not precomputed and are computed during a run will also be buffered in the
precomputed routes.
- Added option use_only_precomputed_routes to examples.environment.get_specification_builder
to only generate cargoes between ports that have a pre-exiting precomputed route
### Fixed
- Vessel location not being updated in TradingHeadquarters get_companies
function.
- TypeError for TradingCompany's get_arrival_time() (SimpleCompany)
if the vessel is OnJourney.

## [0.0.6] - 2024-11-28
### Changed
- Schedule.copy to not create a deepcopy of the internal schedule.
The original and the copy will remain independent with respect to add_transportation etc..
### Fixed
- Trade auction using sorted bids to determine payments.
- Fixed adding to schedule producing "TypeError: unhashable type: 'OnJourney'"
when the vessel is on a journey.
- Schedule completion time to calculate the full time.

## [0.0.5] - 2024-11-26
### Changed
- Set Fuel price to 1, i.e. amount of consumed fuel is equivalent to fuel costs.
### Fixed
- Trade auction not being a reverse auction.

## [0.0.4] - 2024-11-24
### Added
- Generate mixed fleets of Aframax, Suezmax and VLCCs
- Timeouts for TradeCompany's pre_inform, inform and receive
- Calculate final idling per vessel
- Calculate OnJourney locations and distances (distance calculation is time intensive)

<!---
TEMPLATE
## [Unreleased]

## [0.0.0] - 20XX-XX-XX
### Added
- AAA
### Changed
- BBB
### Deprecated
- CCC
### Removed
- DDD
### Fixed
- EEE
### Security
- FFF
-->
