class Car:
    def __init__(self):
        self.name = "Porsche Taycan 4S"
        self.mass = 2215 #kg working weight
        self.power = 390 #kW
        self.torque = 640 #Nm
        self.frontalArea = 2.33
        self.dragCoefficient = 0.22
        self.rollResistance = 0.01
        self.batteryCapacity = 79200 #Wh gross capacity
        self.RegenEfficiency = 0.7

# https://www.car.info/sv-se/porsche/taycan/taycan-23793904/specs
# https://media.porsche.com/mediakit/taycan/en/porsche-taycan/die-aerodynamik
# https://www.diva-portal.org/smash/get/diva2:673348/fulltext01.pdf roll resistance