"""
🛸 DRONE FLIGHT VISUALIZER

Matplotlib-based visualization for drone flights.
No C++ required - pure Python!
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from typing import List, Optional, Dict


def plot_trajectory_3d(trajectory: np.ndarray, 
                       title: str = "Drone Flight Path",
                       show_start_end: bool = True,
                       wind_vector: Optional[np.ndarray] = None):
    """
    Plot a 3D trajectory.
    
    Args:
        trajectory: Nx3 array of [x, y, z] positions
        title: Plot title
        show_start_end: Mark start/end points
        wind_vector: Optional wind direction to show
    """
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot trajectory
    ax.plot(trajectory[:, 0], trajectory[:, 1], trajectory[:, 2], 
            'b-', linewidth=2, label='Flight path')
    
    if show_start_end:
        # Start point (green)
        ax.scatter(*trajectory[0], color='green', s=100, marker='o', label='Start')
        # End point (red)
        ax.scatter(*trajectory[-1], color='red', s=100, marker='x', label='End')
    
    # Wind vector
    if wind_vector is not None and np.linalg.norm(wind_vector) > 0:
        center = trajectory.mean(axis=0)
        ax.quiver(center[0], center[1], center[2],
                  wind_vector[0], wind_vector[1], wind_vector[2],
                  color='orange', arrow_length_ratio=0.2, linewidth=2,
                  label=f'Wind ({np.linalg.norm(wind_vector):.1f} m/s)')
    
    # Ground plane
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    xx, yy = np.meshgrid(np.linspace(xlim[0], xlim[1], 10),
                         np.linspace(ylim[0], ylim[1], 10))
    ax.plot_surface(xx, yy, np.zeros_like(xx), alpha=0.2, color='green')
    
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Altitude (m)')
    ax.set_title(title)
    ax.legend()
    
    plt.tight_layout()
    return fig, ax


def plot_multi_trajectory(trajectories: Dict[str, np.ndarray],
                          colors: Optional[Dict[str, str]] = None,
                          title: str = "Multi-Drone Trajectories"):
    """
    Plot multiple trajectories (e.g., battle).
    
    Args:
        trajectories: Dict of name -> Nx3 trajectory arrays
        colors: Dict of name -> color
        title: Plot title
    """
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    
    default_colors = {'blue': 'blue', 'red': 'red', 'green': 'green', 'orange': 'orange'}
    colors = colors or default_colors
    
    for name, traj in trajectories.items():
        color = colors.get(name, 'gray')
        ax.plot(traj[:, 0], traj[:, 1], traj[:, 2], 
                color=color, linewidth=1.5, label=name)
        ax.scatter(*traj[-1], color=color, s=80, marker='x')
    
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Altitude (m)')
    ax.set_title(title)
    ax.legend()
    
    plt.tight_layout()
    return fig, ax


def plot_actions_over_time(actions: List[int], 
                           dt: float = 0.02,
                           title: str = "Action Distribution Over Time"):
    """
    Plot which actions were taken over time.
    """
    action_names = ['MOVE', 'COOPERATE', 'COMPETE', 'REST', 'REPRODUCE', 'ISOLATE']
    colors = ['#4CAF50', '#2196F3', '#f44336', '#9E9E9E', '#FF9800', '#9C27B0']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Timeline
    times = np.arange(len(actions)) * dt
    ax1.scatter(times, actions, c=[colors[a] for a in actions], s=10, alpha=0.7)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Action')
    ax1.set_yticks(range(6))
    ax1.set_yticklabels(action_names)
    ax1.set_title('Actions Over Time')
    ax1.grid(True, alpha=0.3)
    
    # Histogram
    counts = [actions.count(i) for i in range(6)]
    bars = ax2.bar(action_names, counts, color=colors)
    ax2.set_ylabel('Count')
    ax2.set_title('Action Distribution')
    
    # Add percentages
    total = len(actions)
    for bar, count in zip(bars, counts):
        pct = count / total * 100
        ax2.annotate(f'{pct:.1f}%', 
                     xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                     ha='center', va='bottom')
    
    plt.suptitle(title)
    plt.tight_layout()
    return fig


def plot_flight_stats(stats: Dict, title: str = "Flight Statistics"):
    """
    Create a dashboard of flight statistics.
    """
    fig = plt.figure(figsize=(14, 8))
    
    # Action pie chart
    ax1 = fig.add_subplot(2, 2, 1)
    actions = stats['actions_histogram']
    labels = list(actions.keys())
    sizes = list(actions.values())
    colors = ['#4CAF50', '#2196F3', '#f44336', '#9E9E9E', '#FF9800', '#9C27B0']
    ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Action Distribution')
    
    # Stats text
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.axis('off')
    stats_text = f"""
    FLIGHT STATISTICS
    ─────────────────
    Distance: {stats['distance_traveled']:.1f} m
    Battery: {stats['final_battery']*100:.0f}%
    Max Altitude: {stats['max_altitude']:.1f} m
    Min Altitude: {stats['min_altitude']:.1f} m
    Flight Time: {stats['flight_time']:.1f} s
    Crashed: {'YES ❌' if stats['crashed'] else 'NO ✅'}
    """
    ax2.text(0.1, 0.5, stats_text, fontsize=12, family='monospace',
             verticalalignment='center')
    
    plt.suptitle(title, fontsize=14)
    plt.tight_layout()
    return fig


class LivePlotter:
    """
    Real-time plotting during flight (updates as drone moves).
    """
    
    def __init__(self, arena_size: float = 20.0):
        plt.ion()  # Interactive mode
        self.fig = plt.figure(figsize=(10, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.arena_size = arena_size
        
        # Initialize empty trajectory
        self.trajectory = []
        self.line, = self.ax.plot([], [], [], 'b-', linewidth=2)
        self.point, = self.ax.plot([], [], [], 'ro', markersize=10)
        
        # Set axis limits
        self.ax.set_xlim(-arena_size/2, arena_size/2)
        self.ax.set_ylim(-arena_size/2, arena_size/2)
        self.ax.set_zlim(0, arena_size/2)
        
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Altitude (m)')
        self.ax.set_title('Live Drone Position')
        
        plt.show(block=False)
    
    def update(self, position: np.ndarray):
        """Update with new position."""
        self.trajectory.append(position.copy())
        
        if len(self.trajectory) > 1:
            traj = np.array(self.trajectory)
            self.line.set_data(traj[:, 0], traj[:, 1])
            self.line.set_3d_properties(traj[:, 2])
        
        self.point.set_data([position[0]], [position[1]])
        self.point.set_3d_properties([position[2]])
        
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def close(self):
        plt.ioff()
        plt.close(self.fig)


if __name__ == "__main__":
    # Demo with fake trajectory
    print("🛸 Drone Visualizer Demo")
    
    # Generate sample trajectory (helix)
    t = np.linspace(0, 4*np.pi, 200)
    trajectory = np.column_stack([
        5 * np.cos(t),
        5 * np.sin(t),
        t / (4*np.pi) * 10 + 2  # Rising helix
    ])
    
    # Add some noise to simulate real flight
    trajectory += np.random.randn(*trajectory.shape) * 0.2
    
    # Plot trajectory
    fig1, ax1 = plot_trajectory_3d(
        trajectory, 
        title="Sample Drone Helix Flight",
        wind_vector=np.array([3, 1, 0])
    )
    
    # Plot actions
    actions = [1, 1, 0, 0, 2, 2, 2, 1, 1, 3, 3, 5, 5, 1, 1, 1, 0, 4, 1, 1] * 10
    fig2 = plot_actions_over_time(actions, title="Sample Action Timeline")
    
    # Stats dashboard
    sample_stats = {
        'distance_traveled': 42.5,
        'final_battery': 0.72,
        'max_altitude': 12.1,
        'min_altitude': 2.0,
        'flight_time': 8.5,
        'crashed': False,
        'actions_histogram': {
            'MOVE': 20, 'COOPERATE': 100, 'COMPETE': 20,
            'REST': 20, 'REPRODUCE': 10, 'ISOLATE': 30
        }
    }
    fig3 = plot_flight_stats(sample_stats, "Sample Flight Dashboard")
    
    plt.show()
    print("✅ Visualization demo complete!")
