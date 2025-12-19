"""
Live 3D Drone Visualization using VPython
Real-time feed of drone flight - rotatable, zoomable 3D view
"""

from vpython import canvas, box, sphere, cylinder, arrow, vector, color, rate, label, curve, mag
import numpy as np
from typing import Optional, List, Tuple
import time


class LiveDroneScene:
    """Real-time 3D drone visualization"""
    
    def __init__(self, title: str = "Drone Flight - Live Feed", 
                 ground_size: float = 100.0,
                 show_trail: bool = True):
        """
        Initialize live 3D scene
        
        Args:
            title: Window title
            ground_size: Size of ground plane
            show_trail: Whether to show flight path trail
        """
        # Create canvas (opens browser window)
        self.scene = canvas(
            title=f'<b>{title}</b>',
            width=1200,
            height=800,
            center=vector(0, 10, 0),
            background=color.cyan * 0.3  # Sky blue background
        )
        self.scene.camera.pos = vector(30, 20, 30)
        self.scene.camera.axis = vector(-30, -10, -30)
        
        self.ground_size = ground_size
        self.show_trail = show_trail
        self.drones = {}
        self.trails = {}
        self.labels = {}
        
        # Build the environment
        self._create_ground()
        self._create_sky_elements()
        
    def _create_ground(self):
        """Create ground plane with grid"""
        # Main ground
        self.ground = box(
            pos=vector(0, -0.5, 0),
            size=vector(self.ground_size, 1, self.ground_size),
            color=color.green * 0.6
        )
        
        # Grid lines
        grid_spacing = 10
        for i in range(-int(self.ground_size/2), int(self.ground_size/2) + 1, grid_spacing):
            # X lines
            curve(
                pos=[vector(i, 0.01, -self.ground_size/2), 
                     vector(i, 0.01, self.ground_size/2)],
                color=color.white * 0.3
            )
            # Z lines
            curve(
                pos=[vector(-self.ground_size/2, 0.01, i), 
                     vector(self.ground_size/2, 0.01, i)],
                color=color.white * 0.3
            )
            
        # Origin marker
        arrow(pos=vector(0, 0.1, 0), axis=vector(5, 0, 0), color=color.red, shaftwidth=0.2)
        arrow(pos=vector(0, 0.1, 0), axis=vector(0, 5, 0), color=color.green, shaftwidth=0.2)
        arrow(pos=vector(0, 0.1, 0), axis=vector(0, 0, 5), color=color.blue, shaftwidth=0.2)
        
    def _create_sky_elements(self):
        """Add some reference objects in the sky"""
        # Sun
        self.sun = sphere(
            pos=vector(50, 80, -50),
            radius=8,
            color=color.yellow,
            emissive=True
        )
        
        # Some clouds (white spheres)
        cloud_positions = [
            (20, 40, 30), (-30, 45, -20), (0, 50, -40), (40, 35, 0)
        ]
        for cx, cy, cz in cloud_positions:
            for _ in range(5):
                offset = np.random.randn(3) * 3
                sphere(
                    pos=vector(cx + offset[0], cy + abs(offset[1]), cz + offset[2]),
                    radius=2 + np.random.rand() * 2,
                    color=color.white,
                    opacity=0.7
                )
                
    def add_drone(self, drone_id: str, position: Tuple[float, float, float] = (0, 5, 0),
                  drone_color: Tuple[float, float, float] = (1, 0.5, 0)) -> None:
        """
        Add a drone to the scene
        
        Args:
            drone_id: Unique identifier
            position: Initial (x, y, z) position
            drone_color: RGB color tuple (0-1 range)
        """
        x, y, z = position
        col = vector(*drone_color)
        
        # Drone body (central sphere)
        body = sphere(
            pos=vector(x, y, z),
            radius=0.5,
            color=col
        )
        
        # Arms (4 cylinders)
        arm_length = 1.5
        arms = []
        rotors = []
        
        arm_directions = [
            vector(1, 0, 1).norm(),
            vector(1, 0, -1).norm(),
            vector(-1, 0, 1).norm(),
            vector(-1, 0, -1).norm()
        ]
        
        for direction in arm_directions:
            arm = cylinder(
                pos=vector(x, y, z),
                axis=direction * arm_length,
                radius=0.1,
                color=color.gray(0.3)
            )
            arms.append(arm)
            
            # Rotor at end of arm
            rotor_pos = vector(x, y, z) + direction * arm_length
            rotor = cylinder(
                pos=rotor_pos - vector(0, 0.05, 0),
                axis=vector(0, 0.1, 0),
                radius=0.6,
                color=color.gray(0.5),
                opacity=0.5
            )
            rotors.append(rotor)
            
        # Direction indicator (front arrow)
        front_arrow = arrow(
            pos=vector(x, y, z),
            axis=vector(2, 0, 0),
            color=color.red,
            shaftwidth=0.15
        )
        
        # Status label
        drone_label = label(
            pos=vector(x, y + 2, z),
            text=f'{drone_id}\nAlt: {y:.1f}m',
            height=12,
            color=color.white,
            background=color.black,
            opacity=0.5,
            box=False
        )
        
        # Flight trail
        if self.show_trail:
            trail = curve(color=col * 0.7, radius=0.05)
            trail.append(vector(x, y, z))
            self.trails[drone_id] = trail
            
        self.drones[drone_id] = {
            'body': body,
            'arms': arms,
            'rotors': rotors,
            'front': front_arrow,
            'label': drone_label,
            'color': col
        }
        self.labels[drone_id] = drone_label
        
    def update_drone(self, drone_id: str, 
                     position: Tuple[float, float, float],
                     velocity: Tuple[float, float, float] = (0, 0, 0),
                     orientation: Tuple[float, float, float] = (0, 0, 0),
                     throttle: float = 0.5,
                     status: str = "") -> None:
        """
        Update drone position and state
        
        Args:
            drone_id: Drone to update
            position: New (x, y, z)
            velocity: Current velocity for display
            orientation: Roll, pitch, yaw in radians
            throttle: Current throttle 0-1
            status: Status text to display
        """
        if drone_id not in self.drones:
            return
            
        drone = self.drones[drone_id]
        x, y, z = position
        vx, vy, vz = velocity
        roll, pitch, yaw = orientation
        
        pos = vector(x, y, z)
        
        # Update body
        drone['body'].pos = pos
        
        # Update arms and rotors
        arm_length = 1.5
        arm_directions = [
            vector(1, 0, 1).norm(),
            vector(1, 0, -1).norm(),
            vector(-1, 0, 1).norm(),
            vector(-1, 0, -1).norm()
        ]
        
        # Apply yaw rotation to arms
        cos_yaw = np.cos(yaw)
        sin_yaw = np.sin(yaw)
        
        for i, base_dir in enumerate(arm_directions):
            # Rotate direction by yaw
            rotated_dir = vector(
                base_dir.x * cos_yaw - base_dir.z * sin_yaw,
                base_dir.y,
                base_dir.x * sin_yaw + base_dir.z * cos_yaw
            )
            
            drone['arms'][i].pos = pos
            drone['arms'][i].axis = rotated_dir * arm_length
            
            rotor_pos = pos + rotated_dir * arm_length
            drone['rotors'][i].pos = rotor_pos - vector(0, 0.05, 0)
            
            # Rotor spin effect - opacity based on throttle
            drone['rotors'][i].opacity = 0.3 + throttle * 0.5
            
        # Update front arrow (heading)
        front_dir = vector(cos_yaw, 0, sin_yaw)
        drone['front'].pos = pos
        drone['front'].axis = front_dir * 2
        
        # Update label
        speed = np.sqrt(vx**2 + vy**2 + vz**2)
        label_text = f'{drone_id}\nAlt: {y:.1f}m\nSpd: {speed:.1f}m/s'
        if status:
            label_text += f'\n{status}'
        drone['label'].pos = pos + vector(0, 2.5, 0)
        drone['label'].text = label_text
        
        # Update trail
        if self.show_trail and drone_id in self.trails:
            self.trails[drone_id].append(pos)
            
    def add_target(self, position: Tuple[float, float, float], 
                   target_id: str = "target") -> None:
        """Add a target marker"""
        x, y, z = position
        
        # Target sphere
        target = sphere(
            pos=vector(x, y, z),
            radius=1,
            color=color.red,
            opacity=0.5
        )
        
        # Vertical line to ground
        curve(
            pos=[vector(x, 0, z), vector(x, y, z)],
            color=color.red * 0.5
        )
        
        # Target label
        label(
            pos=vector(x, y + 3, z),
            text=f'TARGET\n({x:.0f}, {y:.0f}, {z:.0f})',
            height=10,
            color=color.red,
            background=color.black,
            opacity=0.5
        )
        
    def add_obstacle(self, position: Tuple[float, float, float],
                     size: Tuple[float, float, float] = (5, 10, 5)) -> None:
        """Add an obstacle/building"""
        x, y, z = position
        sx, sy, sz = size
        
        box(
            pos=vector(x, sy/2, z),
            size=vector(sx, sy, sz),
            color=color.gray(0.4)
        )
        
    def add_wind_indicator(self, wind_speed: float, wind_direction: float) -> None:
        """Show wind direction and speed"""
        # Wind arrow at top corner
        wind_x = np.cos(wind_direction) * wind_speed
        wind_z = np.sin(wind_direction) * wind_speed
        
        arrow(
            pos=vector(-40, 30, -40),
            axis=vector(wind_x, 0, wind_z) * 0.5,
            color=color.cyan,
            shaftwidth=0.5
        )
        
        label(
            pos=vector(-40, 33, -40),
            text=f'Wind: {wind_speed:.1f} m/s',
            height=10,
            color=color.cyan,
            background=color.black,
            opacity=0.5
        )
        
    def set_camera_follow(self, drone_id: str, distance: float = 20) -> None:
        """Make camera follow a drone"""
        if drone_id in self.drones:
            drone_pos = self.drones[drone_id]['body'].pos
            self.scene.center = drone_pos
            
    def tick(self, fps: int = 60) -> None:
        """Call each frame to control update rate"""
        rate(fps)


class LiveCocoonFlight:
    """Run a cocoon-controlled drone with live visualization"""
    
    def __init__(self, cocoon_path: str):
        """
        Args:
            cocoon_path: Path to exported cocoon folder
        """
        self.cocoon_path = cocoon_path
        self.scene = None
        self.pilot = None
        
    def run(self, max_steps: int = 1000, 
            wind_speed: float = 5.0,
            wind_direction: float = 0.0,
            target_position: Tuple[float, float, float] = None) -> None:
        """
        Run live visualization of cocoon flying drone
        
        Args:
            max_steps: Maximum simulation steps
            wind_speed: Wind speed in m/s
            wind_direction: Wind direction in radians
            target_position: Optional target to display
        """
        # Import here to avoid circular imports - use relative imports
        from .cocoon_drone_bridge import CocoonDronePilot
        from .jsbsim_quadcopter import QuadcopterConfig
        
        # Create scene
        print("\n" + "="*60)
        print("LIVE DRONE FEED - VPython 3D Visualization")
        print("="*60)
        print("\nControls:")
        print("  - Right-click + drag: Rotate view")
        print("  - Scroll: Zoom in/out")
        print("  - Middle-click + drag: Pan")
        print("\nStarting simulation...")
        
        self.scene = LiveDroneScene(
            title=f"Cocoon Flight: {self.cocoon_path.split('/')[-1]}",
            show_trail=True
        )
        
        # Configure drone
        config = QuadcopterConfig()
        config.wind_speed = wind_speed
        config.wind_direction = wind_direction
        config.initial_altitude = 10.0
        
        # Create pilot
        self.pilot = CocoonDronePilot(
            cocoon_path=self.cocoon_path,
            drone_config=config
        )
        
        # Add drone to scene
        self.scene.add_drone(
            drone_id="cocoon_drone",
            position=(0, config.initial_altitude, 0),
            drone_color=(1.0, 0.5, 0.0)  # Orange
        )
        
        # Add wind indicator
        self.scene.add_wind_indicator(wind_speed, wind_direction)
        
        # Add target if specified
        if target_position:
            self.scene.add_target(target_position, "target")
            
        # Add some obstacles for reference
        self.scene.add_obstacle((20, 0, 20), (8, 15, 8))
        self.scene.add_obstacle((-15, 0, 25), (6, 20, 6))
        self.scene.add_obstacle((30, 0, -10), (10, 8, 10))
        
        # Get initial state
        state = self.pilot.get_state()
        
        print(f"\nDrone initialized at altitude {state.altitude:.1f}m")
        print(f"Wind: {wind_speed:.1f} m/s from {np.degrees(wind_direction):.0f}°")
        print("\nFlight starting...\n")
        
        step = 0
        flight_active = True
        
        try:
            while step < max_steps and flight_active:
                # Step the simulation
                obs, reward, done, truncated, info = self.pilot.step()
                state = self.pilot.get_state()
                
                # Update drone in scene
                status = f"Batt: {state.battery_percent:.0f}%"
                if state.crashed:
                    status = "CRASHED!"
                    flight_active = False
                    
                self.scene.update_drone(
                    drone_id="cocoon_drone",
                    position=state.position,
                    velocity=state.velocity,
                    orientation=(0, 0, state.heading),
                    throttle=0.5,  # Could extract from action
                    status=status
                )
                
                # Camera follow
                if step % 10 == 0:
                    self.scene.set_camera_follow("cocoon_drone")
                    
                # Print periodic updates
                if step % 100 == 0:
                    print(f"Step {step}: Alt={state.altitude:.1f}m, "
                          f"Pos=({state.position[0]:.1f}, {state.position[2]:.1f}), "
                          f"Batt={state.battery_percent:.0f}%")
                    
                # Control frame rate
                self.scene.tick(fps=60)
                step += 1
                
                if done:
                    flight_active = False
                    
        except KeyboardInterrupt:
            print("\n\nFlight interrupted by user")
            
        # Final report
        final_state = self.pilot.get_state()
        print("\n" + "="*60)
        print("FLIGHT COMPLETE")
        print("="*60)
        print(f"Steps: {step}")
        print(f"Final altitude: {final_state.altitude:.1f}m")
        print(f"Distance traveled: {final_state.distance_traveled:.1f}m")
        print(f"Battery remaining: {final_state.battery_percent:.0f}%")
        print(f"Crashed: {final_state.crashed}")
        print("\nClose the browser window to exit.")
        
        # Keep scene open
        while True:
            self.scene.tick(fps=30)


def demo_flight():
    """Demo with simulated drone (no cocoon needed)"""
    print("\n" + "="*60)
    print("LIVE DRONE DEMO - VPython 3D")
    print("="*60)
    print("\nOpening 3D view in browser...")
    print("\nControls:")
    print("  - Right-click + drag: Rotate view")
    print("  - Scroll: Zoom in/out")
    print("  - Middle-click + drag: Pan")
    
    scene = LiveDroneScene(title="Drone Demo Flight")
    
    # Add a drone
    scene.add_drone("demo_drone", position=(0, 10, 0), drone_color=(0.2, 0.6, 1.0))
    
    # Add target
    scene.add_target((30, 15, 30))
    
    # Add obstacles
    scene.add_obstacle((15, 0, 15), (5, 12, 5))
    scene.add_obstacle((-10, 0, 20), (8, 8, 8))
    
    # Add wind
    scene.add_wind_indicator(5.0, 0.785)  # 5 m/s from NE
    
    # Simulate flight path
    t = 0
    print("\nFlying demo pattern...")
    
    try:
        while True:
            # Simple circular flight pattern
            x = 20 * np.sin(t * 0.5)
            z = 20 * np.cos(t * 0.5)
            y = 10 + 5 * np.sin(t * 0.3)  # Altitude oscillation
            
            # Velocity
            vx = 10 * np.cos(t * 0.5)
            vz = -10 * np.sin(t * 0.5)
            vy = 1.5 * np.cos(t * 0.3)
            
            # Heading follows velocity
            yaw = np.arctan2(vz, vx)
            
            scene.update_drone(
                "demo_drone",
                position=(x, y, z),
                velocity=(vx, vy, vz),
                orientation=(0, 0, yaw),
                throttle=0.5 + 0.2 * np.sin(t),
                status=f"Demo t={t:.1f}s"
            )
            
            scene.tick(fps=60)
            t += 1/60
            
    except KeyboardInterrupt:
        print("\n\nDemo ended.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Run with cocoon
        cocoon_path = sys.argv[1]
        flight = LiveCocoonFlight(cocoon_path)
        flight.run(max_steps=2000, wind_speed=5.0)
    else:
        # Demo mode
        demo_flight()
