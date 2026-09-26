# main.py

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
moon_state, _ = spice.spkezr(
    "MOON",
    et,
    "J2000",
    "NONE",
    "EARTH"
)
spice.kclear()

mars_position_m = mars_state[:3] * 1000
mars_velocity_m_s = mars_state[3:] * 1000

earth_position_m = earth_state[:3] * 1000
earth_velocity_m_s = earth_state[3:] * 1000

moon_position_relative_m = moon_state[:3] * 1000
moon_velocity_relative_m_s = moon_state[3:] * 1000

# ---------------------------------------
# Moon -> Sun centered frame
# ---------------------------------------

moon_position_m = (
    earth_position_m +
    moon_position_relative_m
)
moon_velocity_m_s = (
    earth_velocity_m_s +
    moon_velocity_relative_m_s
)


mars = fuji.CelestialBody(
    name="Mars",
    color="red",
    mass=6.4171e23,
    radius=3.3895e6,
    position=mars_position_m,
    velocity=mars_velocity_m_s
)
earth = fuji.CelestialBody(
    name="Earth",
    color="blue",
    mass=5.9722e24,
    radius=6.371e6,
    position=earth_position_m,
    velocity=earth_velocity_m_s
)
sun = fuji.CelestialBody(
    name="Sun",
    color="yellow",
    mass=1.9885e30,
    radius=6.9634e8,
    position=[0.0, 0.0, 0.0],
    velocity=[0.0, 0.0, 0.0]
)

system = fuji.CelestialSystem([sun, earth, mars])

system.launch_sim(
    duration=1 * 365 * 24 * 3600,
    animation_duration=25,
    dt=3600
)
