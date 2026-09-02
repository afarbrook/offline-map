
import math
def world_to_latlon(x, y, z):
    px, py = x / 256, y / 256
    n = 2**z
    lon = (px/n) * 360 - 180
    lat = math.degrees( math.atan( math.sinh(math.pi-(py/n)*(2*math.pi)) ) )
    return lat, lon

def latlon_to_world(lat, lon, z):
    n = 2**z
    xtile = ((lon + 180) / 360) * n
    ytile = ( 1- ( math.log (math.tan(math.radians(lat)) + (1/math.cos(math.radians(lat))) ) )/math.pi) * (n/2)
    return xtile*256, ytile*256

