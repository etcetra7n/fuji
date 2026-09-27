# geocentric.py

import spiceypy as spice
import fuji

spice.furnsh("../kernels/naif0012.tls")
spice.furnsh("../kernels/de442s.bsp")

utc = "2026-09-26 00:00:00"
et = spice.str2et(utc)

moon_state, _ = spice.spkezr(
    "MOON",
    et,
    "J2000",
    "NONE",
    "EARTH"
)
spice.kclear()

moon_position_m = moon_state[:3] * 1000
moon_velocity_m_s = moon_state[3:] * 1000

earth = fuji.CelestialBody(
    name="Earth",
    color="#4A90E2",
    mass=5.9722e24,
    radius=6.371e6,
    position=[0.0, 0.0, 0.0],
    velocity=[0.0, 0.0, 0.0]
)
moon = fuji.CelestialBody(
    name="Moon",
    color="gray",
    mass=7.342e22,
    radius=1.7371e6,
    position=moon_position_m,
    velocity=moon_velocity_m_s
)
sat1 = fuji.CelestialBody(
    name="Sat1",
    color="red",
    mass=1000.0,
    radius=10000.0,
    position=[0.0, 6.371e6 + 10000e3, 0.0],
    velocity=[4935.0, 0.0, 0.0]
)

system = fuji.CelestialSystem([earth, sat1, moon])

v1, v2 = system.lambert(
    departure_body="Sat1",
    arrival_body="Moon",
    central_body="Earth",
    dt=4.0,
    tof=3 * 24 * 3600
)
print(f"Departure velocity: {v1}")
print(f"Arrival velocity: {v2}")
system.add_impulse(
    body="Sat1",
    delta_v=v1 - sat1.velocity
)

system.launch_sim(
    duration= 3.4 * 24 * 3600,
    animation_duration=10,
    dt=4.0,
    exaggeration_factor=1
)
