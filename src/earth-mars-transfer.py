# heliocentric.py

import spiceypy as spice
import fuji

spice.furnsh("../kernels/naif0012.tls")
spice.furnsh("../kernels/de442s.bsp")

utc = "2026-09-26 00:00:00"
et = spice.str2et(utc)

mars_state, _ = spice.spkezr(
    "MARS BARYCENTER",
    et,
    "J2000",
    "NONE",
    "SUN"
)
earth_state, _ = spice.spkezr(
    "EARTH BARYCENTER",
    et,
    "J2000",
    "NONE",
    "SUN"
)
spice.kclear()

mars_position_m = mars_state[:3] * 1000
mars_velocity_m_s = mars_state[3:] * 1000

earth_position_m = earth_state[:3] * 1000
earth_velocity_m_s = earth_state[3:] * 1000

sun = fuji.CelestialBody(
    name="Sun",
    color="#FDB813",
    mass=1.9885e30,
    radius=6.9634e8,
    position=[0.0, 0.0, 0.0],
    velocity=[0.0, 0.0, 0.0]
)
mars = fuji.CelestialBody(
    name="Mars",
    color="#D14A3A",
    mass=6.4171e23,
    radius=3.3895e6,
    position=mars_position_m,
    velocity=mars_velocity_m_s
)
earth = fuji.CelestialBody(
    name="Earth",
    color="#4A90E2",
    mass=5.9722e24,
    radius=6.371e6,
    position=earth_position_m,
    velocity=earth_velocity_m_s
)
sat1 = fuji.CelestialBody(
    name="Sat1",
    color="#FFFFFF",
    mass=1000.0,
    radius=10000.0,
    position=earth.position + [0.0, 6.371e6 + 1000e6, 0.0],
    velocity=earth.velocity + earth.circular_orbit_velocity(1000e6)
)

system = fuji.CelestialSystem([sun, earth, mars, sat1])

v1, v2 = system.lambert(
    departure_body="Sat1",
    arrival_body="Mars",
    central_body="Sun",
    dt=260,
    tof=270 * 24 * 3600
)
print(f"Departure velocity: {v1}")
print(f"Arrival velocity: {v2}")
system.add_impulse(
    body="Sat1",
    delta_v=v1 - sat1.velocity
)

system.launch_sim(
    duration=275 * 24 * 3600,
    animation_duration=20,
    dt=260,
    exaggeration_factor=10
)
