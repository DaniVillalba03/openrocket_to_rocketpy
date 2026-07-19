from rocketpy import Environment
import datetime
env = Environment(latitude=-25.33, longitude=302.49, elevation=125.0)
ahora = datetime.datetime.utcnow() + datetime.timedelta(days=1)
env.set_date((ahora.year, ahora.month, ahora.day, 12)) 
env.set_atmospheric_model(type='Forecast', file='GFS')
print("Pressure:", env.pressure(0))
