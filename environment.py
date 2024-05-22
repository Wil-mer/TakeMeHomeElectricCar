import numpy as np
class Environement:
    def __init__(self):
        self.airDensitity = [1.3943, 1.3673, 1.3413, 1.3163, 1.2922, 1.2690, 1.2466, 1.2250, 1.2041] #-20 -15 -10 ... *C
        self.temperature = [-20, -15, -10, -5, 0, 5, 10, 15, 20]
        self.airPressure = []

    def interpol(self, T):
        return np.interp(T, self.temperature, self.airDensitity)
        # suboptimal, linear interpolation
        # polyfit() exists
        

# Source: Applied Thermodynamics: Collection of Formulas - Hans Havtun