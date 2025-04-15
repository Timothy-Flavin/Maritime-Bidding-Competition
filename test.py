from mable.cargo_bidding import TradingCompany
from mable.examples import environment, fleets
from mable.cargo_bidding import Bid
import math
import pandas as pd
import pickle


class Simulated_Anealing:
    def __init__(
        self,
    ):
        pass

    def run(
        self,
        destination_ports,  # list of destinations for goods
        time_windows,  # time windows for each destination
        starting_ports,  # where the boats start
        precomputed_distances,  # distances between each ports from dijkstra
    ):
        print("hi")

    def calculate_items_per_boat(self):
        pass

    def fitness(
        self,
        genome_port_list,  # List of port tuples port_name
        genome_partitions,
        all_trades,  # List of all trades
        paths,  # dict[port_name1+port_name2][0] = 'length', 'route'
        n_boats,
        starting_ports,
    ):
        genome_port_index = 0  # the item in the genome we are dealing with
        boat_num = 0
        # The port list is our full path, the item_list is the item destinations in this genome
        proposed_port_path = []
        proposed_port_path.append([starting_ports[0]])  # first boat start
        time_at_each_port = []
        time_at_each_port.append([0])  # first boat start

        # first we fix the genome by adding in free items that are already in the path
        # and we also
        while genome_port_index < len(genome_port_list):
            # if the item we are looking at is the partition number then we need to move
            # to the next boat's tasks because it is the first item in a next boat's inventory
            while (
                genome_port_index == genome_partitions[boat_num]
                and boat_num < n_boats - 1
            ):
                boat_num += 1
                proposed_port_path.append(
                    [starting_ports[boat_num]]
                )  # next boat start new path array
                time_at_each_port.append([0])  # start at time 0 for the next boat

            # Now we add the item to the boat's path and update the time at each port
            proposed_port_path[boat_num].append(genome_port_list[genome_port_index])
            time_at_each_port[boat_num].append(  # time to get to the first item
                float(
                    paths[
                        proposed_port_path[boat_num][-2]
                        + proposed_port_path[boat_num][-1]
                    ][0].length
                )
                + time_at_each_port[boat_num][-1]  # plus previous time.
                # Might change this away from cumulative time later
            )
            genome_port_index += 1

        for boat in range(n_boats):
            calculate_items_per_boat(proposed_port_path[boat], time_at_each_port[boat])

    def get_schedule(self):
        pass

    def get_cost(self):
        pass


class Companyn(TradingCompany):
    def __init__(self, fleet, name):
        super().__init__(fleet, name)
        ports = pd.read_csv("ports.csv")
        # connections = pd.read_csv("time_transition_distribution.csv")

        with open("precomputed_routes.pickle", "rb") as f:
            pr = pickle.load(f)
        print(ports)
        # for p1 in ports["Port_Name"]:
        #    for p2 in ports["Port_Name"]:
        #        if p1 != p2:
        #            print(f"Distance from {p1} to {p2}: {pr[p1+p2][0].route}")
        #            input()
        # exit()

    def inform(self, trades, *args, **kwargs):
        print(f"Company {self._name} received trades: {trades}")
        proposed_scheduling = self.propose_schedules(trades)
        print(proposed_scheduling)
        exit()
        scheduled_trades = proposed_scheduling.scheduled_trades
        self._current_scheduling_proposal = proposed_scheduling
        bids = [Bid(amount=math.inf, trade=one_trade) for one_trade in scheduled_trades]
        return bids

    def pre_inform(self, trades, time):
        print(f"Company {self._name} received trades: {trades} at time {time}")

    def receive(self, contracts, auction_ledger=None, *args, **kwargs):
        print(f"Company {self._name} received contracts: {contracts}")
        input("did that make sense?")


if __name__ == "__main__":
    specifications_builder = environment.get_specification_builder(
        environment_files_path="."
    )
    fleet = fleets.example_fleet_1()
    specifications_builder.add_company(
        Companyn.Data(Companyn, fleet, "My Shipping Corp Ltd.")
    )
    sim = environment.generate_simulation(specifications_builder)
    sim.run()
