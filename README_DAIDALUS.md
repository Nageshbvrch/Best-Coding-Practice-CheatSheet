# Enhanced DAIDALUS: Temporal Conflict Analysis with Bimodal Wind Integration

## Overview

This is a comprehensive integration of DAIDALUS (Detect and Avoid Alerting Logic for Unmanned Systems) with advanced temporal conflict analysis and bimodal wind uncertainty modeling. The system provides probabilistic conflict detection with time-varying risk assessment.

## Key Features

### 1. **Bimodal Wind Uncertainty Modeling**
- Realistic atmospheric wind modeling with dual-mode distributions
- Represents complex weather phenomena:
  - Frontal passages (competing wind patterns)
  - Thermal effects (updrafts and downdrafts)
  - Gusty conditions (strong gusts with calm periods)
  - Mountain wave effects (oscillating wind patterns)

### 2. **Temporal Conflict Analysis**
- Time-evolving conflict probability bands
- Tracks how conflict risk changes over the lookahead period
- Identifies optimal maneuver timing

### 3. **Probabilistic Conflict Detection**
- Monte Carlo simulation with wind uncertainty
- Computes conflict probability rather than binary yes/no
- Provides confidence intervals for conflict timing

### 4. **Enhanced Conflict Bands**
- **Heading bands**: Shows safe/unsafe headings evolving over time
- **Speed bands**: Shows safe/unsafe speeds evolving over time
- **Risk classification**: Green (safe), Yellow (low risk), Orange (medium risk), Red (high risk)

### 5. **Comprehensive Dashboard Visualization**
The system generates a 5-panel dashboard showing:

#### Panel 1: Trajectory Uncertainty Envelope
- Mean trajectories for ownship and intruder
- Uncertainty envelope showing possible paths under wind variability
- Well-clear volume visualization
- Altitude indicators (↑ climbing, ↓ descending, → level)

#### Panel 2: Temporal Conflict Probability
- Conflict probability evolution over lookahead time
- Uncertainty range (25th-75th percentile)
- Risk level regions (low/medium/high)

#### Panel 3: Heading Bands Heatmap
- 2D heatmap showing heading (0-360°) vs. time
- Color indicates conflict probability for each heading at each time
- Current heading marked

#### Panel 4: Speed Bands Heatmap
- 2D heatmap showing speed range vs. time
- Color indicates conflict probability for each speed at each time
- Current speed marked

#### Panel 5: Optimal Maneuver Sequence
- Recommended heading changes over time
- Associated risk level for optimal maneuver

## Code Structure

### Core Classes

#### `AircraftState`
Represents aircraft position and velocity in 3D space (North-East-Up coordinates).

```python
@dataclass
class AircraftState:
    x, y, z: float      # Position (m)
    vx, vy, vz: float   # Velocity (m/s)
```

#### `WindState`
Bimodal wind distribution parameters.

```python
@dataclass
class WindState:
    primary_speed, primary_direction, primary_weight: float
    secondary_speed, secondary_direction: float
    speed_uncertainty, direction_uncertainty: float
```

#### `BimodalWindField`
Generates wind samples from bimodal distribution with temporal evolution.

```python
class BimodalWindField:
    def sample_wind_trajectory(n_samples, time_points) -> np.ndarray
    def to_wind_state() -> WindState
```

#### `DAIDALUSConfig`
Configuration parameters for DAIDALUS logic.

```python
class DAIDALUSConfig:
    DMOD = 4000 ft      # Horizontal separation
    ZTHR = 450 ft       # Vertical threshold
    TAUMOD = 35 s       # Modified tau threshold
    LOOKAHEAD_TIME = 120 s
```

#### `ConflictDetection`
Enhanced conflict detection with wind uncertainty.

```python
class ConflictDetection:
    def detect_interval(own, intr) -> (t_in, t_out)
    def detect_conflict_with_wind(own_pos, own_vel, int_pos, int_vel, wind) -> (t_in, t_out)
    def compute_probabilistic_conflict(...) -> (probability, mean_t_in, mean_t_out, confidence_bands)
```

#### `TemporalConflictBands`
Computes time-varying conflict bands.

```python
class TemporalConflictBands:
    def compute_temporal_conflict_probability(...) -> (prob_over_time, lower, upper)
    def compute_heading_bands_temporal(...) -> (headings, temporal_bands)
    def compute_speed_bands_temporal(...) -> (speeds, temporal_bands)
    def find_optimal_maneuver_sequence(...) -> (times, headings, risks)
```

#### `EnhancedDAIDALUSVisualizer`
Creates comprehensive temporal analysis dashboard.

```python
class EnhancedDAIDALUSVisualizer:
    def create_comprehensive_dashboard(scenario_name, own, intr, wind_field) -> fig
```

## Usage

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
import numpy as np
from daidalus_integrated import *

# Initialize configuration
cfg = DAIDALUSConfig()

# Define aircraft states
own = AircraftState(
    x=0, y=0, z=1000,       # Position (m)
    vx=50, vy=0, vz=0.8     # Velocity (m/s)
)

intr = AircraftState(
    x=1000, y=-1000, z=1200,
    vx=0, vy=50, vz=-0.5
)

# Define bimodal wind field
# Mode 1: Strong gusts (70% probability)
# Mode 2: Light winds (30% probability)
wind_field = BimodalWindField(
    mode1_params=(20, np.pi/2, 6, np.pi/8),   # (speed, direction, speed_std, dir_std)
    mode2_params=(5, -np.pi/2, 2, np.pi/12),
    mix_weight=0.7
)

# Create visualizer and generate dashboard
visualizer = EnhancedDAIDALUSVisualizer(cfg)
fig = visualizer.create_comprehensive_dashboard(
    "My Scenario", own, intr, wind_field
)

plt.savefig('output.png', dpi=150)
plt.show()
```

### Running the Demo

```bash
python daidalus_integrated.py
```

This will:
1. Run Scenario 2 (crossing paths with gusty winds)
2. Print conflict analysis results to console
3. Generate comprehensive dashboard
4. Save as `daidalus_integrated_scenario2.png`

## Scenario 2: Crossing Paths with Gusty Winds

**Setup:**
- **Ownship**: Starting at origin, moving north at 50 m/s, climbing at 0.8 m/s from 1000m altitude
- **Intruder**: Starting at (1000m N, -1000m E), moving east at 50 m/s, descending at 0.5 m/s from 1200m altitude
- **Wind**: Bimodal distribution
  - Mode 1 (70%): Strong southerly gusts at 20 m/s ± 6 m/s
  - Mode 2 (30%): Light northerly winds at 5 m/s ± 2 m/s

**Analysis Output:**
- Deterministic conflict detection (no wind)
- Probabilistic conflict probability with wind uncertainty
- Mean time to conflict with confidence intervals
- Comprehensive 5-panel temporal dashboard

## Key Differences from Basic DAIDALUS

| Feature | Basic DAIDALUS | Enhanced DAIDALUS |
|---------|---------------|-------------------|
| Wind modeling | None or single wind vector | Bimodal distribution with uncertainty |
| Conflict output | Binary (yes/no) | Probabilistic (0-100% chance) |
| Time evolution | Single point-in-time | Continuous over lookahead period |
| Bands | Static color regions | Dynamic heatmaps over time |
| Visualization | Simple 2D plot | 5-panel comprehensive dashboard |
| Maneuver guidance | Current safe regions | Optimal sequence over time |

## Configuration Parameters

### DAIDALUS Parameters (DAIDALUSConfig)
- `DMOD = 4000 ft` (1219.2 m): Horizontal separation threshold
- `HMD = 4000 ft` (1219.2 m): Horizontal miss distance
- `ZTHR = 450 ft` (137.2 m): Vertical separation threshold
- `TAUMOD = 35 s`: Modified tau threshold
- `TCOA = 0 s`: Time to co-altitude threshold
- `LOOKAHEAD_TIME = 120 s`: Conflict detection lookahead

### Wind Parameters (WindState / BimodalWindField)
- `primary_speed, secondary_speed`: Wind speeds for two modes (m/s)
- `primary_direction, secondary_direction`: Wind directions (radians, 0=East, π/2=North)
- `primary_weight`: Probability of primary mode (0-1)
- `speed_uncertainty`: Standard deviation of wind speed (m/s)
- `direction_uncertainty`: Standard deviation of wind direction (radians)

### Computational Parameters
- `n_samples`: Number of Monte Carlo samples (default 100-200)
- `n_headings`: Number of heading samples for bands (default 72, 5° resolution)
- `n_speeds`: Number of speed samples for bands (default 30)
- Time sampling: 60 points for temporal analysis, 15 for expensive computations

## Performance Notes

- **Dashboard generation time**: ~5-15 seconds depending on sample sizes
- **Memory usage**: ~100-200 MB for typical scenarios
- **Optimization tips**:
  - Reduce `n_samples` for faster computation (minimum ~50 for reasonable statistics)
  - Use coarser time sampling (time_points[::4]) for expensive operations
  - Reduce heading/speed resolution for faster band computation

## Extending the System

### Adding New Scenarios

```python
def my_custom_scenario():
    cfg = DAIDALUSConfig()
    visualizer = EnhancedDAIDALUSVisualizer(cfg)

    # Define your aircraft states
    own = AircraftState(...)
    intr = AircraftState(...)

    # Define your wind field
    wind_field = BimodalWindField(...)

    # Generate dashboard
    fig = visualizer.create_comprehensive_dashboard(
        "My Custom Scenario", own, intr, wind_field
    )

    plt.savefig('my_scenario.png', dpi=150)
    plt.show()
```

### Modifying Wind Models

You can create different wind scenarios:

**Frontal Passage:**
```python
wind_field = BimodalWindField(
    mode1_params=(15, 0, 3, np.pi/12),        # East wind pre-front
    mode2_params=(20, np.pi, 4, np.pi/10),    # West wind post-front
    mix_weight=0.6
)
```

**Thermal Effects:**
```python
wind_field = BimodalWindField(
    mode1_params=(10, np.pi/4, 2, np.pi/8),   # Updraft convergence
    mode2_params=(8, -np.pi/4, 2, np.pi/8),   # Downdraft divergence
    mix_weight=0.5
)
```

**Mountain Waves:**
```python
wind_field = BimodalWindField(
    mode1_params=(30, np.pi/3, 5, np.pi/12),  # Lee wave updraft
    mode2_params=(30, -np.pi/3, 5, np.pi/12), # Lee wave downdraft
    mix_weight=0.5
)
```

## Output Files

Running the demo generates:
- `daidalus_integrated_scenario2.png`: Comprehensive 5-panel dashboard
- Console output with detailed conflict analysis

## Dependencies

- **numpy**: Numerical computations and array operations
- **matplotlib**: Visualization and plotting
- **seaborn**: Enhanced color palettes (optional but recommended)
- **scipy**: Statistical functions (used in confidence interval computation)

## References

- DAIDALUS Specification (NASA)
- Original temporal conflict analysis code
- Bimodal wind uncertainty modeling implementation

## License

This integrated implementation combines elements from multiple DAIDALUS implementations and is provided for educational and research purposes.

## Authors

Integration of temporal conflict analysis with bimodal wind uncertainty modeling for enhanced DAIDALUS system.

---

**Version**: 1.0
**Last Updated**: 2025
**Status**: Production-ready for Scenario 2, extensible to additional scenarios
