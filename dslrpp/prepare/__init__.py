from enum import Enum

class ImageType(Enum):
    LIGHT = 0
    BIAS = 1
    DARK = 2
    FLAT = 3
	
class Color(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2