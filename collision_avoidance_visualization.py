"""
Aviation Collision Avoidance System Visualization
Shows ownship, intruder aircraft, SST/WCV circles, and dynamic conflict bands
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.patches import Circle, Wedge, FancyBboxPatch
import math


class CollisionAvoidanceVisualizer:
    """Visualizes aircraft collision avoidance with dynamic conflict bands"""

    def __init__(self):
        # Ownship position (at origin)
        self.ownship_pos = (0, 0)

        # SST and WCV radii (in meters)
        self.sst_radius = 2000  # Self-Separation Threshold (blue dotted)
        self.wcv_radius = 1000  # Well-clear violation volume (red)

        # Axis configuration
        self.axis_min = -2000
        self.axis_max = 6000
        self.axis_step = 500

        # Color scheme for conflict bands
        self.color_green = '#00ff00'  # Safe - far away
        self.color_amber = '#ffbf00'  # Caution - approaching SST
        self.color_red = '#ff0000'    # Danger - near WCV

    def calculate_conflict_band_color(self, distance):
        """
        Calculate conflict band color based on intruder distance
        - Green: distance > SST radius (far away)
        - Amber: WCV radius < distance <= SST radius (approaching)
        - Red: distance <= WCV radius (danger zone)
        """
        if distance > self.sst_radius:
            return self.color_green
        elif distance > self.wcv_radius:
            # Transition from green to amber to red as approaching
            ratio = (distance - self.wcv_radius) / (self.sst_radius - self.wcv_radius)
            if ratio > 0.5:
                return self.color_amber
            else:
                return self.color_red
        else:
            return self.color_red

    def draw_conflict_bands(self, ax, intruder_positions):
        """
        Draw conflict bands based on intruder positions
        Bands change color based on distance from ownship
        """
        # Define bearing sectors (360 degrees divided into 36 sectors of 10 degrees each)
        num_sectors = 36
        sector_angle = 360 / num_sectors

        for i in range(num_sectors):
            start_angle = i * sector_angle
            end_angle = (i + 1) * sector_angle

            # Check if any intruder is in this sector
            sector_color = self.color_green  # Default to green
            min_distance = float('inf')

            for intruder_pos in intruder_positions:
                # Calculate angle to intruder
                dx = intruder_pos[0] - self.ownship_pos[0]
                dy = intruder_pos[1] - self.ownship_pos[1]
                angle_to_intruder = math.degrees(math.atan2(dy, dx))
                if angle_to_intruder < 0:
                    angle_to_intruder += 360

                # Check if intruder is in this sector
                if start_angle <= angle_to_intruder < end_angle:
                    distance = math.sqrt(dx**2 + dy**2)
                    if distance < min_distance:
                        min_distance = distance
                        sector_color = self.calculate_conflict_band_color(distance)

            # Draw the sector as a wedge
            wedge = Wedge(
                self.ownship_pos,
                self.axis_max * 1.5,  # Extended radius
                start_angle,
                end_angle,
                facecolor=sector_color,
                alpha=0.3,
                edgecolor='none',
                zorder=1
            )
            ax.add_patch(wedge)

    def create_visualization(self, intruder_positions):
        """
        Create the complete collision avoidance visualization

        Args:
            intruder_positions: List of (x, y) tuples for intruder aircraft positions
        """
        # Create figure with extra space for legend
        fig, ax = plt.subplots(figsize=(14, 10))

        # Draw conflict bands first (background layer)
        self.draw_conflict_bands(ax, intruder_positions)

        # Draw SST circle (blue dotted) - Self-Separation Threshold
        sst_circle = Circle(
            self.ownship_pos,
            self.sst_radius,
            fill=False,
            edgecolor='blue',
            linestyle='--',
            linewidth=2,
            label='SST (Self-Separation Threshold)',
            zorder=3
        )
        ax.add_patch(sst_circle)

        # Draw WCV circle (red solid) - Well-clear violation volume
        wcv_circle = Circle(
            self.ownship_pos,
            self.wcv_radius,
            fill=False,
            edgecolor='red',
            linestyle='-',
            linewidth=2,
            label='WCV (Well-Clear Violation)',
            zorder=3
        )
        ax.add_patch(wcv_circle)

        # Draw ownship (triangle pointing up)
        ownship_size = 200
        ownship = ax.scatter(
            self.ownship_pos[0],
            self.ownship_pos[1],
            s=ownship_size,
            c='blue',
            marker='^',
            edgecolors='black',
            linewidths=2,
            label='Ownship',
            zorder=5
        )

        # Draw intruder aircraft
        for idx, intruder_pos in enumerate(intruder_positions):
            distance = math.sqrt(
                (intruder_pos[0] - self.ownship_pos[0])**2 +
                (intruder_pos[1] - self.ownship_pos[1])**2
            )

            # Color based on threat level
            if distance <= self.wcv_radius:
                color = 'red'
                marker = 'X'
            elif distance <= self.sst_radius:
                color = 'orange'
                marker = 's'
            else:
                color = 'green'
                marker = 'o'

            intruder = ax.scatter(
                intruder_pos[0],
                intruder_pos[1],
                s=150,
                c=color,
                marker=marker,
                edgecolors='black',
                linewidths=1.5,
                label=f'Intruder {idx+1}' if idx == 0 else '',
                zorder=4
            )

        # Configure axes
        ax.set_xlim(self.axis_min, self.axis_max)
        ax.set_ylim(self.axis_min, self.axis_max)

        # Set ticks at 500 unit intervals
        ticks = np.arange(self.axis_min, self.axis_max + self.axis_step, self.axis_step)
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)

        # Equal aspect ratio for equal dimensions
        ax.set_aspect('equal')

        # Labels
        ax.set_xlabel('X Position (meters)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Y Position (meters)', fontsize=12, fontweight='bold')
        ax.set_title('Aviation Collision Avoidance System - Conflict Band Visualization',
                     fontsize=14, fontweight='bold', pad=20)

        # Grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

        # Legend positioned outside the plot on the right
        legend_elements = [
            plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='blue',
                      markersize=10, label='Ownship', markeredgecolor='black', markeredgewidth=1.5),
            plt.Line2D([0], [0], color='blue', linestyle='--', linewidth=2,
                      label=f'SST - Self-Separation Threshold ({self.sst_radius}m)'),
            plt.Line2D([0], [0], color='red', linestyle='-', linewidth=2,
                      label=f'WCV - Well-Clear Violation ({self.wcv_radius}m)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green',
                      markersize=8, label='Intruder (Safe - Beyond SST)',
                      markeredgecolor='black', markeredgewidth=1),
            plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='orange',
                      markersize=8, label='Intruder (Caution - Within SST)',
                      markeredgecolor='black', markeredgewidth=1),
            plt.Line2D([0], [0], marker='X', color='w', markerfacecolor='red',
                      markersize=8, label='Intruder (Danger - Within WCV)',
                      markeredgecolor='black', markeredgewidth=1),
        ]

        # Add conflict band color explanations
        legend_elements.extend([
            patches.Patch(facecolor=self.color_green, alpha=0.3,
                         label='Conflict Band: GREEN (Safe)'),
            patches.Patch(facecolor=self.color_amber, alpha=0.3,
                         label='Conflict Band: AMBER (Approaching SST)'),
            patches.Patch(facecolor=self.color_red, alpha=0.3,
                         label='Conflict Band: RED (Near WCV)')
        ])

        ax.legend(
            handles=legend_elements,
            loc='center left',
            bbox_to_anchor=(1.02, 0.5),
            fontsize=10,
            framealpha=0.95,
            edgecolor='black',
            title='Legend',
            title_fontsize=12
        )

        # Add text annotations outside plot (bottom)
        fig.text(0.5, 0.02,
                'Conflict Band Behavior: Green (far) → Amber (approaching SST) → Red (near WCV)',
                ha='center', fontsize=11, style='italic',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        # Adjust layout to prevent legend cutoff
        plt.tight_layout(rect=[0, 0.03, 0.85, 0.97])

        return fig, ax


def main():
    """Main function to demonstrate the visualization"""

    # Create visualizer instance
    visualizer = CollisionAvoidanceVisualizer()

    # Example intruder positions at various distances
    # Format: (x, y) coordinates in meters
    intruder_positions = [
        (3500, 2000),   # Far away - should be green
        (1500, 1500),   # Approaching SST - should be amber
        (800, 300),     # Near WCV - should be red
        (-1800, 1200),  # Within SST - amber
        (2500, -1000),  # Outside SST - green
        (500, -700),    # Within WCV - red
    ]

    # Create visualization
    fig, ax = visualizer.create_visualization(intruder_positions)

    # Save the figure
    plt.savefig('collision_avoidance_plot.png', dpi=300, bbox_inches='tight')
    print("Visualization saved as 'collision_avoidance_plot.png'")

    # Display the plot
    plt.show()


if __name__ == "__main__":
    main()
