# DAIDALUS Complete Visualization System

## Overview
Complete implementation of DAIDALUS (Detect and Avoid Alerting Logic for Unmanned Systems) with all requested features including conflict bands, airplane symbols, position tracking, and dynamic status updates.

## ✅ All Features Implemented

### 1. **Conflict Bands** ✈️
- **GREEN bands**: Intruder far away (beyond SST) - Safe to fly
- **AMBER bands**: Intruder approaching (within SST, outside WCV) - Caution
- **RED bands**: Intruder close (near/within WCV) - Danger

The conflict bands show you which directions are safe or unsafe to fly based on the intruder's current distance.

### 2. **SST and WCV Circles** 🎯
- **SST (Self-Separation Threshold)**: Blue dotted circle (1219m radius)
  - Safe separation distance
  - When intruder crosses: **"CONFLICT DETECTED"** appears

- **WCV (Well-Clear Violation)**: Red solid circle (853m radius)
  - Minimum safe distance
  - When intruder crosses: **"⚠️ WARNING"** appears

### 3. **All Legends and Text Outside Plot** 📋
- **Right side legend**: Explains all symbols and circles
- **Top banner**: Shows current status and separations
- **Right side panel**: Real-time position tracking with (x, y, z) coordinates
- **Bottom annotation**: Explains conflict band behavior
- **Plot area**: Clean, only shows aircraft, circles, and bands

### 4. **SST/WCV Abbreviations Displayed**
- SST clearly labeled as "Self-Separation Threshold"
- WCV clearly labeled as "Well-Clear Violation"
- Both shown in legend with full names and abbreviations

### 5. **Position Tracking (x, y, z)** 📍

The right panel displays real-time positions:

```
POSITIONS & VELOCITIES
===================================

OWNSHIP:
  Position: (0, 0, 1000)m
  Ground Speed: 0.0 m/s
  Vert. Speed: +0.0 m/s

INTRUDER:
  Position: (0, 2250, 1000)m
  Ground Speed: 25.0 m/s
  Vert. Speed: +0.0 m/s

SEPARATION:
  Horizontal: 2250m
  Vertical: 0m

TIME: 30.0s
```

**Key moments tracked:**
- **When intruder touches SST**: Shows exact positions at conflict detection
- **When intruder touches WCV**: Shows exact positions at warning
- **Continuous updates**: Every frame shows current (x, y, z)

### 6. **Optimized Axes Configuration** 📊

#### Vertical Approach Scenario (Default)
```python
X-axis (East):  -4000 to 4000m (500-unit increments)
Y-axis (North): -2000 to 2000m (500-unit increments)
```
Perfect for showing intruder approaching from the side

#### Head-On Scenario
```python
X-axis (East):  -2000 to 2000m (500-unit increments)
Y-axis (North): -2000 to 8000m (500-unit increments)
```
Perfect for showing intruder approaching head-on

**All scenarios use 500-unit increments for clear visualization!**

### 7. **Status Changes Based on Distance** 🚦

The top banner changes based on intruder distance:

| Distance | Status | Color | Message |
|----------|--------|-------|---------|
| > SST (>1219m) | Safe | Green | "✓ NO CONFLICT DETECTED" |
| ≤ SST, > WCV | Caution | Yellow | "⚠️ CONFLICT DETECTED - WITHIN SST" |
| ≤ WCV (≤853m) | Warning | Red | "⚠️ WARNING - WITHIN WCV" |

### 8. **Ground Speed (GS) Displayed Outside Plot** 📈

Ground speeds are shown in the **right side panel**:
- Ownship GS: Displayed with position info
- Intruder GS: Displayed with position info
- Both update in real-time
- Plot area remains clean with only moving aircraft

### 9. **Airplane Symbols (Arrows)** ✈️

- **Ownship**: Blue arrow pointing in direction of travel
- **Intruder**: Orange arrow pointing in direction of travel
- Arrow length: 200m (proportional to visibility)
- Both arrows dynamically rotate based on velocity direction
- Clear, intuitive representation

## Usage

### Running the Default Scenario (Vertical Approach)

```bash
python daidalus_complete_visualization.py
```

This creates an animation where:
- Ownship is stationary at (0, 0, 1000)
- Intruder starts at (0, 3000, 1000) and approaches at 25 m/s
- Shows intruder going from far away → SST → WCV → past ownship → away

### Choosing Different Scenarios

Edit the last section of the code:

```python
# Vertical approach (default)
ani, viz = create_animation_scenario(scenario_type="vertical")

# Head-on encounter
ani, viz = create_animation_scenario(scenario_type="head_on")

# Crossing paths
ani, viz = create_animation_scenario(scenario_type="crossing")
```

### Custom Scenarios

Create your own by modifying the aircraft states:

```python
own = AircraftState(
    x=0,      # North position (m)
    y=0,      # East position (m)
    z=1000,   # Altitude (m)
    vx=0,     # North velocity (m/s)
    vy=0,     # East velocity (m/s)
    vz=0      # Vertical speed (m/s)
)

intr = AircraftState(
    x=0,      # North position (m)
    y=3000,   # East position (m) - 3km away
    z=1000,   # Altitude (m)
    vx=0,     # North velocity (m/s)
    vy=-25,   # East velocity (m/s) - approaching
    vz=0      # Vertical speed (m/s)
)
```

### Setting Custom Axes

```python
# For your specific scenario, adjust the axes:
viz.ax.set_xlim(-4000, 4000)  # East direction
viz.ax.set_ylim(-2000, 2000)  # North direction

# Set 500-unit increments
x_ticks = np.arange(-4000, 4500, 500)
y_ticks = np.arange(-2000, 2500, 500)
viz.ax.set_xticks(x_ticks)
viz.ax.set_yticks(y_ticks)
```

## Output

**Generated file**: `daidalus_complete_animation.gif`
- 300 frames
- 20 fps
- Shows complete scenario from start to finish

## Visualization Breakdown

### Plot Area (Clean - 65% of figure)
- Moving aircraft (arrows)
- SST circle (blue dotted)
- WCV circle (red solid)
- Conflict bands (colored wedges)

### Right Panel (35% of figure)
- **Top section**: Positions and velocities with (x, y, z)
- **Middle section**: Complete legend with SST/WCV explanations
- **Bottom section**: Ground speeds and configuration

### Top Banner
- Current status (No Conflict / Conflict / Warning)
- Time to violation
- Current separations (horizontal and vertical)
- Current simulation time

### Bottom Annotation
- Explanation of conflict band color transitions

## Key Behavior

### Scenario Timeline

1. **Start (t=0s)**: Intruder far away
   - Status: "✓ NO CONFLICT DETECTED"
   - Bands: ALL GREEN
   - Position: (0, 3000, 1000)

2. **Approaching SST (t≈45s)**: Intruder at 1219m
   - Status: "⚠️ CONFLICT DETECTED - WITHIN SST"
   - Bands: Conflict directions turn AMBER
   - Position tracked in real-time

3. **Reaching WCV (t≈85s)**: Intruder at 853m
   - Status: "⚠️ WARNING - WITHIN WCV"
   - Bands: Conflict directions turn RED
   - Position tracked in real-time

4. **Passing Through (t≈120s)**: Intruder passes ownship
   - Bands transition back through RED → AMBER → GREEN
   - Shows intruder going away

5. **Departed (t=120s+)**: Intruder far away again
   - Status: "✓ NO CONFLICT DETECTED"
   - Bands: ALL GREEN

## Requirements

```python
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge, FancyArrow
from matplotlib.animation import FuncAnimation
```

Install with:
```bash
pip install numpy matplotlib pillow
```

## Configuration

Modify `DAIDALUSConfig` class to adjust:
- `LOOKAHEAD_TIME`: How far ahead to predict (default: 120s)
- `DMOD`: SST radius in feet (default: 4000 ft = 1219m)
- `WCV_RADIUS`: 0.7 × SST (default: 853m)
- `TRACK_STEP_DEG`: Conflict band resolution (default: 5°)

## Advanced Features

### Animation Speed
```python
# Faster animation (more fps)
ani.save('output.gif', writer='pillow', fps=30)

# Slower animation (less fps)
ani.save('output.gif', writer='pillow', fps=10)
```

### More Frames (Smoother)
```python
times = np.linspace(0, cfg.LOOKAHEAD_TIME, 500)  # 500 frames instead of 300
```

### Different Output Formats
```python
# Save as MP4 (requires ffmpeg)
ani.save('output.mp4', writer='ffmpeg', fps=20)

# Save as individual frames
for i, t in enumerate(times):
    viz.update(t, own, intr, det)
    plt.savefig(f'frame_{i:04d}.png', dpi=150, bbox_inches='tight')
```

## Next Steps: RRT* Integration

This visualization is ready for RRT* path planning integration:

1. **Safe directions**: Use GREEN bands to expand tree
2. **Avoid directions**: Don't expand into RED bands
3. **Caution zones**: Apply higher cost to AMBER bands
4. **Dynamic replanning**: Update bands as aircraft move

The conflict bands provide real-time guidance for path planning algorithms to avoid conflicts while finding optimal routes.

## Troubleshooting

### "Animation is too fast"
- Reduce fps: `ani.save(..., fps=10)`
- Increase frames: `times = np.linspace(0, cfg.LOOKAHEAD_TIME, 500)`

### "Can't see the intruder approach clearly"
- Adjust axis limits to zoom in on action area
- Use 500-unit increments (already default)

### "Conflict bands not appearing"
- Check that intruder is within LOOKAHEAD_TIME range
- Verify velocities are non-zero
- Ensure aircraft are on collision course

### "Position text is cut off"
- Increase figure width: `figsize=(20, 10)`
- Adjust text position: `self.fig.text(0.70, 0.75, ...)`

## Summary of All Requirements Met

✅ 1. Conflict bands created (green → amber → red)
✅ 2. Focus on SST/WCV circles with color changes
✅ 3. All legends and text outside plot
✅ 4. SST, WCV abbreviations shown
✅ 5. Position (x, y, z) tracking displayed
✅ 6. Optimized axes with 500-unit increments
✅ 7. Status changes (No Conflict → Conflict → Warning)
✅ 8. GS displayed outside in text panel
✅ 9. Airplane symbols (arrows) showing direction

**Ready for demonstration and RRT* path planning integration!** 🚀
