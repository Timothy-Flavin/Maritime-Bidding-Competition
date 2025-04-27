import random
import pprint
import trade_utils  # Assuming this file is sitting in the same 'src' folder

def test_generate_trades():
    print("Testing trade generation...\n")
    random.seed(42)  # for reproducibility
    trades = trade_utils.generate_trades(5, allow_nones=True)
    pprint.pprint(trades)
    assert isinstance(trades, list), "Output should be a list"
    assert all(isinstance(t, tuple) and len(t) == 3 for t in trades), "Each trade should be a tuple of (pickup, dropoff, window)"
    assert all(isinstance(t[2], tuple) and len(t[2]) == 4 for t in trades), "Each time window should have 4 elements"
    print("\n✅ Trade generation passed!\n")

def test_fix_trades():
    trades = {'A': (None, 5, None, 10), 'B': (2, None, 5, None)}
    fixed = trade_utils.fix_trades(trades)
    for times in fixed.values():
        for t in times:
            assert t is not None
    print("✅ Fix trades passed!\n")

def test_plot_schedule():
    trades = trade_utils.generate_trades(5, allow_nones=False)
    trade_utils.plot_schedule(trades)  # Should just display a graph without crashing
    print("✅ Plot schedule passed!\n")

def test_is_feasible():
    trades = {
        'A': (1, 5, 6, 10),
        'B': (2, 6, 7, 12)
    }
    assert trade_utils.is_feasible('ABab', trades) == True
    assert trade_utils.is_feasible('aBbA', trades) == False
    print("✅ Feasibility test passed!\n")

def test_generate_init_schedules():
    print("Testing initial schedule generation...")
    trades = {
        'A': (0, 5, 6, 10),
        'B': (2, 7, 8, 13),
        'C': (1, 6, 7, 12),
    }
    schedules = trade_utils.generate_init_schedules(trades)
    print("Generated schedules:", schedules)
    assert isinstance(schedules, list), "Schedules should be a list"
    assert len(schedules) == 3, "Should generate exactly 3 schedules (earliest, midpoint, latest)"
    for schedule in schedules:
        assert isinstance(schedule, str), "Each schedule should be a string"
    print("✅ Initial schedule generation passed!\n")

def test_generate_schedules_swapping():
    trades = trade_utils.generate_trades(3, allow_nones=False)
    schedules = trade_utils.generate_schedules_swapping(trades, num_schedules=10)
    assert len(schedules) == 10
    for sched in schedules:
        assert isinstance(sched, str)
    print("✅ Schedule swapping passed!\n")

def test_generate_schedules_sampling():
    trades = trade_utils.generate_trades(3, allow_nones=False)
    schedules = trade_utils.generate_schedules_sampling(trades, num_schedules=10)
    assert len(schedules) == 10
    for sched in schedules:
        assert isinstance(sched, str)
    print("✅ Schedule sampling passed!\n")

# -----------------------------------------
# Run tests manually
# -----------------------------------------
if __name__ == "__main__":
    test_generate_trades()
    test_fix_trades()
    test_plot_schedule()
    test_is_feasible()
    test_generate_init_schedules()
    test_generate_schedules_swapping()
    test_generate_schedules_sampling()
    print("\n🎉 All trade_utils tests passed! 🎉")
