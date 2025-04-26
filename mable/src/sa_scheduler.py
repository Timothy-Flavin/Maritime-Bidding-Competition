# Simulated Annealing logic lives here
# (Tim's work)

class SAScheduler:
    def __init__(self, vessels, trades):
        self.vessels = vessels
        self.trades = trades
        # More initialization later

    def generate_initial_solution(self):
        pass  # To implement (maybe call a trade_utils function)

    def mutate_solution(self, solution):
        pass

    def evaluate_fitness(self, solution):
        pass

    def run(self):
        pass