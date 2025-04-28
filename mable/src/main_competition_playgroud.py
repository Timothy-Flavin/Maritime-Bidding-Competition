from mable.examples import environment, fleets, companies
from structured_logger_observer import StructuredLoggerObserver

import group8


def build_specification():
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

    # 🛠️ Add StructuredLoggerObserver before running
    structured_logger = StructuredLoggerObserver(output_dir="logs")
    # sim._event_observer.append(structured_logger)

    sim.run()
    structured_logger.save()


if __name__ == "__main__":
    build_specification()
