"""
DAIDALUS Examples: How to create custom scenarios with temporal conflict analysis

This file demonstrates how to easily extend the integrated DAIDALUS system
to create custom scenarios with different aircraft configurations and wind conditions.
"""

import numpy as np
import matplotlib.pyplot as plt
from daidalus_integrated import (
    AircraftState, BimodalWindField, DAIDALUSConfig,
    ConflictDetection, EnhancedDAIDALUSVisualizer
)


def scenario_1_head_on_frontal_winds():
    """
    Scenario 1: Head-on encounter with frontal wind shift

    Two aircraft approaching head-on with wind shifting from east to west (frontal passage)
    """
    print("\n" + "=" * 80)
    print("Scenario 1: Head-on Encounter with Frontal Wind Shift")
    print("=" * 80)

    cfg = DAIDALUSConfig()
    visualizer = EnhancedDAIDALUSVisualizer(cfg)

    # Head-on configuration
    own = AircraftState(
        x=0, y=0, z=1500,           # Starting at origin, 1500m altitude
        vx=50, vy=0, vz=0           # Moving north at 50 m/s, level flight
    )

    intr = AircraftState(
        x=4000, y=0, z=1500,        # 4km north, same altitude
        vx=-50, vy=0, vz=0          # Moving south at 50 m/s, level flight
    )

    # Frontal passage: East wind transitioning to west wind
    wind_field = BimodalWindField(
        mode1_params=(15, 0, 3, np.pi/12),          # 15 m/s from east (pre-front)
        mode2_params=(20, np.pi, 4, np.pi/10),      # 20 m/s from west (post-front)
        mix_weight=0.6                               # 60% pre-front, 40% post-front
    )

    print(f"  Ownship:  Moving north at {own.vx:.1f} m/s from origin")
    print(f"  Intruder: Moving south at {-intr.vx:.1f} m/s from 4km north")
    print(f"  Wind: Frontal passage (60% easterly, 40% westerly)")

    fig = visualizer.create_comprehensive_dashboard(
        "Head-on with Frontal Wind Shift",
        own, intr, wind_field
    )

    plt.savefig('scenario1_head_on_frontal.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: scenario1_head_on_frontal.png")
    plt.close()


def scenario_2_crossing_gusty():
    """
    Scenario 2: Crossing paths with gusty conditions (MAIN SCENARIO)

    Aircraft crossing at right angles with strong gusty winds
    """
    print("\n" + "=" * 80)
    print("Scenario 2: Crossing Paths with Gusty Conditions")
    print("=" * 80)

    cfg = DAIDALUSConfig()
    visualizer = EnhancedDAIDALUSVisualizer(cfg)

    own = AircraftState(
        x=0, y=0, z=1000,           # Origin, 1000m altitude
        vx=50, vy=0, vz=0.8         # North at 50 m/s, climbing at 0.8 m/s
    )

    intr = AircraftState(
        x=1000, y=-1000, z=1200,    # 1km north, 1km west, 1200m altitude
        vx=0, vy=50, vz=-0.5        # East at 50 m/s, descending at 0.5 m/s
    )

    # Gusty conditions: Strong southerly gusts alternating with light northerly
    wind_field = BimodalWindField(
        mode1_params=(20, np.pi/2, 6, np.pi/8),     # 20 m/s from south (gusts)
        mode2_params=(5, -np.pi/2, 2, np.pi/12),    # 5 m/s from north (lulls)
        mix_weight=0.7                               # 70% gusts, 30% lulls
    )

    print(f"  Ownship:  Moving north, climbing from 1000m")
    print(f"  Intruder: Moving east, descending from 1200m")
    print(f"  Wind: Gusty southerly (70% strong, 30% light)")

    fig = visualizer.create_comprehensive_dashboard(
        "Crossing with Gusty Conditions",
        own, intr, wind_field
    )

    plt.savefig('scenario2_crossing_gusty.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: scenario2_crossing_gusty.png")
    plt.close()


def scenario_3_parallel_thermal():
    """
    Scenario 3: Parallel paths with thermal wind effects

    Two aircraft on parallel paths with thermal-induced wind variability
    """
    print("\n" + "=" * 80)
    print("Scenario 3: Parallel Paths with Thermal Wind Effects")
    print("=" * 80)

    cfg = DAIDALUSConfig()
    visualizer = EnhancedDAIDALUSVisualizer(cfg)

    # Parallel paths with slight convergence
    own = AircraftState(
        x=0, y=0, z=800,            # Origin, low altitude
        vx=70, vy=0, vz=0           # Fast northbound, level
    )

    intr = AircraftState(
        x=0, y=1000, z=850,         # 1km east, similar altitude
        vx=65, vy=-5, vz=0          # Slower, slight convergence
    )

    # Thermal circulation: Updraft vs downdraft zones
    wind_field = BimodalWindField(
        mode1_params=(10, np.pi/4, 2, np.pi/8),     # Updraft convergence (NE)
        mode2_params=(8, -np.pi/4, 2, np.pi/8),     # Downdraft divergence (SE)
        mix_weight=0.5                               # Equal probability
    )

    print(f"  Ownship:  Fast parallel path on west side")
    print(f"  Intruder: Slower on east side, slight convergence")
    print(f"  Wind: Thermal circulation (50% updraft, 50% downdraft)")

    fig = visualizer.create_comprehensive_dashboard(
        "Parallel with Thermal Effects",
        own, intr, wind_field
    )

    plt.savefig('scenario3_parallel_thermal.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: scenario3_parallel_thermal.png")
    plt.close()


def scenario_4_overtaking_mountain_wave():
    """
    Scenario 4: Overtaking with mountain wave effects

    Fast aircraft overtaking slower one with oscillating mountain wave winds
    """
    print("\n" + "=" * 80)
    print("Scenario 4: Overtaking with Mountain Wave Effects")
    print("=" * 80)

    cfg = DAIDALUSConfig()
    visualizer = EnhancedDAIDALUSVisualizer(cfg)

    # Overtaking scenario
    own = AircraftState(
        x=0, y=0, z=2000,           # Starting behind
        vx=80, vy=0, vz=0           # Fast overtaking speed
    )

    intr = AircraftState(
        x=1500, y=200, z=2000,      # Ahead and slightly east
        vx=50, vy=0, vz=0           # Slower speed
    )

    # Mountain wave: Oscillating lee wave pattern
    wind_field = BimodalWindField(
        mode1_params=(30, np.pi/3, 5, np.pi/12),    # Updraft side (NE wind)
        mode2_params=(30, -np.pi/3, 5, np.pi/12),   # Downdraft side (SE wind)
        mix_weight=0.5                               # Oscillating pattern
    )

    print(f"  Ownship:  Fast aircraft (80 m/s) overtaking from behind")
    print(f"  Intruder: Slower aircraft (50 m/s) ahead")
    print(f"  Wind: Mountain wave oscillation (±30° from east)")

    fig = visualizer.create_comprehensive_dashboard(
        "Overtaking with Mountain Waves",
        own, intr, wind_field
    )

    plt.savefig('scenario4_overtaking_mountain.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: scenario4_overtaking_mountain.png")
    plt.close()


def scenario_5_custom_template():
    """
    Scenario 5: Custom template - modify this for your own scenarios

    Template showing all the parameters you can customize
    """
    print("\n" + "=" * 80)
    print("Scenario 5: Custom Template")
    print("=" * 80)

    cfg = DAIDALUSConfig()

    # Optionally modify config parameters
    # cfg.DMOD = 1500  # Change separation threshold to 1500m
    # cfg.LOOKAHEAD_TIME = 180  # Increase lookahead to 3 minutes

    visualizer = EnhancedDAIDALUSVisualizer(cfg)

    # Define your ownship
    own = AircraftState(
        x=0,        # North position (m)
        y=0,        # East position (m)
        z=1000,     # Altitude (m)
        vx=50,      # North velocity (m/s)
        vy=0,       # East velocity (m/s)
        vz=0        # Vertical velocity (m/s): positive=climb, negative=descend
    )

    # Define your intruder
    intr = AircraftState(
        x=2000,     # North position (m)
        y=0,        # East position (m)
        z=1000,     # Altitude (m)
        vx=-30,     # North velocity (m/s)
        vy=0,       # East velocity (m/s)
        vz=0        # Vertical velocity (m/s)
    )

    # Define your wind field
    # Direction: 0=East, π/2=North, π=West, -π/2=South
    wind_field = BimodalWindField(
        mode1_params=(
            15,         # Wind speed mode 1 (m/s)
            np.pi/4,    # Wind direction mode 1 (radians)
            3,          # Speed uncertainty (std dev, m/s)
            np.pi/12    # Direction uncertainty (std dev, radians)
        ),
        mode2_params=(
            10,         # Wind speed mode 2 (m/s)
            -np.pi/4,   # Wind direction mode 2 (radians)
            2,          # Speed uncertainty (std dev, m/s)
            np.pi/12    # Direction uncertainty (std dev, radians)
        ),
        mix_weight=0.6  # Probability of mode 1 (0-1)
    )

    print(f"  Custom scenario configured")
    print(f"  Modify the parameters above to create your own scenario")

    fig = visualizer.create_comprehensive_dashboard(
        "Custom Scenario",
        own, intr, wind_field
    )

    plt.savefig('scenario5_custom.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: scenario5_custom.png")
    plt.close()


def run_conflict_analysis_only(own, intr, wind_field, scenario_name="Custom"):
    """
    Helper function: Run conflict analysis without generating full dashboard
    Useful for quick testing or batch processing
    """
    cfg = DAIDALUSConfig()
    detector = ConflictDetection(cfg)
    wind_state = wind_field.to_wind_state()

    print(f"\nConflict Analysis: {scenario_name}")
    print("-" * 60)

    # Deterministic (no wind)
    t_in, t_out = detector.detect_interval(own, intr, 0.0, cfg.LOOKAHEAD_TIME)
    print(f"Deterministic (no wind):")
    if t_in <= t_out:
        print(f"  CONFLICT: t_in={t_in:.1f}s, duration={t_out-t_in:.1f}s")
    else:
        print(f"  No conflict")

    # Probabilistic (with wind)
    altitude_diff = own.z - intr.z
    prob, mean_t_in, mean_t_out, conf_bands = detector.compute_probabilistic_conflict(
        own.position_2d, own.velocity_2d,
        intr.position_2d, intr.velocity_2d,
        wind_state, altitude_diff, n_samples=200
    )

    print(f"Probabilistic (with wind, n=200):")
    print(f"  Conflict probability: {prob:.1%}")
    if mean_t_in > 0:
        print(f"  Mean time to conflict: {mean_t_in:.1f}s")
        if conf_bands:
            print(f"  95% CI: [{conf_bands['t_in_lower']:.1f}s, {conf_bands['t_in_upper']:.1f}s]")


def main():
    """
    Main function - run all scenarios or select specific ones
    """
    print("\n" + "=" * 80)
    print("DAIDALUS Integrated System - Example Scenarios")
    print("=" * 80)
    print("\nGenerating comprehensive dashboards for all scenarios...")
    print("This may take 1-2 minutes depending on your system.\n")

    # Set random seed for reproducibility
    np.random.seed(42)

    # Run all scenarios
    # Comment out scenarios you don't want to run

    scenario_1_head_on_frontal_winds()
    scenario_2_crossing_gusty()  # Main scenario
    scenario_3_parallel_thermal()
    scenario_4_overtaking_mountain_wave()
    scenario_5_custom_template()

    print("\n" + "=" * 80)
    print("All scenarios complete!")
    print("=" * 80)
    print("\nGenerated files:")
    print("  - scenario1_head_on_frontal.png")
    print("  - scenario2_crossing_gusty.png")
    print("  - scenario3_parallel_thermal.png")
    print("  - scenario4_overtaking_mountain.png")
    print("  - scenario5_custom.png")
    print("\n")


if __name__ == "__main__":
    main()
