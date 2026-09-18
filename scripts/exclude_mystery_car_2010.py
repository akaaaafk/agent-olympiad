"""Exclude the archived physical-car task; do not invent historical context."""
from exclude_mystery_interactive_2010 import main


if __name__ == '__main__':
    main(
        targets={'mystery_hunt_01307': (
            'Just look in the usual space or somewhere nearby.',
            'Original archive warns of time-changing elements. The task requires locating a historical car; vehicle/location context is absent from the isolated input. No substitute context is invented.')},
        report_path='output/hunt_car_exclusion_20260917.json',
        required_limitation='Historical location, car and time-sensitive context are not recreated',
    )
