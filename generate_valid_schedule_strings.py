import matplotlib.pyplot as plt
import random

# Fix trades by ensuring all time windows are integers
def fix_trades(trades):
    times = [t for window in trades.values() for t in window if t is not None]
    if len(times) == 4*len(trades):  # All times are already integers
        return trades
    fixed_trades = {}
    min_time = min(times) - 1
    max_time = max(times) + 1
    fixed_trades = {}
    for port, windows in trades.items():
        ep, lp, ed, ld = windows
        if ep is None: ep = min_time
        if ld is None: ld = max_time
        if ed is None: ed = ep
        if lp is None: lp = ld
        fixed_trades[port] = (ep, lp, ed, ld)
    return fixed_trades

# Plot the schedule graph
def plot_schedule(trades):
    fig, ax = plt.subplots(figsize=(7, 3))
    y_positions = range(len(trades))
    for i, (trade, (ep, lp, ed, ld)) in enumerate(trades.items()):
        # Plot pickup window
        ax.plot([ep, lp], [i, i], color='blue', linewidth=4, label='Pickup' if i == 0 else "", alpha=0.5)
        # Plot dropoff window
        ax.plot([ed, ld], [i, i], color='green', linewidth=4, label='Dropoff' if i == 0 else "", alpha=0.5)
        # Add labels
        ax.text(ep - 0.5, i, f"{trade}", verticalalignment='center', color='blue')
        ax.text(ld + 0.5, i, f"{trade.lower()}", verticalalignment='center', color='green')

    ax.set_yticks(y_positions)
    ax.set_yticklabels(trades.keys())
    ax.set_xlabel("Time")
    ax.set_title("Trade Schedule")
    ax.legend()
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def is_feasible(trades, sequence):
    # Check uppercase precedes lowercase, and time feasibility
    time = 0
    visited = {}
    for ch in sequence:
        t = trades[ch.upper()]  # Get the time windows for the port
        if ch.isupper(): # Pickup
            time = max(time, t[0])  # Earliest pickup
            if time > t[1]: return False  # Too late for pickup
            visited[ch.upper()] = time
        else: # Dropoff
            if ch.upper() not in visited: return False  # Dropoff before pickup
            time = max(time, t[2])  # Earliest dropoff
            if time > t[3]: return False  # Too late for dropoff
    return True

# Generate orders based on different criteria
def generate_init_schedules(trades):
    # Create a dictionary with pickup and dropoff ports
    ports = {}
    for port, windows in trades.items():
        ep, lp, ed, ld = windows
        ports[port.upper()] = (ep, lp)
        ports[port.lower()] = (ed, ld)

    # Order by earliest time in the time window
    earliest_order = sorted(ports.keys(), key=lambda x: ports[x][0])
    # Order by midpoint of the time window
    midpoint_order = sorted(ports.keys(), key=lambda x: (ports[x][0] + ports[x][1]) / 2)
    # Order by latest time in the time window
    latest_order = sorted(ports.keys(), key=lambda x: ports[x][1])

    return [''.join(earliest_order), ''.join(midpoint_order), ''.join(latest_order)]

# Generate 100 schedules by swapping adjacent ports
def generate_schedules(trades, num_schedules=100):
    schedules = generate_init_schedules(trades)
    while len(schedules) < num_schedules:
        schedule = list(random.choice(schedules))  # Pick a random schedule
        idx = random.randint(0, len(schedule) - 2)  # Pick a random adjacent pair
        schedule[idx], schedule[idx + 1] = schedule[idx + 1], schedule[idx]  # Swap them
        schedule = ''.join(schedule)  # Convert back to string
        if schedule not in schedules and is_feasible(trades, schedule):  # Check if the new schedule is unique and feasible
            schedules.append(schedule)
    return schedules

if __name__ == "__main__":
    # trades = {
    #     'A': (1,2,9,10),
    #     'C': (3,4,6,7),
    #     'E': (2,5,10,13),
    #     'G': (1,8,9,16),
    #     'I': (6,7,20,21),
    #     'N': (5,10,15,20)
    # }
    trades = {
        'A': (1,2,9,10),
        'C': (None,4,6,7),
        'E': (2,5,10,None),
        'G': (1,8,None,16),
        'I': (6,None,20,21),
        'N': (None,10,None,20)
    }
    fixed_trades = fix_trades(trades)

    # Generate schedules
    schedules = generate_schedules(fixed_trades)

    # Print the generated schedules
    for i, schedule in enumerate(schedules):
        print(f"Schedule {i + 1}: {schedule}")

    plot_schedule(fixed_trades)
