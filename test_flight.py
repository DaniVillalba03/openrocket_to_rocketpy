from rocketpy import Environment, SolidMotor, Rocket, Flight
import datetime

env = Environment(latitude=-25.33, longitude=-57.51, elevation=125.0)
ahora = datetime.datetime.now()
env.set_date((ahora.year, ahora.month, ahora.day, ahora.hour)) 
env.set_atmospheric_model(type='Forecast', file='GFS')

motor = SolidMotor(
    thrust_source="notebooks/simulacion_cohete.ipynb/thrust_source.csv",
    dry_mass=0,
    dry_inertia=(0.001, 0.001, 0.001),
    center_of_dry_mass_position=0,
    grains_center_of_mass_position=0,
    burn_time=1.0,
    grain_number=1,
    grain_separation=0,
    grain_density=823.3,
    grain_outer_radius=0.009,
    grain_initial_inner_radius=0.0045,
    grain_initial_height=0.07,
    nozzle_radius=0.00675,
    throat_radius=0.0045,
    interpolation_method="linear",
    coordinate_system_orientation="nozzle_to_combustion_chamber",
)

rocket = Rocket(
    radius=0.0125,
    mass=0.061,
    inertia=(0.001, 0.001, 0.001),
    power_off_drag="notebooks/simulacion_cohete.ipynb/drag_curve.csv",
    power_on_drag="notebooks/simulacion_cohete.ipynb/drag_curve.csv",
    center_of_mass_without_motor=0.24,
    coordinate_system_orientation="nose_to_tail",
)
rocket.add_motor(motor, position=0.382)

flight = Flight(
    rocket=rocket,
    environment=env,
    rail_length=1.0,
    inclination=90.0,
    heading=90.0,
    terminate_on_apogee=False,
    max_time=600,
)
print("Flight Z:", flight.apogee)
print("Flight Velocity:", flight.max_velocity)


