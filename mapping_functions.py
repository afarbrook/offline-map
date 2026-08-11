
import numpy as np

def world_to_latlon(x, y, z):
    px, py = int(x / 256), int(y / 256)
    n = 2**z
    lon = (px/n) * 360 - 180
    lat = np.degrees( np.arctan( np.sinh(np.pi-(py/n)*(2*np.pi)) ) )
    return lat, lon

def latlon_to_world(lat, lon, z):
    n = 2**z
    xtile = ((lon + 180) / 360) * n
    ytile = ( 1- ( np.log (np.tan(np.radians(lat)) + (1/np.cos(np.radians(lat))) ) )/np.pi) * (n/2)
    return xtile*256, ytile*256

