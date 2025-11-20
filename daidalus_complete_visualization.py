"""
DAIDALUS (Detect and Avoid Alerting Logic for Unmanned Systems)
Complete visualization with conflict bands, airplane symbols, and position tracking

FEATURES:
- Conflict bands (green → amber → red based on distance)
- Airplane symbols (arrows pointing in direction of travel)
- SST and WCV circles
- Position tracking (x, y, z) displayed outside plot
- Status changes based on proximity to SST/WCV
- All legends and text outside plot area
- 500-unit axis increments
"""

import numpy as np
import math
from dataclasses import dataclass
from typing import Tuple, List
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge, FancyArrow
from matplotlib.animation import FuncAnimation

# Use system fallback fonts to avoid warnings
matplotlib.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]

# ---------------------------
# Aircraft state
# ---------------------------
@dataclass
class AircraftState:
    """Aircraft state representation in 3D Euclidean space"""
    x: float  # North (m)
    y: float  # East (m)
    z: float  # Altitude (m)
    vx: float  # North velocity (m/s)
    vy: float  # East velocity (m/s)
    vz: float  # Vertical speed (m/s)

    @property
    def ground_speed(self) -> float:
        return math.hypot(self.vx, self.vy)

    @property
    def track(self) -> float:
        epsilon = 1e-9
        return math.atan2(self.vy, self.vx + epsilon)

    @property
    def position_2d(self) -> np.ndarray:
        return np.array([self.x, self.y])

    @property
    def velocity_2d(self) -> np.ndarray:
        return np.array([self.vx, self.vy])


# ---------------------------
# Config
# ---------------------------
class DAIDALUSConfig:
    """DAIDALUS configuration parameters"""
    DMOD = 4000.0    # ft - SST (Self-Separation Threshold)
    HMD = 4000.0     # ft
    ZTHR = 450.0     # ft
    TAUMOD = 35.0    # s
    TCOA = 0.0       # s
    LOOKAHEAD_TIME = 120.0  # seconds

    # Band sampling
    TRACK_STEP_DEG = 5  # degrees
    BAND_INNER_M = 250  # visualization ring thickness
    BAND_OUTER_M = 450

    def __init__(self):
        ft2m = 0.3048
        self.DMOD *= ft2m
        self.HMD *= ft2m
        self.ZTHR *= ft2m
        self.SST_RADIUS = self.DMOD  # Blue dotted circle
        self.WCV_RADIUS = 0.7 * self.DMOD  # Red circle


# ---------------------------
# Geometry helpers
# ---------------------------
class GeometricUtils:
    @staticmethod
    def horizontal_range(s: np.ndarray, v: np.ndarray, t: float) -> float:
        return np.linalg.norm(s + t * v)

    @staticmethod
    def time_to_cpa(s: np.ndarray, v: np.ndarray) -> float:
        v2 = np.dot(v, v)
        if v2 == 0.0:
            return 0.0
        t = -np.dot(s, v) / v2
        return max(0.0, t)

    @staticmethod
    def dcpa(s: np.ndarray, v: np.ndarray) -> float:
        t = GeometricUtils.time_to_cpa(s, v)
        return GeometricUtils.horizontal_range(s, v, t)

    @staticmethod
    def time_to_coaltitude(sz: float, vz: float) -> float:
        if sz * vz < 0.0:
            return -sz / vz
        return -1.0

    @staticmethod
    def modified_tau(s: np.ndarray, v: np.ndarray, dmod: float) -> float:
        s_dot_v = np.dot(s, v)
        if s_dot_v < 0.0:
            s2 = np.dot(s, s)
            return (dmod**2 - s2) / s_dot_v
        return -1.0


# ---------------------------
# WCV logic
# ---------------------------
class WellClearLogic:
    def __init__(self, cfg: DAIDALUSConfig):
        self.cfg = cfg

    def horizontal_wcv(self, s: np.ndarray, v: np.ndarray) -> bool:
        if np.linalg.norm(s) <= self.cfg.DMOD:
            return True
        dcpa = GeometricUtils.dcpa(s, v)
        tau = GeometricUtils.modified_tau(s, v, self.cfg.DMOD)
        return (dcpa <= self.cfg.HMD) and (0 <= tau <= self.cfg.TAUMOD)

    def vertical_wcv(self, sz: float, vz: float) -> bool:
        if abs(sz) <= self.cfg.ZTHR:
            return True
        tcoa = GeometricUtils.time_to_coaltitude(sz, vz)
        return (0 <= tcoa <= self.cfg.TCOA)

    def well_clear_violation(self, own: AircraftState, intr: AircraftState) -> bool:
        s = own.position_2d - intr.position_2d
        v = own.velocity_2d - intr.velocity_2d
        sz = own.z - intr.z
        vz = own.vz - intr.vz
        return self.horizontal_wcv(s, v) and self.vertical_wcv(sz, vz)


# ---------------------------
# Conflict detection
# ---------------------------
class ConflictDetection:
    def __init__(self, cfg: DAIDALUSConfig):
        self.cfg = cfg
        self.wcv = WellClearLogic(cfg)

    def vertical_entry_exit(self, sz: float, vz: float, t0: float, t1: float) -> Tuple[float, float]:
        if abs(vz) < 1e-6:
            return (t0, t1) if abs(sz) <= self.cfg.ZTHR else (-1.0, -1.0)
        H = max(self.cfg.ZTHR, self.cfg.TCOA * abs(vz))
        sign = 1.0 if vz >= 0 else -1.0
        t_in = (-sign * H - sz) / vz
        t_out = (sign * H - sz) / vz
        if t_in > t_out:
            t_in, t_out = t_out, t_in
        if t1 < t_in or t_out < t0:
            return (-1.0, -1.0)
        return (max(t0, t_in), min(t1, t_out))

    def horizontal_entry_exit(self, s: np.ndarray, v: np.ndarray, span: float) -> Tuple[float, float]:
        if np.linalg.norm(s) <= self.cfg.DMOD:
            tau = GeometricUtils.modified_tau(s, v, self.cfg.DMOD)
            t_out = min(span, tau) if tau > 0 else span
            return (0.0, t_out)

        sdotv = np.dot(s, v)
        v2 = np.dot(v, v)
        if (sdotv >= 0) or (v2 == 0):
            return (-1.0, -1.0)

        a = v2
        b = 2*sdotv + self.cfg.TAUMOD * v2
        c = np.dot(s, s) + self.cfg.TAUMOD * sdotv - self.cfg.DMOD**2
        disc = b*b - 4*a*c
        if disc < 0:
            return (-1.0, -1.0)
        t_in = (-b - math.sqrt(disc)) / (2*a)
        if not (0 <= t_in <= span):
            return (-1.0, -1.0)
        tau = GeometricUtils.modified_tau(s, v, self.cfg.DMOD)
        t_out = min(span, tau) if tau > 0 else span
        return (t_in, t_out)

    def detect_interval(self, own: AircraftState, intr: AircraftState,
                        t0: float = 0.0, t1: float = None) -> Tuple[float, float]:
        if t1 is None:
            t1 = self.cfg.LOOKAHEAD_TIME
        s = own.position_2d - intr.position_2d
        v = own.velocity_2d - intr.velocity_2d
        sz = own.z - intr.z
        vz = own.vz - intr.vz

        v_in, v_out = self.vertical_entry_exit(sz, vz, t0, t1)
        if v_in < 0 or v_out < 0 or v_in > v_out:
            return (t1, t0)

        span = v_out - v_in
        s_at_vin = s + v_in * v
        h_in, h_out = self.horizontal_entry_exit(s_at_vin, v, span)
        if h_in < 0 or h_out < 0:
            return (t1, t0)

        return (v_in + h_in, v_in + h_out)


# ---------------------------
# Visualization + Bands
# ---------------------------
class DAIDALUSVisualizer:
    def __init__(self, cfg: DAIDALUSConfig):
        self.cfg = cfg
        # Create figure with extra space for legends and text outside
        self.fig = plt.figure(figsize=(18, 10))
        # Main plot takes up left 65% of figure
        self.ax = self.fig.add_axes([0.08, 0.12, 0.55, 0.78])
        self._setup_axes()

        # Animated artists - airplane symbols
        self.own_arrow = None
        self.int_arrow = None

        # Well-clear circles
        self.sst_circle = Circle((0, 0), self.cfg.SST_RADIUS, fill=False, ls='--',
                                lw=2, ec='tab:blue', alpha=0.7, label='SST')
        self.wcv_circle = Circle((0, 0), self.cfg.WCV_RADIUS, fill=False,
                                lw=2, ec='tab:red', alpha=0.8, label='WCV')
        self.ax.add_patch(self.sst_circle)
        self.ax.add_patch(self.wcv_circle)

        # Conflict bands container
        self.band_patches: List[Wedge] = []

        # Status banner - positioned outside plot at top
        self.banner = self.fig.text(0.40, 0.95, '', ha='center', va='top',
                                   fontsize=12, fontweight='bold',
                                   bbox=dict(boxstyle="round,pad=0.6", fc='lightgreen', alpha=0.9))

        # Position information - RIGHT SIDE
        self.position_text = self.fig.text(0.68, 0.75, '', ha='left', va='top',
                                          fontsize=10, family='monospace',
                                          bbox=dict(boxstyle="round,pad=0.8", fc='lightyellow',
                                                   ec='black', alpha=0.95))

        # Legend positioned outside plot area on the right side
        self._create_legend()

        # Additional text explanations below the plot
        self._create_text_annotations()

    def _setup_axes(self):
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel("East (m)", fontsize=12, fontweight='bold')
        self.ax.set_ylabel("North (m)", fontsize=12, fontweight='bold')
        self.ax.set_title("DAIDALUS Collision Avoidance — Distance-Based Conflict Bands",
                         fontsize=14, fontweight='bold')

    def _create_legend(self):
        """Create comprehensive legend outside the plot area"""
        legend_x = 0.68
        legend_y = 0.50

        legend_text = (
            "LEGEND\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "CIRCLES:\n"
            f"● SST (Blue --): Self-Separation\n"
            f"   Threshold = {self.cfg.SST_RADIUS:.0f}m\n\n"
            f"● WCV (Red —): Well-Clear\n"
            f"   Violation = {self.cfg.WCV_RADIUS:.0f}m\n\n"
            "CONFLICT BANDS:\n"
            "● GREEN: Safe\n"
            "   Intruder beyond SST\n\n"
            "● AMBER: Caution\n"
            "   Within SST, outside WCV\n\n"
            "● RED: Danger\n"
            "   Near or within WCV\n\n"
            "AIRCRAFT:\n"
            "● Blue arrow: Ownship\n"
            "● Orange arrow: Intruder\n\n"
            f"Lookahead: {self.cfg.LOOKAHEAD_TIME:.0f}s"
        )

        self.legend_text = self.fig.text(
            legend_x, legend_y, legend_text,
            va='top', ha='left', fontsize=9,
            bbox=dict(boxstyle="round,pad=0.8", fc='lightcyan',
                     ec='black', alpha=0.95),
            family='monospace'
        )

    def _create_text_annotations(self):
        """Create text annotations below the plot"""
        annotation_text = (
            "Conflict Band Behavior: GREEN (far from SST) → AMBER (approaching SST) → RED (near/within WCV)"
        )

        self.annotation = self.fig.text(
            0.35, 0.04, annotation_text,
            ha='center', va='center', fontsize=10, style='italic',
            bbox=dict(boxstyle="round,pad=0.5", fc='wheat', alpha=0.8)
        )

    @staticmethod
    def _rotate_to_track(speed: float, track_rad: float) -> np.ndarray:
        vx = speed * math.cos(track_rad)
        vy = speed * math.sin(track_rad)
        return np.array([vx, vy])

    def draw_track_bands(self, own: AircraftState, intr: AircraftState, detector: ConflictDetection):
        """Draw conflict bands with distance-based color transitions"""
        # Clear existing wedges
        for p in self.band_patches:
            p.remove()
        self.band_patches.clear()

        center = (own.y, own.x)
        inner_r, outer_r = self.cfg.BAND_INNER_M, self.cfg.BAND_OUTER_M

        # Current distance from ownship to intruder
        current_distance = np.linalg.norm(own.position_2d - intr.position_2d)

        # Determine threat level based on CURRENT distance
        if current_distance > self.cfg.SST_RADIUS:
            threat_level = "SAFE"
        elif current_distance > self.cfg.WCV_RADIUS:
            threat_level = "CAUTION"
        else:
            threat_level = "DANGER"

        for deg in range(0, 360, self.cfg.TRACK_STEP_DEG):
            theta = math.radians(deg)
            v2d = self._rotate_to_track(own.ground_speed, theta)
            hypo = AircraftState(own.x, own.y, own.z, v2d[0], v2d[1], own.vz)

            t_in, t_out = detector.detect_interval(hypo, intr, 0.0, self.cfg.LOOKAHEAD_TIME)

            # Distance-based color classification
            if t_in <= t_out:  # Conflict exists
                if threat_level == "SAFE":
                    color = '#90EE90'  # Light green
                    alpha = 0.5
                elif threat_level == "CAUTION":
                    color = '#FFB000'  # Amber
                    alpha = 0.6
                else:  # DANGER
                    color = '#DC143C'  # Crimson red
                    alpha = 0.7
            else:
                if threat_level == "SAFE":
                    color = '#228B22'  # Forest green
                    alpha = 0.5
                elif threat_level == "CAUTION":
                    color = '#90EE90'  # Light green
                    alpha = 0.5
                else:  # DANGER
                    color = '#FFD700'  # Gold
                    alpha = 0.5

            # Draw wedge
            start = 90 - deg - self.cfg.TRACK_STEP_DEG/2
            end = 90 - deg + self.cfg.TRACK_STEP_DEG/2
            w = Wedge(center, outer_r, start, end, width=outer_r-inner_r,
                     color=color, alpha=alpha, ec='white', linewidth=0.3, zorder=1)
            self.ax.add_patch(w)
            self.band_patches.append(w)

    def update(self, t: float, own0: AircraftState, intr0: AircraftState, detector: ConflictDetection):
        """Update frame"""
        own = AircraftState(own0.x + own0.vx*t, own0.y + own0.vy*t, own0.z + own0.vz*t,
                            own0.vx, own0.vy, own0.vz)
        intr = AircraftState(intr0.x + intr0.vx*t, intr0.y + intr0.vy*t, intr0.z + intr0.vz*t,
                             intr0.vx, intr0.vy, intr0.vz)

        # Calculate current separation
        horiz_sep = np.linalg.norm(own.position_2d - intr.position_2d)
        vert_sep = abs(own.z - intr.z)

        # Move circles to ownship
        self.sst_circle.center = (own.y, own.x)
        self.wcv_circle.center = (own.y, own.x)

        # Update airplane arrows
        if self.own_arrow:
            self.own_arrow.remove()
        if self.int_arrow:
            self.int_arrow.remove()

        # Ownship arrow
        arrow_len = 200
        if own.ground_speed > 1e-6:
            dx = own.vx / own.ground_speed * arrow_len
            dy = own.vy / own.ground_speed * arrow_len
            self.own_arrow = FancyArrow(
                own.y - dy, own.x - dx, dy, dx,
                head_width=50, head_length=60,
                fc='blue', ec='black', linewidth=2, alpha=0.8, zorder=10
            )
            self.ax.add_patch(self.own_arrow)

        # Intruder arrow
        if intr.ground_speed > 1e-6:
            dx = intr.vx / intr.ground_speed * arrow_len
            dy = intr.vy / intr.ground_speed * arrow_len
            self.int_arrow = FancyArrow(
                intr.y - dy, intr.x - dx, dy, dx,
                head_width=50, head_length=60,
                fc='orange', ec='black', linewidth=2, alpha=0.8, zorder=10
            )
            self.ax.add_patch(self.int_arrow)

        # Update position information - RIGHT SIDE
        position_info = (
            f"POSITIONS & VELOCITIES\n"
            f"{'='*35}\n\n"
            f"OWNSHIP:\n"
            f"  Position: ({own.x:.0f}, {own.y:.0f}, {own.z:.0f})m\n"
            f"  Ground Speed: {own.ground_speed:.1f} m/s\n"
            f"  Vert. Speed: {own.vz:+.1f} m/s\n\n"
            f"INTRUDER:\n"
            f"  Position: ({intr.x:.0f}, {intr.y:.0f}, {intr.z:.0f})m\n"
            f"  Ground Speed: {intr.ground_speed:.1f} m/s\n"
            f"  Vert. Speed: {intr.vz:+.1f} m/s\n\n"
            f"SEPARATION:\n"
            f"  Horizontal: {horiz_sep:.0f}m\n"
            f"  Vertical: {vert_sep:.0f}m\n\n"
            f"TIME: {t:.1f}s"
        )
        self.position_text.set_text(position_info)

        # Detect conflict
        t_in, t_out = detector.detect_interval(own, intr, 0.0, detector.cfg.LOOKAHEAD_TIME)

        # Status banner with distance-based severity
        if horiz_sep <= self.cfg.WCV_RADIUS:
            severity = "⚠️ WARNING - WITHIN WCV"
            bg_color = '#FF6B6B'  # Red
        elif horiz_sep <= self.cfg.SST_RADIUS:
            severity = "⚠️ CONFLICT DETECTED - WITHIN SST"
            bg_color = '#FFE66D'  # Yellow
        else:
            severity = "✓ NO CONFLICT DETECTED"
            bg_color = '#A8E6CF'  # Light green

        if t_in <= t_out:
            self.banner.set_text(
                f"{severity}\n"
                f"Time to violation: {t_in:.1f}s | Duration: {t_out-t_in:.1f}s | "
                f"Horiz: {horiz_sep:.0f}m | Vert: {vert_sep:.0f}m"
            )
        else:
            self.banner.set_text(
                f"{severity}\n"
                f"Horiz. sep: {horiz_sep:.0f}m | Vert. sep: {vert_sep:.0f}m | Time: {t:.1f}s"
            )
        self.banner.set_bbox(dict(boxstyle="round,pad=0.6", fc=bg_color, alpha=0.9))

        # Draw conflict bands
        self.draw_track_bands(own, intr, detector)

        return [self.own_arrow, self.int_arrow, self.sst_circle, self.wcv_circle,
                self.banner, *self.band_patches]


# ---------------------------
# Animation scenario
# ---------------------------
def create_animation_scenario(scenario_type="vertical"):
    """
    Create animation for different scenarios

    scenario_type options:
    - "vertical": Intruder approaches vertically (y-direction)
    - "head_on": Head-on encounter
    - "crossing": Crossing paths
    """
    cfg = DAIDALUSConfig()
    det = ConflictDetection(cfg)
    viz = DAIDALUSVisualizer(cfg)

    if scenario_type == "vertical":
        # Vertical approach scenario - Aircraft swap positions
        own = AircraftState(
            x=0,      # North
            y=0,      # East - starts at 0
            z=1000,   # Altitude
            vx=0,     # No north movement
            vy=25,    # Moving east at 25 m/s (will reach y=3000 in 120s)
            vz=0      # Level flight
        )

        intr = AircraftState(
            x=0,      # Same north position
            y=3000,   # 3km to the east - starts at 3000
            z=1000,   # Same altitude
            vx=0,     # No north movement
            vy=-25,   # Moving west at 25 m/s (will reach y=0 in 120s)
            vz=0      # Level flight
        )

        # Set axes for vertical scenario with 500 unit increments
        viz.ax.set_xlim(-4000, 4000)  # East (y-axis)
        viz.ax.set_ylim(-2000, 2000)  # North (x-axis)
        x_ticks = np.arange(-4000, 4500, 500)
        y_ticks = np.arange(-2000, 2500, 500)
        viz.ax.set_xticks(x_ticks)
        viz.ax.set_yticks(y_ticks)

    elif scenario_type == "head_on":
        # Head-on scenario
        own = AircraftState(
            x=0, y=0, z=1000,
            vx=50, vy=0, vz=0
        )
        intr = AircraftState(
            x=6000, y=0, z=1000,
            vx=-45, vy=0, vz=0
        )

        # Set axes with 500 unit increments
        viz.ax.set_xlim(-2000, 2000)
        viz.ax.set_ylim(-2000, 8000)
        x_ticks = np.arange(-2000, 2500, 500)
        y_ticks = np.arange(-2000, 8500, 500)
        viz.ax.set_xticks(x_ticks)
        viz.ax.set_yticks(y_ticks)

    times = np.linspace(0, cfg.LOOKAHEAD_TIME, 300)
    ani = FuncAnimation(viz.fig, lambda tt: viz.update(tt, own, intr, det),
                        frames=times, blit=True, repeat=False, interval=50)
    return ani, viz


if __name__ == "__main__":
    # Create vertical approach scenario (intruder approaching from the side)
    print("Creating DAIDALUS visualization with conflict bands...")
    ani, viz = create_animation_scenario(scenario_type="vertical")

    # Save animation
    ani.save('daidalus_complete_animation.gif', writer='pillow', fps=20)
    print("Animation saved as 'daidalus_complete_animation.gif'")

    plt.show()
