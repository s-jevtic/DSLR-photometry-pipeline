from enum import IntEnum

class ImageType(IntEnum):
    LIGHT = 0
    BIAS = 1
    DARK = 2
    FLAT = 3
	
class Color(IntEnum):
    RED = 0
    GREEN = 1
    BLUE = 2