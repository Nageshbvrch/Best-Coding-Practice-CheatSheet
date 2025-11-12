# DAIDALUS Visualization Updates

## Overview
This document describes the updates made to the DAIDALUS (Detect and Avoid Alerting Logic for Unmanned Systems) visualization system.

## Key Changes

### 1. **Axes Configuration**
- **X-axis and Y-axis**: Now range from **-2000 to 6000 meters**
- **Increment**: **500-unit intervals** for both axes
- **Equal dimensions**: Both axes have the same scale for proper geometric representation

### 2. **Legend and Text Positioning**
All legends and text annotations are now positioned **OUTSIDE** the plot area:
- **Legend**: Positioned on the right side of the plot (70% plot width, 30% legend)
- **Status Banner**: Positioned at the top of the figure, outside the plot
- **Annotations**: Positioned at the bottom of the figure with explanation text

### 3. **Ownship Circles**

The visualization clearly shows two circles around the ownship:

#### **SST (Self-Separation Threshold)**
- **Color**: Blue dotted line
- **Radius**: 1219m (4000 ft converted)
- **Purpose**: Safe separation distance - intruders beyond this are considered safe
- **Description**: Displayed in legend outside the plot

#### **WCV (Well-Clear Violation Volume)**
- **Color**: Red solid line
- **Radius**: 853m (0.7 × SST radius)
- **Purpose**: Minimum safe distance - intruders within this are in danger zone
- **Description**: Displayed in legend outside the plot

### 4. **Conflict Band Colors (Distance-Based)**

The conflict bands now change color based on the **actual distance** of the intruder from the ownship, not time-based thresholds:

#### **🟢 GREEN (Safe)**
- **Condition**: Intruder is **far away**, beyond the SST circle
- **Meaning**: No immediate threat, ownship can safely maintain this heading
- **Visual**: Forest green, moderate opacity

#### **🟡 AMBER (Caution)**
- **Condition**: Intruder is **approaching the SST circle** but still **outside the WCV circle**
- **Meaning**: Caution required, intruder entering the separation threshold
- **Visual**: Amber/orange color, medium opacity
- **Transition**: Appears as intruder crosses into SST radius

#### **🔴 RED (Danger)**
- **Condition**: Intruder is **near or within the WCV circle**
- **Meaning**: Immediate danger, well-clear violation imminent or occurring
- **Visual**: Crimson red, higher opacity
- **Transition**: Appears as intruder approaches WCV radius

### 5. **Dynamic Color Transitions**

The visualization demonstrates realistic conflict band behavior:

```
Distance from Ownship:

    > SST_RADIUS (>1219m)  ──→  GREEN band   (Safe)
                    ↓
    ≤ SST_RADIUS (≤1219m)  ──→  AMBER band   (Approaching)
                    ↓
    ≤ WCV_RADIUS (≤853m)   ──→  RED band     (Danger)
```

## Implementation Details

### Distance Calculation
```python
# Calculate closest approach distance for each heading
closest_distance = GeometricUtils.dcpa(s, v)

# Color assignment based on distance thresholds
if closest_distance <= WCV_RADIUS:
    color = RED      # Danger
elif closest_distance <= SST_RADIUS:
    color = AMBER    # Caution
else:
    color = GREEN    # Safe
```

### Key Features
1. **Real-time updates**: Circles and bands move with the ownship
2. **Altitude awareness**: Aircraft markers show climb/descent status (↑↓→)
3. **Comprehensive information**: Displays ground speed, altitude, separation distances
4. **Clear visual hierarchy**: Color intensity indicates threat level

## Usage

### Running the Visualization
```python
python daidalus_visualization.py
```

### Requirements
```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from matplotlib.animation import FuncAnimation
```

### Output
- Generates an animated GIF: `daidalus_animation.gif`
- Shows real-time conflict band updates as aircraft approach
- Displays dynamic color transitions from green → amber → red

## Scenario
The default scenario simulates:
- **Ownship**: Starting at origin (0, 0), altitude 1000m, moving north at 50 m/s, climbing
- **Intruder**: Starting 8km north, altitude 1200m, moving south at 45 m/s, descending
- **Result**: Head-on approach demonstrating all three color phases

## Benefits
1. ✅ **Intuitive understanding**: Colors directly represent distance-based threat levels
2. ✅ **Clear documentation**: All circles and bands explained outside the plot
3. ✅ **Realistic behavior**: Matches real-world collision avoidance systems
4. ✅ **Equal scaling**: Proper geometric representation with equal axis dimensions
5. ✅ **Comprehensive legend**: All information accessible without cluttering the plot

## References
- DAIDALUS: NASA's Detect and Avoid Alerting Logic for Unmanned Systems
- Well-Clear concept: Minimum safe separation for aircraft
- Conflict bands: Visual representation of safe/unsafe headings
