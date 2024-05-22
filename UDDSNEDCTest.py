import numpy as np
from car import Car
from environment import Environement
from matplotlib import pyplot as plt
car = Car()
envir = Environement()

def airdrag(v, T):
    return 0.5 * car.dragCoefficient* car.frontalArea * envir.interpol(T) * v**3

def rollresistance(v,incline):
    return car.mass * 9.818 * car.rollResistance * np.cos(incline) * v

def climbing(v,incline):
    return car.mass * 9.818 * np.sin(incline) * v

def acceleration(a, v):
    return a * car.mass * v

def calculatePower(a, v, slope):
    P_air = airdrag(v,18)
    P_r = rollresistance(v, slope)
    P_c = climbing(v,slope) # zero if no incline/decline
    P_acc = acceleration(a,v) # zero if no change in velocity
    P_total = P_air + P_r + P_c + P_acc
    return P_total

def UDDS():
    print("--UDDS--")
    with open("uddscol.txt",'r') as f:
        next(f)
        next(f)
        lines = f.read().splitlines()

    sec = []    #s
    v = []      #m/s
    accel = [0]    #m/s^2
    E_total = 0     #Wh
    distance = 12.07        #km 
    Ps = []
    for a in lines:
        l = a.split("\t")
        sec.append(float(l[0]))  # Seconds
        v.append(float(l[1])*0.44704)    # m/s

    for i in range(1, len(sec)):
        accel.append((v[i]-v[i-1])/(sec[i]-sec[i-1])) #acceleration calc
        
    for i in range(0,len(sec)-1):
        P = calculatePower(accel[i],v[i], 0)
        if accel[i]<0: P=0
        Ps.append(P)
        E_total += P/3600
    plt.subplot(2,2,1)
    plt.plot(v)
    plt.title("EPA Urban Dynamometer Driving Schedule\n Längd 1369 sekunder    Sträcka = 12.07 km",loc='center')
    plt.ylabel("Hastighet (m/s)")
    plt.xlabel("Test Tid (s)")
    plt.subplot(2,2,3)
    plt.plot(Ps)
    plt.ylabel("Effekt (W)")
    plt.xlabel("Test Tid (s)")
    expectedRange = (car.batteryCapacity/E_total)*distance
    print("UDDS Expected range: ", expectedRange)
    print("Total energy expended: ",E_total)
    print("Consumption: ",E_total/distance)

def NEDC():
    print("--NEDC--")
    with open("NEDC.txt",'r') as f:
        next(f)
        lines = f.read().splitlines()
    sec = []    #s
    time = [i/4 for i in range(0, 1180*4)]
    v = 0
    vs = []      #m/s
    accel = []    #m/s^2
    accel2 = []
    E_total = 0     #Wh
    distance = 10932/1000        #km 
    Ps = []
    for a in lines:
        l = a.split("\t")
        accel.append(float(l[0]))  # m/s^2
        sec.append(float(l[1]))    # s

    for i in range(len(accel)):
        for j in range(0, int(sec[i])*4):
            accel2.append(accel[i])
            v += accel[i]*1/4
            vs.append(abs(round(v,0)))


    for j in range(0,len(vs)):
            P = calculatePower(accel2[j],vs[j], 0)
            if accel2[j]<0: P=0
            Ps.append(P)
            E_total += (P*0.25)/3600

    plt.subplot(2,2,2)
    plt.plot(time,vs)
    plt.title("New European Driving Cycle\n Längd 1180 sekunder    Sträcka = 10932 m",loc='center')
    plt.ylabel("Hastighet (m/s)")
    plt.xlabel("Test Tid (s)")
    plt.subplot(2,2,4)
    plt.plot(time,Ps)
    plt.ylabel("Effekt (W)")
    plt.xlabel("Test Tid (s)")
    expectedRange = (car.batteryCapacity/E_total)*distance
    print("NEDC Expected range: ", expectedRange)
    print("Total energy expended: ",E_total)
    print("Consumption: ",E_total/distance)

UDDS()
NEDC()
plt.show()