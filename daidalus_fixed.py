"""
DAIDALUS (Detect and Avoid Alerting Logic for Unmanned Systems)
Phase 1: Core math, detection, visualization (with altitude cues) + basic track conflict bands
FIXED VERSION: Aircraft start far apart, proper color transitions (green → amber → red)
"""

import numpy as np
import math
from dataclasses import dataclass
from typing import Tuple, List
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from matplotlib.animation import FuncAnimation
import IPython.display as ipydisplay

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
    DMOD = 4000.0    # ft
    HMD  = 4000.0    # ft
    ZTHR = 450.0     # ft
    TAUMOD = 35.0    # s
    TCOA = 0.0       # s
    LOOKAHEAD_TIME = 180.0  # Increased for longer scenario

    # Band thresholds for color transitions
    CORRECTIVE_THRESHOLD = 25.0  # s - time to red (danger)
    WARNING_THRESHOLD = 60.0     # s - time to amber (caution)

    # Band sampling
    TRACK_STEP_DEG = 5  # coarse for speed; we can refine later
    BAND_INNER_M = 250  # visualization ring thickness
    BAND_OUTER_M = 450

    def __init__(self):
        ft2m = 0.3048
        self.DMOD *= ft2m
        self.HMD  *= ft2m
        self.ZTHR *= ft2m


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
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self._setup_axes()

        # animated artists
        self.own_marker, = self.ax.plot([], [], 'o', ms=12)
        self.int_marker, = self.ax.plot([], [], 'o', ms=12)
        self.own_label = self.ax.text(0, 0, '', fontsize=10,
                                      bbox=dict(boxstyle="round,pad=0.3", fc='white', alpha=0.8))
        self.int_label = self.ax.text(0, 0, '', fontsize=10,
                                      bbox=dict(boxstyle="round,pad=0.3", fc='white', alpha=0.8))

        # Well-clear circles (centered on ownship)
        self.sst_circle = Circle((0, 0), self.cfg.DMOD, fill=False, ls='--', lw=2, ec='tab:blue', alpha=0.6)
        self.wcv_circle = Circle((0, 0), 0.7*self.cfg.DMOD, fill=False, lw=2, ec='tab:red', alpha=0.8)
        self.ax.add_patch(self.sst_circle)
        self.ax.add_patch(self.wcv_circle)

        # conflict bands container
        self.band_patches: List[Wedge] = []

        # status
        self.banner = self.ax.text(0.02, 0.98, '', transform=self.ax.transAxes,
                                   va='top', ha='left', fontsize=12, fontweight='bold',
                                   bbox=dict(boxstyle="round,pad=0.5", fc='lightgreen', alpha=0.9))

        # config textbox
        self.cfg_text = self.ax.text(0.98, 0.02,
            f"Configuration:\nDMOD: {self.cfg.DMOD:.0f}m\nZTHR: {self.cfg.ZTHR:.0f}m\n"
            f"TAUMOD: {self.cfg.TAUMOD:.0f}s\nLookahead: {self.cfg.LOOKAHEAD_TIME:.0f}s\n\n"
            f"Band Colors:\nGreen = Safe\nAmber = Caution\nRed = Danger",
            transform=self.ax.transAxes, va='bottom', ha='right', fontsize=9,
            bbox=dict(boxstyle="round,pad=0.4", fc='lightgray', alpha=0.8))

    def _setup_axes(self):
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel("East (m)", fontsize=11)
        self.ax.set_ylabel("North (m)", fontsize=11)
        self.ax.set_title("DAIDALUS Detection Logic — Head-On Approach with Color Transitions", fontsize=13, fontweight='bold')

    # --- utility: rotate a horizontal vector to a desired track (radians)
    @staticmethod
    def _rotate_to_track(speed: float, track_rad: float) -> np.ndarray:
        # track 0 rad = +North (x), +90° = +East (y)
        vx = speed * math.cos(track_rad)
        vy = speed * math.sin(track_rad)
        return np.array([vx, vy])

    # --- build conflict bands with proper color transitions
    def draw_track_bands(self, own: AircraftState, intr: AircraftState, detector: ConflictDetection):
        # clear existing wedges
        for p in self.band_patches:
            p.remove()
        self.band_patches.clear()

        center = (own.y, own.x)
        inner_r, outer_r = self.cfg.BAND_INNER_M, self.cfg.BAND_OUTER_M

        for deg in range(0, 360, self.cfg.TRACK_STEP_DEG):
            theta = math.radians(deg)
            # create a hypothetical ownship with same speed, new heading
            v2d = self._rotate_to_track(own.ground_speed, theta)
            hypo = AircraftState(own.x, own.y, own.z, v2d[0], v2d[1], own.vz)

            t_in, t_out = detector.detect_interval(hypo, intr, 0.0, self.cfg.LOOKAHEAD_TIME)

            # classify with proper thresholds: GREEN → AMBER → RED
            if t_in <= t_out:  # Conflict exists
                if t_in <= self.cfg.CORRECTIVE_THRESHOLD:
                    color = '#DC143C'  # Red - immediate danger
                    alpha = 0.7
                elif t_in <= self.cfg.WARNING_THRESHOLD:
                    color = '#FFB000'  # Amber - caution
                    alpha = 0.6
                else:
                    color = '#90EE90'  # Light green - future conflict
                    alpha = 0.5
            else:
                color = '#228B22'  # Forest green - safe
                alpha = 0.5

            # Draw wedge centered on ownship
            start = 90 - deg - self.cfg.TRACK_STEP_DEG/2
            end   = 90 - deg + self.cfg.TRACK_STEP_DEG/2
            w = Wedge(center, outer_r, start, end, width=outer_r-inner_r,
                     color=color, alpha=alpha, ec='white', linewidth=0.3)
            self.ax.add_patch(w)
            self.band_patches.append(w)

    # --- initialize limits around both trajectories
    def set_limits_for_pair(self, own: AircraftState, intr: AircraftState):
        T = self.cfg.LOOKAHEAD_TIME
        xs = [own.x, intr.x, own.x + own.vx*T, intr.x + intr.vx*T]
        ys = [own.y, intr.y, own.y + own.vy*T, intr.y + intr.vy*T]
        margin = max(self.cfg.DMOD*2, 2000)
        x_min, x_max = min(xs)-margin, max(xs)+margin
        y_min, y_max = min(ys)-margin, max(ys)+margin
        if x_max - x_min < 4000:
            c = 0.5*(x_min+x_max); x_min, x_max = c-2000, c+2000
        if y_max - y_min < 4000:
            c = 0.5*(y_min+y_max); y_min, y_max = c-2000, c+2000
        self.ax.set_xlim(y_min, y_max)  # East on x-axis
        self.ax.set_ylim(x_min, x_max)  # North on y-axis

    # --- altitude-aware marker styling
    @staticmethod
    def _alt_marker_style(vz: float):
        if vz > 0.05:
            return dict(color='#4169E1'), " ↑"  # Royal blue
        if vz < -0.05:
            return dict(color='#FF8C00'), " ↓"  # Dark orange
        return dict(color='#696969'), " →"  # Dim gray

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

        # markers (1-element sequences for Line2D)
        own_style, own_glyph = self._alt_marker_style(own.vz)
        int_style, int_glyph = self._alt_marker_style(intr.vz)
        self.own_marker.set_data([own.y], [own.x])
        self.int_marker.set_data([intr.y], [intr.x])
        self.own_marker.set_color(own_style["color"])
        self.int_marker.set_color(int_style["color"])

        # labels with altitude and climb/descent glyph
        self.own_label.set_position((own.y + 200, own.x + 200))
        self.own_label.set_text(f"OWNSHIP{own_glyph}\nGS: {own.ground_speed:.1f} m/s\nAlt: {own.z:.0f} m")
        self.int_label.set_position((intr.y + 200, intr.x + 200))
        self.int_label.set_text(f"INTRUDER{int_glyph}\nGS: {intr.ground_speed:.1f} m/s\nAlt: {intr.z:.0f} m")

        # status banner with enhanced information
        t_in, t_out = detector.detect_interval(own, intr, 0.0, detector.cfg.LOOKAHEAD_TIME)
        if t_in <= t_out:
            # Determine severity
            if t_in <= self.cfg.CORRECTIVE_THRESHOLD:
                severity = "🔴 DANGER"
                bg_color = '#FFB6C1'  # Light coral
            elif t_in <= self.cfg.WARNING_THRESHOLD:
                severity = "🟡 CAUTION"
                bg_color = '#FFFFE0'  # Light yellow
            else:
                severity = "🟢 ADVISORY"
                bg_color = '#E0FFE0'  # Very light green

            self.banner.set_text(
                f"{severity}\n"
                f"Time to violation: {t_in:.1f}s\n"
                f"Conflict duration: {t_out-t_in:.1f}s\n"
                f"Horiz. sep: {horiz_sep:.0f}m | Vert. sep: {vert_sep:.0f}m"
            )
            self.banner.set_bbox(dict(boxstyle="round,pad=0.5", fc=bg_color, alpha=0.9))
        else:
            self.banner.set_text(
                f"✓ NO CONFLICT\n"
                f"Horiz. sep: {horiz_sep:.0f}m | Vert. sep: {vert_sep:.0f}m"
            )
            self.banner.set_bbox(dict(boxstyle="round,pad=0.5", fc='lightgreen', alpha=0.9))

        # bands (recomputed each frame)
        self.draw_track_bands(own, intr, detector)

        # return animated artists
        return [self.own_marker, self.int_marker, self.own_label, self.int_label,
                self.sst_circle, self.wcv_circle, self.banner, *self.band_patches]


# ---------------------------
# Build animation - Aircraft start FAR APART
# ---------------------------
def create_animation_scenario2():
    cfg = DAIDALUSConfig()
    det = ConflictDetection(cfg)
    viz = DAIDALUSVisualizer(cfg)

    # FIXED: Aircraft start FAR APART (8km separation) and approach each other
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

    viz.set_limits_for_pair(own, intr)

    times = np.linspace(0, cfg.LOOKAHEAD_TIME, 300)
    ani = FuncAnimation(viz.fig, lambda tt: viz.update(tt, own, intr, det),
                        frames=times, blit=True, repeat=False, interval=50)
    return ani, viz


if __name__ == "__main__":
    ani, viz = create_animation_scenario2()
    ipydisplay.display(ipydisplay.HTML(ani.to_jshtml()))
    plt.close(viz.fig)
