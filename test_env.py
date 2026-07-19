from rocketpy import Environment
import datetime
env = Environment(latitude=-25.33, longitude=-57.51, elevation=125.0)
ahora = datetime.datetime.now()
env.set_date((ahora.year, ahora.month, ahora.day, ahora.hour)) 
env.set_atmospheric_model(type='Forecast', file='GFS')
print("Atmospheric model elevation:", env.elevation)
print("Density at ground:", env.density(0))
print("Pressure at ground:", env.pressure(0))
print("Wind velocity at ground:", env.wind_velocity_x(0), env.wind_velocity_y(0))
