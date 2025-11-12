# DAIDALUS Visualization Updates

## Overview
This document describes the updates made to the DAIDALUS (Detect and Avoid Alerting Logic for Unmanned Systems) visualization system.

## Latest Updates (v2)

### **Aircraft Symbols**
- ✈ **Airplane symbols** now used instead of dots for both ownship and intruder
- Color-coded based on altitude changes:
  - **Blue ✈**: Climbing aircraft
  - **Orange ✈**: Descending aircraft
  - **Gray ✈**: Level flight
- Font configuration added to support Unicode airplane symbol without warnings

### **Fixed Conflict Band Logic**
The conflict bands now correctly start **ALL GREEN** when the intruder is far away and transition colors as it approaches:
- **When starting** (intruder 8km away): ALL bands are GREEN
- **As intruder approaches SST**: Conflict directions turn AMBER
- **When near WCV**: Conflict directions turn RED

This is based on the **CURRENT distance** of the intruder, not predicted closest approach, providing more intuitive and realistic behavior.

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

### Distance-Based Band Coloring (v2 Logic)
```python
# Calculate CURRENT distance from ownship to intruder
current_distance = np.linalg.norm(own.position_2d - intr.position_2d)

# Determine threat level based on CURRENT distance
if current_distance > SST_RADIUS:
    threat_level = "SAFE"       # ALL bands green
elif current_distance > WCV_RADIUS:
    threat_level = "CAUTION"    # Conflict bands amber
else:
    threat_level = "DANGER"     # Conflict bands red

# Apply colors to each direction based on conflict + threat level
if conflict_exists:
    if threat_level == "SAFE":
        color = LIGHT_GREEN  # Even conflicts are green when far
    elif threat_level == "CAUTION":
        color = AMBER        # Conflicts are amber when approaching
    else:
        color = RED          # Conflicts are red when close
else:
    color = GREEN           # No conflict = green
```

### Aircraft Symbol Configuration
```python
# Font configuration to support ✈ symbol
matplotlib.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]

# Create airplane markers as text annotations
own_marker = ax.text(0, 0, '✈', fontsize=24, ha='center', va='center')
int_marker = ax.text(0, 0, '✈', fontsize=24, ha='center', va='center')
```

### Key Features
1. **Real-time updates**: Circles and bands move with the ownship
2. **Airplane symbols**: Clear ✈ symbols for ownship and intruder aircraft
3. **Altitude awareness**: Color-coded aircraft symbols show climb/descent status (Blue↑ Orange↓ Gray→)
4. **Comprehensive information**: Displays ground speed, altitude, separation distances
5. **Clear visual hierarchy**: Color intensity indicates threat level
6. **Distance-based bands**: Bands correctly reflect current threat level, not future predictions

## Usage

### Running the Visualization
```python
python daidalus_visualization.py
```

### Requirements
```python
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from matplotlib.animation import FuncAnimation

# Font configuration for airplane symbols
matplotlib.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]
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
2. ✅ **Clear visual markers**: Airplane symbols (✈) immediately recognizable
3. ✅ **Correct band behavior**: Bands start green when far away, transition as intruder approaches
4. ✅ **Clear documentation**: All circles and bands explained outside the plot
5. ✅ **Realistic behavior**: Matches real-world collision avoidance systems
6. ✅ **Equal scaling**: Proper geometric representation with equal axis dimensions
7. ✅ **Comprehensive legend**: All information accessible without cluttering the plot
8. ✅ **No font warnings**: Proper font configuration for Unicode symbols

## References
- DAIDALUS: NASA's Detect and Avoid Alerting Logic for Unmanned Systems
- Well-Clear concept: Minimum safe separation for aircraft
- Conflict bands: Visual representation of safe/unsafe headings
