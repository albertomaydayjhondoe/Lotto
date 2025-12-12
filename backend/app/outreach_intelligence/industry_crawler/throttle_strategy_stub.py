# STUB throttle strategies simulating human-like timing

def safe_mode():
    return {
        "mode": "SAFE_MODE",
        "req_per_sec": 1,
        "notes": "Slowest mode — legal safe baseline.",
    }

def burst_mode():
    return {
        "mode": "BURST_MODE",
        "initial_burst": 3,
        "cooldown_sec": 5,
        "notes": "Short bursts followed by rest — realistic but controlled.",
    }

def nervous_mode():
    return {
        "mode": "NERVOUS_MODE",
        "pattern": "random_human_like",
        "delay_range_ms": [300, 1800],
        "burst_limit": 2,
        "cooldown_after_burst_ms": 2500,
        "notes": "Most human-like — varies timing and pauses.",
    }
