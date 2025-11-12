"""
DAIDALUS Integrated System: Temporal Conflict Analysis with Bimodal Wind Uncertainty
Combines core DAIDALUS logic with advanced probabilistic wind modeling and temporal analysis

Key Features:
1. Bimodal wind distribution for realistic atmospheric modeling
2. Temporal conflict bands showing risk evolution over time
3. Monte Carlo trajectory propagation with wind uncertainty
4. Probabilistic conflict bands with risk levels
5. Enhanced visualization with comprehensive dashboard
6. Scenario 2: Crossing paths with gusty bimodal wind conditions
"""

import numpy as np
import math
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as patches
import seaborn as sns

# ---------------------------
# Aircraft state
# ---------------------------
@dataclass
class AircraftState:
    """Aircraft state in local N-E-U coordinate system"""
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
        # radians, clockwise from North
        eps = 1e-9
        return math.atan2(self.vy, self.vx + eps)

    @property
    def position_2d(self) -> np.ndarray:
        return np.array([self.x, self.y])

    @property
    def velocity_2d(self) -> np.ndarray:
        return np.array([self.vx, self.vy])


# ---------------------------
# Wind State with Bimodal Distribution
# ---------------------------
@dataclass
class WindState:
    """Wind state with bimodal uncertainty parameters"""
    # Primary mode (dominant wind pattern)
    primary_speed: float      # m/s
    primary_direction: float  # radians
    primary_weight: float     # weight in bimodal distribution (0-1)

    # Secondary mode (secondary wind pattern)
    secondary_speed: float    # m/s
    secondary_direction: float # radians

    # Uncertainty parameters
    speed_uncertainty: float   # std dev in m/s
    direction_uncertainty: float # std dev in radians

    def sample_wind(self, n_samples: int = 1) -> np.ndarray:
        """
        Sample from bimodal wind distribution
        Returns: Array of (wind_x, wind_y) samples
        """
        samples = []

        for _ in range(n_samples):
            # Choose mode based on weights
            if np.random.random() < self.primary_weight:
                # Primary mode
                speed = np.random.normal(self.primary_speed, self.speed_uncertainty)
                direction = np.random.normal(self.primary_direction, self.direction_uncertainty)
            else:
                # Secondary mode
                speed = np.random.normal(self.secondary_speed, self.speed_uncertainty)
                direction = np.random.normal(self.secondary_direction, self.direction_uncertainty)

            # Convert to Cartesian
            wind_x = speed * np.cos(direction)
            wind_y = speed * np.sin(direction)
            samples.append([wind_x, wind_y])

        return np.array(samples)

    def get_mean_wind(self) -> np.ndarray:
        """Get weighted mean wind vector"""
        # Primary component
        primary_x = self.primary_speed * np.cos(self.primary_direction)
        primary_y = self.primary_speed * np.sin(self.primary_direction)

        # Secondary component
        secondary_x = self.secondary_speed * np.cos(self.secondary_direction)
        secondary_y = self.secondary_speed * np.sin(self.secondary_direction)

        # Weighted average
        mean_x = self.primary_weight * primary_x + (1 - self.primary_weight) * secondary_x
        mean_y = self.primary_weight * primary_y + (1 - self.primary_weight) * secondary_y

        return np.array([mean_x, mean_y])


# ---------------------------
# Bimodal Wind Field with Temporal Evolution
# ---------------------------
class BimodalWindField:
    """
    Enhanced bimodal wind model with temporal evolution
    Models realistic atmospheric conditions like fronts, thermals, gusts
    """

    def __init__(self, mode1_params, mode2_params, mix_weight=0.7):
        """
        mode1_params: (speed, direction, speed_std, dir_std)
        mode2_params: (speed, direction, speed_std, dir_std)
        mix_weight: probability of mode1 (0-1)
        """
        self.mode1 = mode1_params
        self.mode2 = mode2_params
        self.mix_weight = mix_weight

    def sample_wind_trajectory(self, n_samples, time_points):
        """
        Sample wind that can vary over time (e.g., frontal passage)
        Returns: Array of wind samples (n_samples x 2)
        """
        n_times = len(time_points)
        wind_samples = []

        for _ in range(n_samples):
            # Determine which mode for this sample
            use_mode1 = np.random.random() < self.mix_weight

            if use_mode1:
                base_speed = self.mode1[0]
                base_dir = self.mode1[1]
                speed_std = self.mode1[2]
                dir_std = self.mode1[3]
            else:
                base_speed = self.mode2[0]
                base_dir = self.mode2[1]
                speed_std = self.mode2[2]
                dir_std = self.mode2[3]

            # Add temporal variation (wind can change over time)
            speed = base_speed + np.random.normal(0, speed_std)
            direction = base_dir + np.random.normal(0, dir_std)

            # Add small temporal drift
            drift = 0.1 * np.sin(2 * np.pi * time_points[-1] / 120)
            speed += drift * base_speed

            wind_x = speed * np.cos(direction)
            wind_y = speed * np.sin(direction)
            wind_samples.append(np.array([wind_x, wind_y]))

        return np.array(wind_samples)

    def to_wind_state(self) -> WindState:
        """Convert to WindState for compatibility"""
        return WindState(
            primary_speed=self.mode1[0],
            primary_direction=self.mode1[1],
            primary_weight=self.mix_weight,
            secondary_speed=self.mode2[0],
            secondary_direction=self.mode2[1],
            speed_uncertainty=self.mode1[2],
            direction_uncertainty=self.mode1[3]
        )


# ---------------------------
# Config
# ---------------------------
class DAIDALUSConfig:
    """DAIDALUS configuration parameters"""
    DMOD = 4000.0    # ft - horizontal separation
    HMD  = 4000.0    # ft - horizontal miss distance
    ZTHR = 450.0     # ft - vertical threshold
    TAUMOD = 35.0    # s - modified tau threshold
    TCOA = 0.0       # s - time to co-altitude
    LOOKAHEAD_TIME = 120.0  # s - lookahead time

    # Band sampling
    TRACK_STEP_DEG = 5  # degrees for track band sampling
    BAND_INNER_M = 250  # visualization ring thickness (m)
    BAND_OUTER_M = 450  # visualization ring outer radius (m)

    def __init__(self):
        ft2m = 0.3048
        self.DMOD *= ft2m
        self.HMD  *= ft2m
        self.ZTHR *= ft2m


# ---------------------------
# Geometry helpers
# ---------------------------
class GeometricUtils:
    """Geometric utility functions for conflict detection"""

    @staticmethod
    def horizontal_range(s: np.ndarray, v: np.ndarray, t: float) -> float:
        """Compute horizontal range at time t"""
        return np.linalg.norm(s + t * v)

    @staticmethod
    def time_to_cpa(s: np.ndarray, v: np.ndarray) -> float:
        """Compute time to closest point of approach"""
        v2 = np.dot(v, v)
        if v2 == 0.0:
            return 0.0
        t = -np.dot(s, v) / v2
        return max(0.0, t)

    @staticmethod
    def dcpa(s: np.ndarray, v: np.ndarray) -> float:
        """Compute distance at closest point of approach"""
        t = GeometricUtils.time_to_cpa(s, v)
        return GeometricUtils.horizontal_range(s, v, t)

    @staticmethod
    def time_to_coaltitude(sz: float, vz: float) -> float:
        """Compute time to co-altitude"""
        if sz * vz < 0.0:
            return -sz / vz
        return -1.0

    @staticmethod
    def modified_tau(s: np.ndarray, v: np.ndarray, dmod: float) -> float:
        """Compute modified tau (time to horizontal separation threshold)"""
        s_dot_v = np.dot(s, v)
        if s_dot_v < 0.0:
            s2 = np.dot(s, s)
            return (dmod**2 - s2) / s_dot_v
        return -1.0


# ---------------------------
# WCV logic
# ---------------------------
class WellClearLogic:
    """Well-Clear Volume logic for determining violations"""

    def __init__(self, cfg: DAIDALUSConfig):
        self.cfg = cfg

    def horizontal_wcv(self, s: np.ndarray, v: np.ndarray) -> bool:
        """Check horizontal well-clear violation"""
        if np.linalg.norm(s) <= self.cfg.DMOD:
            return True
        dcpa = GeometricUtils.dcpa(s, v)
        tau  = GeometricUtils.modified_tau(s, v, self.cfg.DMOD)
        return (dcpa <= self.cfg.HMD) and (0 <= tau <= self.cfg.TAUMOD)

    def vertical_wcv(self, sz: float, vz: float) -> bool:
        """Check vertical well-clear violation"""
        if abs(sz) <= self.cfg.ZTHR:
            return True
        tcoa = GeometricUtils.time_to_coaltitude(sz, vz)
        return (0 <= tcoa <= self.cfg.TCOA)

    def well_clear_violation(self, own: AircraftState, intr: AircraftState) -> bool:
        """Check if well-clear is violated"""
        s  = own.position_2d - intr.position_2d
        v  = own.velocity_2d - intr.velocity_2d
        sz = own.z - intr.z
        vz = own.vz - intr.vz
        return self.horizontal_wcv(s, v) and self.vertical_wcv(sz, vz)


# ---------------------------
# Enhanced Conflict Detection with Wind Uncertainty
# ---------------------------
class ConflictDetection:
    """Enhanced conflict detection with wind uncertainty and probabilistic methods"""

    def __init__(self, cfg: DAIDALUSConfig):
        self.cfg = cfg
        self.wcv = WellClearLogic(cfg)

    def vertical_entry_exit(self, sz: float, vz: float, t0: float, t1: float) -> Tuple[float, float]:
        """Compute vertical conflict entry/exit times"""
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
        """Compute horizontal conflict entry/exit times"""
        # Already inside
        if np.linalg.norm(s) <= self.cfg.DMOD:
            tau = GeometricUtils.modified_tau(s, v, self.cfg.DMOD)
            t_out = min(span, tau) if tau > 0 else span
            return (0.0, t_out)

        sdotv = np.dot(s, v)
        v2 = np.dot(v, v)
        if (sdotv >= 0) or (v2 == 0):
            return (-1.0, -1.0)

        # Quadratic on ||s + t v||^2 = DMOD^2 with tau-modified boundary
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
        """Detect conflict interval [t_in, t_out]"""
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

    def detect_conflict_with_wind(self, own_pos, own_vel, int_pos, int_vel,
                                  wind_sample, altitude_diff):
        """
        Detect conflict for a specific wind realization
        Returns: (t_entry, t_exit)
        """
        # Apply wind to velocities
        own_vel_wind = own_vel + wind_sample
        int_vel_wind = int_vel + wind_sample

        # Relative state
        s = own_pos - int_pos
        v = own_vel_wind - int_vel_wind

        # Check vertical separation
        if abs(altitude_diff) > self.cfg.ZTHR:
            return -1.0, -1.0

        # Check horizontal conflict
        current_dist = np.linalg.norm(s)
        if current_dist <= self.cfg.DMOD:
            return 0.0, self.cfg.LOOKAHEAD_TIME

        # Check future conflict
        s_dot_v = np.dot(s, v)
        v_squared = np.dot(v, v)

        if s_dot_v >= 0 or v_squared == 0:
            return -1.0, -1.0

        # Solve quadratic for entry/exit times
        a = v_squared
        b = 2 * s_dot_v
        c = np.dot(s, s) - self.cfg.DMOD**2

        discriminant = b**2 - 4*a*c
        if discriminant < 0:
            return -1.0, -1.0

        sqrt_disc = np.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2*a)
        t2 = (-b + sqrt_disc) / (2*a)

        t_entry = max(0, min(t1, t2))
        t_exit = max(t1, t2)

        if t_entry > self.cfg.LOOKAHEAD_TIME:
            return -1.0, -1.0

        return t_entry, min(t_exit, self.cfg.LOOKAHEAD_TIME)

    def compute_probabilistic_conflict(self, own_pos, own_vel, int_pos, int_vel,
                                      wind_state: WindState, altitude_diff,
                                      n_samples: int = 100):
        """
        Compute conflict probability using Monte Carlo sampling
        Returns: (conflict_probability, mean_t_in, mean_t_out, confidence_bands)
        """
        wind_samples = wind_state.sample_wind(n_samples)

        conflicts = []
        t_ins = []
        t_outs = []

        for wind_sample in wind_samples:
            t_in, t_out = self.detect_conflict_with_wind(
                own_pos, own_vel, int_pos, int_vel, wind_sample, altitude_diff
            )

            if t_in >= 0 and t_in < t_out:
                conflicts.append(1)
                t_ins.append(t_in)
                t_outs.append(t_out)
            else:
                conflicts.append(0)

        conflict_probability = np.mean(conflicts)

        if len(t_ins) > 0:
            mean_t_in = np.mean(t_ins)
            mean_t_out = np.mean(t_outs)

            # Compute confidence bands (25th and 75th percentiles)
            confidence_bands = {
                't_in_lower': np.percentile(t_ins, 25),
                't_in_upper': np.percentile(t_ins, 75),
                't_out_lower': np.percentile(t_outs, 25),
                't_out_upper': np.percentile(t_outs, 75)
            }
        else:
            mean_t_in = -1
            mean_t_out = -1
            confidence_bands = None

        return conflict_probability, mean_t_in, mean_t_out, confidence_bands


# ---------------------------
# Temporal Conflict Bands
# ---------------------------
class TemporalConflictBands:
    """
    Compute conflict bands that evolve over time with bimodal wind uncertainty
    """

    def __init__(self, cfg: DAIDALUSConfig):
        self.cfg = cfg
        self.DMOD = cfg.DMOD
        self.ZTHR = cfg.ZTHR
        self.LOOKAHEAD = cfg.LOOKAHEAD_TIME

    def compute_temporal_conflict_probability(self,
                                             own_pos, own_vel,
                                             int_pos, int_vel,
                                             wind_samples,
                                             time_points):
        """
        Compute conflict probability at multiple time points
        Returns: (conflict_prob_over_time, lower_bound, upper_bound)
        """
        n_samples = len(wind_samples)
        n_times = len(time_points)
        conflict_matrix = np.zeros((n_samples, n_times))

        for i, wind in enumerate(wind_samples):
            own_vel_w = own_vel + wind
            int_vel_w = int_vel + wind

            for j, t in enumerate(time_points):
                # Positions at time t
                own_pos_t = own_pos + own_vel_w * t
                int_pos_t = int_pos + int_vel_w * t

                # Check if in conflict at time t
                distance = np.linalg.norm(own_pos_t - int_pos_t)
                conflict_matrix[i, j] = 1 if distance < self.DMOD else 0

        # Compute probability at each time
        conflict_prob_over_time = np.mean(conflict_matrix, axis=0)

        # Compute confidence intervals
        lower_bound = np.percentile(conflict_matrix, 25, axis=0)
        upper_bound = np.percentile(conflict_matrix, 75, axis=0)

        return conflict_prob_over_time, lower_bound, upper_bound

    def compute_heading_bands_temporal(self,
                                       own_pos, own_vel,
                                       int_pos, int_vel,
                                       wind_samples,
                                       time_points,
                                       n_headings=72):
        """
        Compute heading bands that evolve over time
        Returns: (headings, temporal_bands) where temporal_bands is (heading x time)
        """
        headings = np.linspace(0, 2*np.pi, n_headings)
        speed = np.linalg.norm(own_vel)

        # Initialize 2D array for results
        temporal_bands = np.zeros((n_headings, len(time_points)))

        for h_idx, heading in enumerate(headings):
            # New velocity for this heading
            new_vel = np.array([speed * np.cos(heading),
                               speed * np.sin(heading)])

            # Compute conflict probability over time for this heading
            prob_over_time, _, _ = self.compute_temporal_conflict_probability(
                own_pos, new_vel, int_pos, int_vel, wind_samples, time_points
            )

            temporal_bands[h_idx, :] = prob_over_time

        return headings, temporal_bands

    def compute_speed_bands_temporal(self,
                                    own_pos, own_vel,
                                    int_pos, int_vel,
                                    wind_samples,
                                    time_points,
                                    speed_range=(10, 100),
                                    n_speeds=30):
        """
        Compute speed bands that evolve over time
        Returns: (speeds, temporal_bands)
        """
        speeds = np.linspace(speed_range[0], speed_range[1], n_speeds)
        heading = np.arctan2(own_vel[1], own_vel[0])

        temporal_bands = np.zeros((n_speeds, len(time_points)))

        for s_idx, speed in enumerate(speeds):
            new_vel = np.array([speed * np.cos(heading),
                               speed * np.sin(heading)])

            prob_over_time, _, _ = self.compute_temporal_conflict_probability(
                own_pos, new_vel, int_pos, int_vel, wind_samples, time_points
            )

            temporal_bands[s_idx, :] = prob_over_time

        return speeds, temporal_bands

    def find_optimal_maneuver_sequence(self,
                                      own_pos, own_vel,
                                      int_pos, int_vel,
                                      wind_samples,
                                      time_points):
        """
        Find the optimal sequence of maneuvers over time
        Returns: (time_points, optimal_headings, min_risks)
        """
        # Compute heading bands over time
        headings, heading_bands = self.compute_heading_bands_temporal(
            own_pos, own_vel, int_pos, int_vel, wind_samples, time_points
        )

        # Find minimum risk heading at each time point
        optimal_headings = []
        min_risks = []

        for t_idx in range(len(time_points)):
            risks_at_t = heading_bands[:, t_idx]
            min_idx = np.argmin(risks_at_t)
            optimal_headings.append(headings[min_idx])
            min_risks.append(risks_at_t[min_idx])

        return time_points, optimal_headings, min_risks


# ---------------------------
# Enhanced Visualization with Temporal Dashboard
# ---------------------------
class EnhancedDAIDALUSVisualizer:
    """
    Enhanced visualization combining temporal analysis, wind uncertainty, and conflict bands
    """

    def __init__(self, cfg: DAIDALUSConfig):
        self.cfg = cfg
        self.conflict_computer = TemporalConflictBands(cfg)

    def create_comprehensive_dashboard(self, scenario_name, own: AircraftState,
                                      intr: AircraftState, wind_field: BimodalWindField):
        """
        Create comprehensive temporal analysis dashboard with all integrated features
        """
        # Time points for analysis
        time_points = np.linspace(0, self.cfg.LOOKAHEAD_TIME, 60)
        time_points_coarse = time_points[::4]  # Coarser for expensive computations

        # Sample wind field
        wind_samples = wind_field.sample_wind_trajectory(100, time_points)

        # Create figure with subplots
        fig = plt.figure(figsize=(22, 14))

        # === Subplot 1: Trajectory with uncertainty envelope ===
        ax1 = plt.subplot2grid((3, 4), (0, 0), colspan=2, rowspan=2)
        self.plot_trajectory_envelope(ax1, own, intr, wind_samples, time_points, scenario_name)

        # === Subplot 2: Temporal conflict probability ===
        ax2 = plt.subplot2grid((3, 4), (2, 0), colspan=2)
        conflict_prob, lower, upper = self.conflict_computer.compute_temporal_conflict_probability(
            own.position_2d, own.velocity_2d, intr.position_2d, intr.velocity_2d,
            wind_samples, time_points
        )
        self.plot_temporal_probability(ax2, time_points, conflict_prob, lower, upper)

        # === Subplot 3: Heading bands heatmap over time ===
        ax3 = plt.subplot2grid((3, 4), (0, 2), colspan=2)
        headings, heading_bands = self.conflict_computer.compute_heading_bands_temporal(
            own.position_2d, own.velocity_2d, intr.position_2d, intr.velocity_2d,
            wind_samples, time_points_coarse
        )
        self.plot_heading_temporal_heatmap(ax3, headings, time_points_coarse, heading_bands, own)

        # === Subplot 4: Speed bands heatmap over time ===
        ax4 = plt.subplot2grid((3, 4), (1, 2), colspan=2)
        speeds, speed_bands = self.conflict_computer.compute_speed_bands_temporal(
            own.position_2d, own.velocity_2d, intr.position_2d, intr.velocity_2d,
            wind_samples, time_points_coarse
        )
        self.plot_speed_temporal_heatmap(ax4, speeds, time_points_coarse, speed_bands, own)

        # === Subplot 5: Optimal maneuver sequence ===
        ax5 = plt.subplot2grid((3, 4), (2, 2), colspan=2)
        opt_times, opt_headings, opt_risks = self.conflict_computer.find_optimal_maneuver_sequence(
            own.position_2d, own.velocity_2d, intr.position_2d, intr.velocity_2d,
            wind_samples, time_points_coarse
        )
        self.plot_optimal_maneuver(ax5, opt_times, opt_headings, opt_risks)

        plt.suptitle(f'Enhanced DAIDALUS: {scenario_name}', fontsize=16, fontweight='bold')
        plt.tight_layout()

        return fig

    def plot_trajectory_envelope(self, ax, own: AircraftState, intr: AircraftState,
                                wind_samples, time_points, title):
        """Plot trajectories with uncertainty envelope"""
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('East Position (m)', fontsize=11)
        ax.set_ylabel('North Position (m)', fontsize=11)
        ax.set_title(f'{title} - Trajectory Uncertainty', fontsize=12, fontweight='bold')

        own_pos = own.position_2d
        own_vel = own.velocity_2d
        int_pos = intr.position_2d
        int_vel = intr.velocity_2d

        # Plot sample trajectories
        for i in range(min(20, len(wind_samples))):
            wind = wind_samples[i]
            own_vel_w = own_vel + wind
            int_vel_w = int_vel + wind

            own_traj = own_pos[:, np.newaxis] + own_vel_w[:, np.newaxis] * time_points
            int_traj = int_pos[:, np.newaxis] + int_vel_w[:, np.newaxis] * time_points

            ax.plot(own_traj[1], own_traj[0], 'b-', alpha=0.1, linewidth=0.5)
            ax.plot(int_traj[1], int_traj[0], 'r-', alpha=0.1, linewidth=0.5)

        # Plot mean trajectory
        mean_wind = np.mean(wind_samples, axis=0)
        own_vel_mean = own_vel + mean_wind
        int_vel_mean = int_vel + mean_wind

        own_traj_mean = own_pos[:, np.newaxis] + own_vel_mean[:, np.newaxis] * time_points
        int_traj_mean = int_pos[:, np.newaxis] + int_vel_mean[:, np.newaxis] * time_points

        ax.plot(own_traj_mean[1], own_traj_mean[0], 'b-', linewidth=3, label='Ownship (mean)')
        ax.plot(int_traj_mean[1], int_traj_mean[0], 'r-', linewidth=3, label='Intruder (mean)')

        # Aircraft positions with altitude indicators
        own_marker = '↑' if own.vz > 0.05 else '↓' if own.vz < -0.05 else '→'
        int_marker = '↑' if intr.vz > 0.05 else '↓' if intr.vz < -0.05 else '→'

        ax.plot(own_pos[1], own_pos[0], 'bo', markersize=12, markeredgecolor='black', markeredgewidth=2)
        ax.plot(int_pos[1], int_pos[0], 'ro', markersize=12, markeredgecolor='black', markeredgewidth=2)

        ax.text(own_pos[1]+100, own_pos[0]+100, f'Own {own_marker}\nAlt:{own.z:.0f}m', fontsize=9)
        ax.text(int_pos[1]+100, int_pos[0]+100, f'Int {int_marker}\nAlt:{intr.z:.0f}m', fontsize=9)

        # Well-clear volume
        circle = patches.Circle((own_pos[1], own_pos[0]), self.cfg.DMOD,
                               fill=False, color='orange', linestyle='--', linewidth=2, alpha=0.7)
        ax.add_patch(circle)

        ax.legend(loc='upper left')

    def plot_temporal_probability(self, ax, time_points, prob, lower, upper):
        """Plot conflict probability over time"""
        ax.fill_between(time_points, lower, upper, alpha=0.3, color='red', label='Uncertainty range')
        ax.plot(time_points, prob, 'r-', linewidth=2, label='Mean probability')

        # Risk level regions
        ax.axhspan(0, 0.1, alpha=0.2, color='green', label='Low risk')
        ax.axhspan(0.1, 0.5, alpha=0.2, color='yellow', label='Medium risk')
        ax.axhspan(0.5, 1.0, alpha=0.2, color='red', label='High risk')

        ax.set_xlabel('Time (seconds)', fontsize=11)
        ax.set_ylabel('Conflict Probability', fontsize=11)
        ax.set_title('Temporal Conflict Probability Evolution', fontsize=12, fontweight='bold')
        ax.set_xlim(0, self.cfg.LOOKAHEAD_TIME)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=8)

    def plot_heading_temporal_heatmap(self, ax, headings, time_points, bands, own: AircraftState):
        """Plot heading bands evolution as heatmap"""
        # Convert to degrees for display
        heading_degrees = np.degrees(headings)

        # Create custom colormap (green=safe, red=dangerous)
        colors = ['green', 'yellow', 'orange', 'red']
        n_bins = 100
        cmap = LinearSegmentedColormap.from_list('risk', colors, N=n_bins)

        im = ax.imshow(bands, aspect='auto', cmap=cmap, vmin=0, vmax=1,
                      extent=[time_points[0], time_points[-1],
                              heading_degrees[0], heading_degrees[-1]],
                      origin='lower')

        ax.set_xlabel('Time (seconds)', fontsize=11)
        ax.set_ylabel('Heading (degrees)', fontsize=11)
        ax.set_title('Heading Conflict Bands Over Time', fontsize=12, fontweight='bold')

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Conflict Probability', fontsize=10)

        # Mark current heading
        current_heading = np.degrees(own.track)
        ax.axhline(y=current_heading, color='white', linestyle='--', linewidth=2, label='Current')

        ax.set_ylim(0, 360)

    def plot_speed_temporal_heatmap(self, ax, speeds, time_points, bands, own: AircraftState):
        """Plot speed bands evolution as heatmap"""
        colors = ['green', 'yellow', 'orange', 'red']
        cmap = LinearSegmentedColormap.from_list('risk', colors, N=100)

        im = ax.imshow(bands, aspect='auto', cmap=cmap, vmin=0, vmax=1,
                      extent=[time_points[0], time_points[-1],
                              speeds[0], speeds[-1]],
                      origin='lower')

        ax.set_xlabel('Time (seconds)', fontsize=11)
        ax.set_ylabel('Speed (m/s)', fontsize=11)
        ax.set_title('Speed Conflict Bands Over Time', fontsize=12, fontweight='bold')

        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Conflict Probability', fontsize=10)

        # Mark current speed
        current_speed = own.ground_speed
        ax.axhline(y=current_speed, color='white', linestyle='--', linewidth=2, label='Current')

    def plot_optimal_maneuver(self, ax, time_points, opt_headings, risks):
        """Plot optimal maneuver sequence"""
        ax2 = ax.twinx()

        # Plot optimal heading over time
        ax.plot(time_points, np.degrees(opt_headings), 'b-', linewidth=2, label='Optimal heading')
        ax.fill_between(time_points, np.degrees(opt_headings) - 10,
                        np.degrees(opt_headings) + 10, alpha=0.3, color='blue')

        # Plot associated risk
        ax2.plot(time_points, risks, 'r--', linewidth=2, alpha=0.7, label='Risk level')
        ax2.fill_between(time_points, 0, risks, alpha=0.2, color='red')

        ax.set_xlabel('Time (seconds)', fontsize=11)
        ax.set_ylabel('Optimal Heading (degrees)', fontsize=11, color='blue')
        ax2.set_ylabel('Minimum Risk Level', fontsize=11, color='red')
        ax.set_title('Optimal Maneuver Sequence', fontsize=12, fontweight='bold')

        ax.tick_params(axis='y', labelcolor='blue')
        ax2.tick_params(axis='y', labelcolor='red')

        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, time_points[-1])


# ---------------------------
# Main Demonstration
# ---------------------------
def demonstrate_integrated_scenario2():
    """
    Demonstrate integrated DAIDALUS with Scenario 2: Crossing paths with gusty bimodal winds
    """
    print("=" * 80)
    print("Enhanced DAIDALUS: Temporal Conflict Analysis with Bimodal Wind Integration")
    print("=" * 80)
    print("\nScenario 2: Crossing Paths with Gusty Bimodal Wind Conditions")
    print("-" * 80)

    # Initialize components
    cfg = DAIDALUSConfig()
    detector = ConflictDetection(cfg)
    visualizer = EnhancedDAIDALUSVisualizer(cfg)

    # Scenario 2: Crossing paths with altitude changes and gusty winds
    own = AircraftState(
        x=0,      # North position (m)
        y=0,      # East position (m)
        z=1000,   # Altitude (m)
        vx=50,    # North velocity (m/s)
        vy=0,     # East velocity (m/s)
        vz=0.8    # Vertical velocity (m/s) - climbing
    )

    intr = AircraftState(
        x=1000,   # North position (m)
        y=-1000,  # East position (m)
        z=1200,   # Altitude (m)
        vx=0,     # North velocity (m/s)
        vy=50,    # East velocity (m/s)
        vz=-0.5   # Vertical velocity (m/s) - descending
    )

    # Bimodal wind: Gusty crosswind conditions
    # Mode 1: Strong gusts from the south (common)
    # Mode 2: Light winds from the north (occasional lulls)
    wind_field = BimodalWindField(
        mode1_params=(20, np.pi/2, 6, np.pi/8),    # 20 m/s from south, high variability
        mode2_params=(5, -np.pi/2, 2, np.pi/12),   # 5 m/s from north, low variability
        mix_weight=0.7  # 70% strong gusts, 30% light winds
    )

    print(f"\nAircraft Configuration:")
    print(f"  Ownship:  Pos=({own.x:.0f}, {own.y:.0f}, {own.z:.0f})m, "
          f"Vel=({own.vx:.1f}, {own.vy:.1f}, {own.vz:.1f})m/s")
    print(f"  Intruder: Pos=({intr.x:.0f}, {intr.y:.0f}, {intr.z:.0f})m, "
          f"Vel=({intr.vx:.1f}, {intr.vy:.1f}, {intr.vz:.1f})m/s")

    print(f"\nWind Configuration (Bimodal):")
    print(f"  Mode 1 (70%): {wind_field.mode1[0]:.1f} m/s @ {np.degrees(wind_field.mode1[1]):.0f}°")
    print(f"  Mode 2 (30%): {wind_field.mode2[0]:.1f} m/s @ {np.degrees(wind_field.mode2[1]):.0f}°")

    # Compute basic conflict detection
    print(f"\nConflict Detection (deterministic, no wind):")
    t_in, t_out = detector.detect_interval(own, intr, 0.0, cfg.LOOKAHEAD_TIME)
    if t_in <= t_out:
        print(f"  CONFLICT DETECTED: t_in={t_in:.1f}s, t_out={t_out:.1f}s, duration={t_out-t_in:.1f}s")
    else:
        print(f"  No conflict detected")

    # Compute probabilistic conflict with wind
    print(f"\nProbabilistic Conflict Detection (with bimodal wind, n=200 samples):")
    wind_state = wind_field.to_wind_state()
    altitude_diff = own.z - intr.z
    prob, mean_t_in, mean_t_out, conf_bands = detector.compute_probabilistic_conflict(
        own.position_2d, own.velocity_2d, intr.position_2d, intr.velocity_2d,
        wind_state, altitude_diff, n_samples=200
    )

    print(f"  Conflict Probability: {prob:.1%}")
    if mean_t_in > 0:
        print(f"  Mean time to conflict: {mean_t_in:.1f}s")
        if conf_bands:
            print(f"  95% CI: [{conf_bands['t_in_lower']:.1f}s, {conf_bands['t_in_upper']:.1f}s]")
    else:
        print(f"  No conflicts detected in Monte Carlo simulation")

    # Create comprehensive visualization
    print(f"\nGenerating comprehensive temporal analysis dashboard...")
    fig = visualizer.create_comprehensive_dashboard(
        "Scenario 2: Crossing with Gusty Winds",
        own, intr, wind_field
    )

    output_file = 'daidalus_integrated_scenario2.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"  Dashboard saved as: {output_file}")

    plt.show()
    plt.close()

    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    # Set random seed for reproducibility
    np.random.seed(42)

    # Run integrated demonstration
    demonstrate_integrated_scenario2()
