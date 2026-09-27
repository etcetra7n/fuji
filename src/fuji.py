# fuji.py

import numpy as np
import pyvista as pv
import copy

G = 6.67430e-11
DEFAULT_DT_MAX_STEP = 324000

class CelestialBody:
    def __init__(self, name, mass, position, velocity, radius=None, color=None):
        self.name = name
        self.color = color
        self.mass = mass
        self.radius = radius
        self.state = np.array([
            position[0], position[1], position[2],
            velocity[0], velocity[1], velocity[2]
        ], dtype=np.float64)

    @property
    def position(self):
        return self.state[:3]

    @property
    def velocity(self):
        return self.state[3:6]

    def __repr__(self):
        separator = "=" * 50
        underline = "-" * 50
        return (
            f"{separator}\n"
            f"{self.name}\n"
            f"{underline}\n"
            f"Color = {self.color}\n"
            f"Mass = {self.mass} kg\n"
            f"Radius = {self.radius} m\n"
            f"Position = {self.position}\n"
            f"Velocity = {self.velocity}\n"
            f"{separator}\n"
        )
    def circular_orbit_velocity(self, orbit_radius):
        if orbit_radius <= 0:
            raise ValueError("Orbit radius must be positive.")
        
        return np.sqrt(G * self.mass / orbit_radius)

class CelestialSystem:
    def __init__(self, bodies, T=0.0):
        self.bodies = bodies
        self.T = T

    def __repr__(self):
        return "\n".join([str(body.name) for body in self.bodies])
    
    def get_body(self, name):
        for body in self.bodies:
            if body.name == name:
                return body
        raise ValueError(f"Body '{name}' not found in the system")

    def propagate(self, dt):
        n = len(self.bodies)

        # Calculate accelerations at the current positions
        accelerations = [
            np.zeros(3, dtype=np.float64)
            for _ in range(n)
        ]

        for i in range(n):
            for j in range(i + 1, n):
                body_i = self.bodies[i]
                body_j = self.bodies[j]

                # Vector from i -> j
                r_vec = body_j.position - body_i.position
                distance = np.linalg.norm(r_vec)

                if distance == 0:
                    raise ValueError(
                        f"{body_i.name} and {body_j.name} "
                        "have the same position."
                    )

                # Gravitational acceleration
                direction = r_vec / distance

                acceleration_i = (
                    G * body_j.mass / distance**2
                ) * direction

                acceleration_j = (
                    G * body_i.mass / distance**2
                ) * -direction

                accelerations[i] += acceleration_i
                accelerations[j] += acceleration_j

        # Velocity Verlet: update positions
        for i, body in enumerate(self.bodies):
            body.position[:] += (
                body.velocity * dt
                + 0.5 * accelerations[i] * dt**2
            )

        # Calculate accelerations again at the new positions
        new_accelerations = [
            np.zeros(3, dtype=np.float64)
            for _ in range(n)
        ]

        for i in range(n):
            for j in range(i + 1, n):
                body_i = self.bodies[i]
                body_j = self.bodies[j]

                r_vec = body_j.position - body_i.position
                distance = np.linalg.norm(r_vec)

                if distance == 0:
                    raise ValueError(
                        f"{body_i.name} and {body_j.name} "
                        "have the same position."
                    )

                direction = r_vec / distance

                acceleration_i = (
                    G * body_j.mass / distance**2
                ) * direction

                acceleration_j = (
                    G * body_i.mass / distance**2
                ) * -direction

                new_accelerations[i] += acceleration_i
                new_accelerations[j] += acceleration_j

        # Velocity Verlet: update velocities
        for i, body in enumerate(self.bodies):
            body.velocity[:] += (
                0.5
                * (accelerations[i] + new_accelerations[i])
                * dt
            )
    def add_impulse(self, body, delta_v):
        body = self.get_body(body)
        body.velocity[:] += delta_v
    
    def get_system_at_time(self, T, dt=None):
        if dt is None:
            dt = (T - self.T) / DEFAULT_DT_MAX_STEP

        system = copy.deepcopy(self)
        duration = T - system.T

        if duration < 0:
            raise ValueError("Requested time is before the current system time.")

        while duration > dt:
            system.propagate(dt)
            system.T += dt
            duration -= dt

        if duration > 0:
            system.propagate(duration)
            system.T += duration

        return system

    def lambert(
        self,
        departure_body,
        arrival_body,
        central_body,
        tof,
        dt=None,
        prograde=True
    ):
        final_system = self.get_system_at_time(self.T + tof, dt)

        body1 = self.get_body(departure_body)
        body2 = final_system.get_body(arrival_body)
        center_body = self.get_body(central_body)

        r1 = body1.position - center_body.position
        r2 = body2.position - center_body.position

        mu = center_body.mass * G

        v1, v2 = lambert_universal(
            r1,
            r2,
            tof,
            mu,
            prograde=prograde
        )

        return v1, v2

    def launch_sim(
        self,
        duration,
        dt=None,
        animation_duration=10.0,
        fps=60,
        trail_length=500,
        exaggeration_factor = 300,
        dot_spacing = 200
    ):
        # ---------------------------------------
        # Generate trajectories
        # ---------------------------------------

        if dt is None:
            dt = duration / DEFAULT_DT_MAX_STEP
            print(f"Using dt = {dt:.3f}s")

        steps = int(duration / dt) + 1

        initial_states = [
            body.state.copy()
            for body in self.bodies
        ]

        trajectories = [
            np.empty((steps, 3), dtype=np.float64)
            for _ in self.bodies
        ]

        # ---------------------------------------
        # Physics simulation
        # ---------------------------------------

        for step in range(steps):

            for i, body in enumerate(self.bodies):
                trajectories[i][step] = body.position

            if step < steps - 1:
                self.propagate(dt)

        # Restore initial state
        for body, state in zip(self.bodies, initial_states):
            body.state[:] = state

        print(f"Computed {steps} physics frames")

        # ---------------------------------------
        # PyVista
        # ---------------------------------------

        plotter = pv.Plotter()
        plotter.set_background("black")

        marker = pv.create_axes_marker(
            x_color="red",
            y_color="green",
            z_color="blue"
        )
        text_property = marker.GetXAxisCaptionActor2D().GetCaptionTextProperty()
        text_property.SetColor(1, 1, 1)
        text_property = marker.GetYAxisCaptionActor2D().GetCaptionTextProperty()
        text_property.SetColor(1, 1, 1)
        text_property = marker.GetZAxisCaptionActor2D().GetCaptionTextProperty()
        text_property.SetColor(1, 1, 1)
        plotter.add_orientation_widget(
            marker,
            viewport=(0.0, 0.0, 0.2, 0.2),
            interactive=False
        )

        actors = []
        trail_actors = []

        # ---------------------------------------
        # Create bodies
        # ---------------------------------------

        for i, body in enumerate(self.bodies):

            position = trajectories[i][0]

            radius = (
                body.radius * exaggeration_factor
                if body.radius is not None
                else 1e9
            )

            color = (
                body.color
                if body.color is not None
                else "lightblue"
            )

            # -----------------------------------
            # Body
            # -----------------------------------

            sphere = pv.Sphere(
                radius=radius,
                center=(0, 0, 0)
            )

            actor = plotter.add_mesh(
                sphere,
                color=color,
                smooth_shading=True,
                name=body.name
            )
            actor.position = position
            actors.append(actor)

            # ----------------------------------- #
            # FULL ORBIT - DOTTED 
            # ----------------------------------- 
            orbit_points = trajectories[i]
            dotted_points = orbit_points[::dot_spacing]
            orbit_dots = pv.PolyData(dotted_points) 
            orbit_actor = plotter.add_mesh( 
                orbit_dots, 
                color=color, 
                point_size=1, 
                render_points_as_spheres=False, 
                opacity=0.9
            )

            # -----------------------------------
            # Dynamic trail
            # -----------------------------------

            trail_points = trajectories[i][0:1]
            trail_mesh = pv.PolyData(
                trail_points
            )
            trail_actor = plotter.add_mesh(
                trail_mesh,
                color=color,
                line_width=3
            )

            trail_actors.append(trail_actor)

        # ---------------------------------------
        # Camera
        # ---------------------------------------

        plotter.reset_camera()

        # ---------------------------------------
        # Animation
        # ---------------------------------------

        visual_frames = max(
            2,
            int(animation_duration * fps)
        )
        interval_ms = max(
            1,
            int(1000 / fps)
        )

        def update(step):
            fraction = (
                step / (visual_frames - 1)
            )
            physics_frame = int(
                fraction * (steps - 1)
            )
            for i in range(len(self.bodies)):
                position = trajectories[i][physics_frame]

                # Move body
                actors[i].position = position

                # -----------------------------------
                # Dynamic trail
                # -----------------------------------

                start = max(
                    0,
                    physics_frame - trail_length
                )

                points = trajectories[i][
                    start:physics_frame + 1
                ]

                if len(points) >= 2:

                    # Create connected line
                    lines = np.empty(
                        (len(points) - 1, 3),
                        dtype=np.int64
                    )

                    lines[:, 0] = 2
                    lines[:, 1] = np.arange(
                        len(points) - 1
                    )

                    lines[:, 2] = np.arange(
                        1,
                        len(points)
                    )

                    trail_mesh = pv.PolyData(
                        points,
                        lines=lines
                    )

                    trail_actors[i].mapper.SetInputData(
                        trail_mesh
                    )
            plotter.render()

        # ---------------------------------------
        # Timer
        # ---------------------------------------

        plotter.iren.initialize()
        plotter.add_timer_event(
            max_steps=visual_frames,
            duration=interval_ms,
            callback=update
        )
        plotter.show()


def stumpff_C(z):
    """Stumpff C(z)."""
    if z > 1e-8:
        s = np.sqrt(z)
        return (1.0 - np.cos(s)) / z
    elif z < -1e-8:
        s = np.sqrt(-z)
        return (np.cosh(s) - 1.0) / (-z)
    else:
        # Taylor expansion around z = 0
        return (
            1.0 / 2.0
            - z / 24.0
            + z**2 / 720.0
            - z**3 / 40320.0
        )


def stumpff_S(z):
    """Stumpff S(z)."""
    if z > 1e-8:
        s = np.sqrt(z)
        return (s - np.sin(s)) / (s**3)
    elif z < -1e-8:
        s = np.sqrt(-z)
        return (np.sinh(s) - s) / (s**3)
    else:
        # Taylor expansion around z = 0
        return (
            1.0 / 6.0
            - z / 120.0
            + z**2 / 5040.0
            - z**3 / 362880.0
        )


def lambert_universal(r1, r2, tof, mu, prograde=True):

    r1 = np.asarray(r1, dtype=float)
    r2 = np.asarray(r2, dtype=float)

    R1 = np.linalg.norm(r1)
    R2 = np.linalg.norm(r2)

    if R1 == 0 or R2 == 0:
        raise ValueError("Position vectors cannot be zero.")

    if tof <= 0:
        raise ValueError("Time of flight must be positive.")

    # ---------------------------------------------------------
    # Transfer angle
    # ---------------------------------------------------------

    cos_dtheta = np.dot(r1, r2) / (R1 * R2)
    cos_dtheta = np.clip(cos_dtheta, -1.0, 1.0)

    cross = np.cross(r1, r2)

    if prograde:
        if cross[2] >= 0:
            dtheta = np.arccos(cos_dtheta)
        else:
            dtheta = 2.0 * np.pi - np.arccos(cos_dtheta)
    else:
        if cross[2] < 0:
            dtheta = np.arccos(cos_dtheta)
        else:
            dtheta = 2.0 * np.pi - np.arccos(cos_dtheta)

    # ---------------------------------------------------------
    # A parameter
    # ---------------------------------------------------------

    sin_dtheta = np.sin(dtheta)

    A = (
        sin_dtheta
        * np.sqrt(R1 * R2 / (1.0 - cos_dtheta))
    )

    if abs(A) < 1e-12:
        raise ValueError(
            "Transfer angle is too close to 0 or 360 degrees."
        )

    # ---------------------------------------------------------
    # Solve for universal variable z
    # ---------------------------------------------------------

    def y(z):

        C = stumpff_C(z)
        S = stumpff_S(z)

        if C <= 0:
            return np.nan

        return (
            R1
            + R2
            + A * (z * S - 1.0) / np.sqrt(C)
        )

    def time_of_flight(z):

        C = stumpff_C(z)
        S = stumpff_S(z)

        Y = y(z)

        if Y < 0 or C <= 0:
            return np.nan

        X = np.sqrt(Y / C)

        return (
            (X**3 * S + A * np.sqrt(Y))
            / np.sqrt(mu)
        )

    def F(z):
        t = time_of_flight(z)

        if np.isnan(t):
            return np.nan

        return t - tof

    # ---------------------------------------------------------
    # Find a bracket for z
    # ---------------------------------------------------------

    z_min = -4.0 * np.pi**2
    z_max = 4.0 * np.pi**2

    z_values = np.linspace(z_min, z_max, 20000)

    previous_z = None
    previous_F = None

    bracket = None

    for z in z_values:

        f = F(z)

        if not np.isfinite(f):
            continue

        if previous_F is not None:

            if f * previous_F < 0:
                bracket = (previous_z, z)
                break

        previous_z = z
        previous_F = f

    if bracket is None:
        raise RuntimeError(
            "Could not find a Lambert solution for the supplied geometry."
        )

    # ---------------------------------------------------------
    # Bisection
    # ---------------------------------------------------------

    z_lo, z_hi = bracket

    for _ in range(200):

        z_mid = 0.5 * (z_lo + z_hi)

        f_mid = F(z_mid)

        if not np.isfinite(f_mid):
            z_lo = z_mid
            continue

        if abs(f_mid) < 1e-10:
            break

        f_lo = F(z_lo)

        if f_lo * f_mid <= 0:
            z_hi = z_mid
        else:
            z_lo = z_mid

    z = z_mid

    # ---------------------------------------------------------
    # Calculate f and g Lagrange coefficients
    # ---------------------------------------------------------

    Y = y(z)

    f = 1.0 - Y / R1
    g = A * np.sqrt(Y / mu)
    gdot = 1.0 - Y / R2

    # ---------------------------------------------------------
    # Velocities
    # ---------------------------------------------------------

    v1 = (r2 - f * r1) / g
    v2 = (gdot * r2 - r1) / g

    return v1, v2