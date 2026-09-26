# fuji.py

import numpy as np
import pyvista as pv

G = 6.67430e-11


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


class CelestialSystem:
    def __init__(self, bodies):
        self.bodies = bodies

    def __repr__(self):
        return "\n".join([str(body.name) for body in self.bodies])

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

    def launch_sim(
        self,
        duration,
        dt,
        animation_duration=10.0,
        fps=60,
        trail_length=500
    ):
        # ---------------------------------------
        # Generate trajectories
        # ---------------------------------------

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

        print(f"Generated {steps} physics frames.")

        # ---------------------------------------
        # PyVista
        # ---------------------------------------

        plotter = pv.Plotter()
        plotter.set_background("black")

        actors = []
        trail_actors = []

        # ---------------------------------------
        # Create bodies
        # ---------------------------------------

        for i, body in enumerate(self.bodies):

            position = trajectories[i][0]

            # Visualization radius
            exaggeration_factor = 10

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

            # -----------------------------------
            # FULL ORBIT - DOTTED
            # -----------------------------------

            orbit_points = trajectories[i]

            # Take every Nth physics point
            dot_spacing = 50

            dotted_points = orbit_points[::dot_spacing]

            # Create PolyData containing only vertices
            orbit_dots = pv.PolyData(dotted_points)

            orbit_actor = plotter.add_mesh(
                orbit_dots,
                color=color,
                point_size=2,
                render_points_as_spheres=False,
                opacity=0.45
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