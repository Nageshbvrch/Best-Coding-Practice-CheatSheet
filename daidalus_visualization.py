"""
DAIDALUS (Detect and Avoid Alerting Logic for Unmanned Systems)

Phase 1: Core math, detection, visualization (with altitude cues) + basic track conflict bands

UPDATED VERSION:
- Axes from -2000 to 6000 with 500 unit increments
- All legends and text outside plot
- Conflict bands based on DISTANCE from SST/WCV circles
- Green (far from SST) → Amber (approaching SST) → Red (near WCV)
"""

import numpy as np
import math
from dataclasses import dataclass
from typing import Tuple, List
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from matplotlib.animation import FuncAnimation
import IPython.display as ipydisplay

# Use system fallback fonts to avoid warnings for the ✈ symbol
matplotlib.rcParams["font.family"] = ["DejaVu Sans", "sans-serif"]

# ---------------------------
# Aircraft state
# ---------------------------
@dataclass
class AircraftState:
    # Position (m) in local N-E-U
    x: float  # North
    y: float  # East
    z: float  # Altitude (up)
    # Velocity (m/s)
    vx: float
    vy: float
    vz: float

    @property
    def ground_speed(self) -> float:
        return math.hypot(self.vx, self.vy)

    @property
    def track(self) -> float:
        # radians, clockwise from North (consistent with our N/E axes)
        eps = 1e-9
        return math.atan2(self.vy, self.vx + eps)

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
    DMOD = 4000.0    # ft - SST (Self-Separation Threshold)
    HMD  = 4000.0    # ft
    ZTHR = 450.0     # ft
    TAUMOD = 35.0    # s
    TCOA = 0.0       # s
    LOOKAHEAD_TIME = 180.0  # Increased for longer scenario

    # Band thresholds based on DISTANCE from circles
    # SST_RADIUS will be set after conversion from DMOD
    # WCV_RADIUS will be 0.7 * SST_RADIUS

    # Band sampling
    TRACK_STEP_DEG = 5  # coarse for speed; we can refine later
    BAND_INNER_M = 250  # visualization ring thickness
    BAND_OUTER_M = 450

    def __init__(self):
        ft2m = 0.3048
        self.DMOD *= ft2m
        self.HMD  *= ft2m
        self.ZTHR *= ft2m

        # Set thresholds for distance-based coloring
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
        tau  = GeometricUtils.modified_tau(s, v, self.cfg.DMOD)
        return (dcpa <= self.cfg.HMD) and (0 <= tau <= self.cfg.TAUMOD)

    def vertical_wcv(self, sz: float, vz: float) -> bool:
        if abs(sz) <= self.cfg.ZTHR:
            return True
        tcoa = GeometricUtils.time_to_coaltitude(sz, vz)
        return (0 <= tcoa <= self.cfg.TCOA)

    def well_clear_violation(self, own: AircraftState, intr: AircraftState) -> bool:
        s  = own.position_2d - intr.position_2d
        v  = own.velocity_2d - intr.velocity_2d
        sz = own.z - intr.z
        vz = own.vz - intr.vz
        return self.horizontal_wcv(s, v) and self.vertical_wcv(sz, vz)


# ---------------------------
# Conflict detection (interval)
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
        t_in  = (-sign * H - sz) / vz
        t_out = ( sign * self.cfg.ZTHR - sz) / vz
        if t_in > t_out:
            t_in, t_out = t_out, t_in
        if t1 < t_in or t_out < t0:
            return (-1.0, -1.0)
        return (max(t0, t_in), min(t1, t_out))

    def horizontal_entry_exit(self, s: np.ndarray, v: np.ndarray, span: float) -> Tuple[float, float]:
        # Already inside
        if np.linalg.norm(s) <= self.cfg.DMOD:
            tau = GeometricUtils.modified_tau(s, v, self.cfg.DMOD)
            t_out = min(span, tau) if tau > 0 else span
            return (0.0, t_out)

        sdotv = np.dot(s, v)
        v2 = np.dot(v, v)
        if (sdotv >= 0) or (v2 == 0):
            return (-1.0, -1.0)

        # Quadratic on ||s + t v||^2 = DMOD^2 with tau-modified boundary (as in spec)
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
        s  = own.position_2d - intr.position_2d
        v  = own.velocity_2d - intr.velocity_2d
        sz = own.z - intr.z
        vz = own.vz - intr.vz

        v_in, v_out = self.vertical_entry_exit(sz, vz, t0, t1)
        if v_in < 0 or v_out < 0 or v_in > v_out:
            return (t1, t0)  # empty

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
        self.fig = plt.figure(figsize=(16, 10))
        # Main plot takes up left 70% of figure
        self.ax = self.fig.add_axes([0.08, 0.15, 0.60, 0.75])
        self._setup_axes()

        # animated artists - using airplane symbols ✈
        self.own_marker = self.ax.text(0, 0, '✈', fontsize=24, ha='center', va='center',
                                       fontweight='bold', zorder=10)
        self.int_marker = self.ax.text(0, 0, '✈', fontsize=24, ha='center', va='center',
                                       fontweight='bold', zorder=10)
        self.own_label = self.ax.text(0, 0, '', fontsize=10,
                                      bbox=dict(boxstyle="round,pad=0.3", fc='white', alpha=0.8))
        self.int_label = self.ax.text(0, 0, '', fontsize=10,
                                      bbox=dict(boxstyle="round,pad=0.3", fc='white', alpha=0.8))

        # Well-clear circles (centered on ownship)
        # SST - Self-Separation Threshold (blue dotted)
        self.sst_circle = Circle((0, 0), self.cfg.SST_RADIUS, fill=False, ls='--',
                                lw=2, ec='tab:blue', alpha=0.7, label='SST')
        # WCV - Well-Clear Violation (red solid)
        self.wcv_circle = Circle((0, 0), self.cfg.WCV_RADIUS, fill=False,
                                lw=2, ec='tab:red', alpha=0.8, label='WCV')
        self.ax.add_patch(self.sst_circle)
        self.ax.add_patch(self.wcv_circle)

        # conflict bands container
        self.band_patches: List[Wedge] = []

        # status banner - positioned outside plot at top
        self.banner = self.fig.text(0.40, 0.94, '', ha='center', va='top',
                                   fontsize=11, fontweight='bold',
                                   bbox=dict(boxstyle="round,pad=0.5", fc='lightgreen', alpha=0.9))

        # Legend positioned outside plot area on the right side
        self._create_legend()

        # Additional text explanations below the plot
        self._create_text_annotations()

    def _setup_axes(self):
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel("East (m)", fontsize=12, fontweight='bold')
        self.ax.set_ylabel("North (m)", fontsize=12, fontweight='bold')
        self.ax.set_title("DAIDALUS Detection Logic — Distance-Based Conflict Bands",
                         fontsize=14, fontweight='bold')

        # Set axes from -2000 to 6000 with 500 unit increments
        self.ax.set_xlim(-2000, 6000)
        self.ax.set_ylim(-2000, 6000)
        ticks = np.arange(-2000, 6500, 500)
        self.ax.set_xticks(ticks)
        self.ax.set_yticks(ticks)

    def _create_legend(self):
        """Create comprehensive legend outside the plot area"""
        legend_x = 0.72
        legend_y = 0.85

        legend_text = (
            "LEGEND\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "OWNSHIP CIRCLES:\n"
            f"● SST (Blue Dotted): Self-Separation\n"
            f"   Threshold = {self.cfg.SST_RADIUS:.0f}m\n"
            f"   Safe separation distance\n\n"
            f"● WCV (Red Solid): Well-Clear\n"
            f"   Violation = {self.cfg.WCV_RADIUS:.0f}m\n"
            f"   Minimum safe distance\n\n"
            "CONFLICT BANDS:\n"
            "● GREEN: Safe\n"
            "   Intruder beyond SST\n\n"
            "● AMBER: Caution\n"
            "   Intruder approaching SST,\n"
            "   outside WCV\n\n"
            "● RED: Danger\n"
            "   Intruder near or within WCV\n\n"
            "AIRCRAFT SYMBOLS:\n"
            "● ✈ Airplane marker\n"
            "● ↑ Climbing (blue ✈)\n"
            "● ↓ Descending (orange ✈)\n"
            "● → Level flight (gray ✈)\n\n"
            f"Configuration:\n"
            f"DMOD: {self.cfg.DMOD:.0f}m\n"
            f"ZTHR: {self.cfg.ZTHR:.0f}m\n"
            f"TAUMOD: {self.cfg.TAUMOD:.0f}s\n"
            f"Lookahead: {self.cfg.LOOKAHEAD_TIME:.0f}s"
        )

        self.legend_text = self.fig.text(
            legend_x, legend_y, legend_text,
            va='top', ha='left', fontsize=9,
            bbox=dict(boxstyle="round,pad=0.8", fc='lightyellow',
                     ec='black', alpha=0.95),
            family='monospace'
        )

    def _create_text_annotations(self):
        """Create text annotations below the plot"""
        annotation_text = (
            "Conflict Band Behavior: As intruder approaches ownship, colors transition → "
            "GREEN (far from SST) → AMBER (approaching SST, outside WCV) → RED (near/within WCV)"
        )

        self.annotation = self.fig.text(
            0.40, 0.06, annotation_text,
            ha='center', va='center', fontsize=10, style='italic',
            bbox=dict(boxstyle="round,pad=0.5", fc='wheat', alpha=0.8),
            wrap=True
        )

    # --- utility: rotate a horizontal vector to a desired track (radians)
    @staticmethod
    def _rotate_to_track(speed: float, track_rad: float) -> np.ndarray:
        # track 0 rad = +North (x), +90° = +East (y)
        vx = speed * math.cos(track_rad)
        vy = speed * math.sin(track_rad)
        return np.array([vx, vy])

    # --- build conflict bands with DISTANCE-BASED color transitions
    def draw_track_bands(self, own: AircraftState, intr: AircraftState, detector: ConflictDetection):
        # clear existing wedges
        for p in self.band_patches:
            p.remove()
        self.band_patches.clear()

        center = (own.y, own.x)
        inner_r, outer_r = self.cfg.BAND_INNER_M, self.cfg.BAND_OUTER_M

        # Current distance from ownship to intruder - THIS IS THE KEY!
        current_distance = np.linalg.norm(own.position_2d - intr.position_2d)

        # Determine the threat level based on CURRENT distance
        # This ensures bands are green when intruder is far away
        if current_distance > self.cfg.SST_RADIUS:
            threat_level = "SAFE"  # Beyond SST - all green
        elif current_distance > self.cfg.WCV_RADIUS:
            threat_level = "CAUTION"  # Within SST but outside WCV - amber for conflicts
        else:
            threat_level = "DANGER"  # Within WCV - red for conflicts

        for deg in range(0, 360, self.cfg.TRACK_STEP_DEG):
            theta = math.radians(deg)
            # create a hypothetical ownship with same speed, new heading
            v2d = self._rotate_to_track(own.ground_speed, theta)
            hypo = AircraftState(own.x, own.y, own.z, v2d[0], v2d[1], own.vz)

            t_in, t_out = detector.detect_interval(hypo, intr, 0.0, self.cfg.LOOKAHEAD_TIME)

            # DISTANCE-BASED color classification
            # Key concept: Base color on CURRENT distance, not predicted closest approach
            if t_in <= t_out:  # Conflict exists in this direction
                # Color based on current distance threat level
                if threat_level == "SAFE":
                    # Intruder far away - even conflict directions stay green
                    color = '#90EE90'  # Light green
                    alpha = 0.5
                elif threat_level == "CAUTION":
                    # Intruder within SST - conflict directions are AMBER
                    color = '#FFB000'  # Amber
                    alpha = 0.6
                else:  # DANGER
                    # Intruder within WCV - conflict directions are RED
                    color = '#DC143C'  # Crimson red
                    alpha = 0.7
            else:
                # No conflict in this direction - always GREEN but shade varies
                if threat_level == "SAFE":
                    color = '#228B22'  # Forest green
                    alpha = 0.5
                elif threat_level == "CAUTION":
                    color = '#90EE90'  # Light green
                    alpha = 0.5
                else:  # DANGER
                    color = '#FFD700'  # Gold (non-conflict but still close)
                    alpha = 0.5

            # Draw wedge centered on ownship
            start = 90 - deg - self.cfg.TRACK_STEP_DEG/2
            end   = 90 - deg + self.cfg.TRACK_STEP_DEG/2
            w = Wedge(center, outer_r, start, end, width=outer_r-inner_r,
                     color=color, alpha=alpha, ec='white', linewidth=0.3)
            self.ax.add_patch(w)
            self.band_patches.append(w)

    # --- update frame
    def update(self, t: float, own0: AircraftState, intr0: AircraftState, detector: ConflictDetection):
        own = AircraftState(own0.x + own0.vx*t, own0.y + own0.vy*t, own0.z + own0.vz*t,
                            own0.vx, own0.vy, own0.vz)
        intr = AircraftState(intr0.x + intr0.vx*t, intr0.y + intr0.vy*t, intr0.z + intr0.vz*t,
                             intr0.vx, intr0.vy, intr0.vz)

        # Calculate current horizontal separation
        horiz_sep = np.linalg.norm(own.position_2d - intr.position_2d)
        vert_sep = abs(own.z - intr.z)

        # move well-clear circles to ownship
        self.sst_circle.center = (own.y, own.x)
        self.wcv_circle.center = (own.y, own.x)

        # markers - airplane symbols ✈ with altitude-based coloring
        own_style, own_glyph = self._alt_marker_style(own.vz)
        int_style, int_glyph = self._alt_marker_style(intr.vz)
        self.own_marker.set_position((own.y, own.x))
        self.int_marker.set_position((intr.y, intr.x))
        self.own_marker.set_color(own_style["color"])
        self.int_marker.set_color(int_style["color"])

        # labels with altitude and climb/descent glyph
        self.own_label.set_position((own.y + 200, own.x + 200))
        self.own_label.set_text(f"OWNSHIP{own_glyph}\nGS: {own.ground_speed:.1f} m/s\nAlt: {own.z:.0f} m")
        self.int_label.set_position((intr.y + 200, intr.x + 200))
        self.int_label.set_text(f"INTRUDER{int_glyph}\nGS: {intr.ground_speed:.1f} m/s\nAlt: {intr.z:.0f} m")

        # status banner with enhanced information - OUTSIDE PLOT at top
        t_in, t_out = detector.detect_interval(own, intr, 0.0, detector.cfg.LOOKAHEAD_TIME)

        # Determine severity based on DISTANCE
        if horiz_sep <= self.cfg.WCV_RADIUS:
            severity = "🔴 DANGER - WITHIN WCV"
            bg_color = '#FFB6C1'  # Light coral
        elif horiz_sep <= self.cfg.SST_RADIUS:
            severity = "🟡 CAUTION - WITHIN SST"
            bg_color = '#FFFFE0'  # Light yellow
        else:
            severity = "🟢 SAFE - BEYOND SST"
            bg_color = '#E0FFE0'  # Very light green

        if t_in <= t_out:
            self.banner.set_text(
                f"{severity}\n"
                f"Time to violation: {t_in:.1f}s | Duration: {t_out-t_in:.1f}s\n"
                f"Horiz. sep: {horiz_sep:.0f}m | Vert. sep: {vert_sep:.0f}m | Time: {t:.1f}s"
            )
        else:
            self.banner.set_text(
                f"✓ NO CONFLICT PREDICTED\n"
                f"Horiz. sep: {horiz_sep:.0f}m | Vert. sep: {vert_sep:.0f}m | Time: {t:.1f}s"
            )
        self.banner.set_bbox(dict(boxstyle="round,pad=0.5", fc=bg_color, alpha=0.9))

        # bands (recomputed each frame)
        self.draw_track_bands(own, intr, detector)

        # return animated artists
        return [self.own_marker, self.int_marker, self.own_label, self.int_label,
                self.sst_circle, self.wcv_circle, self.banner, *self.band_patches]

    # --- altitude-aware marker styling
    @staticmethod
    def _alt_marker_style(vz: float):
        if vz > 0.05:
            return dict(color='#4169E1'), " ↑"  # Royal blue
        if vz < -0.05:
            return dict(color='#FF8C00'), " ↓"  # Dark orange
        return dict(color='#696969'), " →"  # Dim gray


# ---------------------------
# Build animation - Aircraft start FAR APART
# ---------------------------
def create_animation_scenario():
    cfg = DAIDALUSConfig()
    det = ConflictDetection(cfg)
    viz = DAIDALUSVisualizer(cfg)

    # Aircraft start FAR APART (8km separation) and approach each other
    # Head-on collision course with altitude changes
    own = AircraftState(
        x=0,           # North position
        y=0,           # East position
        z=1000,        # 1000m altitude
        vx=50,         # Moving North at 50 m/s
        vy=0,          # No East velocity
        vz=1.0         # Climbing at 1 m/s
    )

    intr = AircraftState(
        x=8000,        # 8km North of ownship (FAR AWAY)
        y=0,           # Same East position (head-on)
        z=1200,        # 1200m altitude (200m above ownship)
        vx=-45,        # Moving South at 45 m/s (toward ownship)
        vy=0,          # No East velocity
        vz=-0.8        # Descending at 0.8 m/s (toward ownship altitude)
    )

    times = np.linspace(0, cfg.LOOKAHEAD_TIME, 300)
    ani = FuncAnimation(viz.fig, lambda tt: viz.update(tt, own, intr, det),
                        frames=times, blit=True, repeat=False, interval=50)
    return ani, viz


if __name__ == "__main__":
    ani, viz = create_animation_scenario()
    # For Jupyter notebooks:
    # ipydisplay.display(ipydisplay.HTML(ani.to_jshtml()))
    # For saving to file:
    ani.save('daidalus_animation.gif', writer='pillow', fps=20)
    print("Animation saved as 'daidalus_animation.gif'")
    plt.show()
    # plt.close(viz.fig)
