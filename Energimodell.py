import matplotlib.pyplot as plt
import numpy as np
import math
import time as t
import PySimpleGUI as sg
import random
from car import Car
from environment import Environement
from linkedQFile import LinkedQ
from PID import PIDController
from routing import Routing
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# TODO: inför predictive hastighethetssänkning för minskad hastighethetsbegränsning på kommande sträcka
# TODO: Energikravberäkning av en viss resa? Resulterar simuleringen i detta? Jämföra med någon tillgänglig energimängd och avgöra möjlighet?
# TODO: Optimering, maximera hastigheten med constraint att hålla effekten under en viss nivå och därmed totalenergiförbrukningen under en viss gräns?

car = Car()
envir = Environement()
q = LinkedQ()
r = Routing()
pid = PIDController()
pidBraking = PIDController()

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

def lateralAcc(v, radius):
    if radius != 0:
        a_lateral = v**2/radius
        return abs(a_lateral)
    return 0

def calculateMaxSpeed(v, s, section, q, type):
    v_lateral_forward_max = 0
    v_speedLim_max = 0
    v_lateral_max = 0
    if type == 2: range = 150
    else:
        if section.speedLimit < 70:
            range = 150
        elif section.speedLimit == 70:
            range = 150
        elif section.speedLimit > 70:
            range = 300

    if (s+range)>=section.distance: # om vi är i nästa delsträcka
        if q.peek() is not None: # en nästa delsträcka finns
            if lateralAcc(v,q.peek().radius) > 2: # om latacc är större än 0
                v_lateral_forward_max = math.sqrt(2*abs(q.peek().radius))
            if lateralAcc(v,section.radius) > 2: # om latacc är större än 0
                v_lateral_max = math.sqrt(2*abs(section.radius))
            if v*3.6 > q.peek().speedLimit:
                v_speedLim_max = q.peek().speedLimit/3.6

            if v_lateral_max == 0 and v_lateral_forward_max == 0 and v_speedLim_max != 0:
                return type, v_speedLim_max
            elif v_lateral_max == 0 and v_lateral_forward_max != 0 and v_speedLim_max == 0:
                return type, v_lateral_forward_max
            elif v_lateral_max != 0 and v_lateral_forward_max == 0 and v_speedLim_max == 0:
                return 2, v_lateral_max
            elif v_lateral_max != 0 and v_lateral_forward_max != 0 and v_speedLim_max == 0:
                if v_lateral_max<v_lateral_forward_max:
                    return 2, v_lateral_max
                else: 
                    return type, v_lateral_forward_max
            elif v_lateral_max != 0 and v_lateral_forward_max == 0 and v_speedLim_max != 0:
                if v_lateral_max<v_speedLim_max:
                    return 2, v_lateral_max
                else: 
                    return type, v_speedLim_max
            elif v_lateral_max == 0 and v_lateral_forward_max != 0 and v_speedLim_max != 0:
                return type, min(v_lateral_forward_max, v_speedLim_max)
            else:
                return 2, section.speedLimit/3.6
            
        else:
            if lateralAcc(v, section.radius) >= 2:
                v_lateral_max = math.sqrt(2*abs(section.radius))
            else:
                v_speedLim_max = section.speedLimit/3.6
            if v_lateral_max != 0:
                return 2, v_lateral_max
            else:
                return 2, v_speedLim_max
            
    else:
        if lateralAcc(v, section.radius) >= 2:
            v_lateral_max = math.sqrt(2*abs(section.radius))
        else:
            v_speedLim_max = section.speedLimit/3.6
        if v_lateral_max != 0:
            return 2, v_lateral_max
        else:
            return 2, v_speedLim_max

def previewNextSection(type, s, v, section, q):
    if type == 2: range = 150
    else:
        if section.speedLimit < 70:
            range = 150
        elif section.speedLimit == 70:
            range = 250
        elif section.speedLimit > 70:
            range = 500
    if (s+range)>=section.distance:
        if q.peek() is not None:
            if q.peek().radius != 0:
                return lateralAcc(v, q.peek().radius)
    return 0
            
def createGraphicInterphase(xs, ys):
    left_column = [
        [sg.Text('Current SOC (%): '), sg.Input(key='-SOC-',size=(6,1)),sg.Button('Submit',bind_return_key=True)],
        [sg.Button('Enginebraking',key='-FLASH-')],
        [sg.Text('Current speed (km/h): '), sg.Text('Speed', key='-SPEED-')],
        [sg.Text('Current power (W): '), sg.Text('power', key='-POWER-')],
        [sg.Text('Current total energy (Wh): '), sg.Text('energy', key='-ENERGY-')],
        [sg.Text('Total elapsed time (s): '), sg.Text('time', key='-TIME-')],
        [sg.Text('Current acceleration (m/s^2): '), sg.Text('acc', key='-ACC-')],
        [sg.Text('Current lateral acceleration (m/s^2): '), sg.Text('latacc', key='-LATACC-')],
        [sg.Text('Current predicted lateral acceleration (m/s^2): '), sg.Text('latacc', key='-LATACCPRED-')]
        ]
    leftmost_column = [
        [sg.Button('Braking',key='-FLASH2-')],
        [sg.Text('Available energy (Wh): '), sg.Text('energy', key='-AVAENE-')],
        [sg.Text('Regenerated energy (Wh): '), sg.Text('energy', key='-REGENE-')],
        [sg.Text('Speedlimit: '), sg.Text('Speedlim', key='-SPEEDLIM-')]
        ]
    layout = [
    [sg.Canvas(key='-CANVAS-'), sg.Column(left_column, element_justification='center'),sg.Column(leftmost_column, element_justification='center')]
    ]
    # Create the window
    window = sg.Window('Map GUI', layout, finalize=True,location=(0,0))

    # Add the pyplot figure to the GUI
    fig, ax = plt.subplots(figsize=(4,3))
    ax.plot(xs, ys)  # Preplot road
    dot, = ax.plot([], [], 'ro')  # Create a Line2D object for the moving dot
    fig_canvas_agg = FigureCanvasTkAgg(fig, window['-CANVAS-'].TKCanvas)
    fig_canvas_agg.draw()
    fig_canvas_agg.get_tk_widget().pack(side='top', expand=1)
    return fig_canvas_agg, window, dot

def flashButton(window, button_key):
    button = window[button_key]
    button.update(button_color=('white', 'red'))
    window.refresh()
    sg.time.sleep(0.05)  # Flash duration
    button.update(button_color=('white', 'gray'))
    window.refresh()

def currentPosition(dot, fig_canvas_agg, x, y):
    dot.set_data(x,y)
    fig_canvas_agg.draw()

def drawRoad(q, stepsize):
    x = 0
    y = 0
    currentHeading = 0
    xs = [x]
    ys = [y]
    for i in range(0, q.length()):
        section = q.dequeue()
        if section.radius == 0:  # straight road
            for j in range(int(section.distance / stepsize)):
                x += stepsize * np.cos(currentHeading)
                y += stepsize * np.sin(currentHeading)
                xs.append(x)
                ys.append(y)
        else:  # curved road
            angle= section.distance / section.radius
            cx = x - section.radius * np.sin(currentHeading)  # center of the circle
            cy = y + section.radius * np.cos(currentHeading)
            for j in range(int(section.distance / stepsize)):
                currentHeading += (angle / section.distance) * stepsize
                x = cx + section.radius * np.sin(currentHeading)
                y = cy - section.radius * np.cos(currentHeading)
                xs.append(x)
                ys.append(y)
        q.enqueue(section.distance, section.slope, section.radius, section.speedLimit)
    return xs, ys

def main():
    pid = PIDController()
    time = 0
    E = 0
    v = 0
    a = 0
    P_target = car.power*1000
    pid.PTerm = 100
    pid.ITerm = 10
    pid.DTerm = 1
    v_list = []
    p_list = []
    z = 0
    total_distance = 0
    stepsize = 1  # meter 
    regenedEnergy = 0
    totalRegenedSpeed = 0
    xs, ys = drawRoad(q, stepsize)
    fig_canvas_agg, window, dot = createGraphicInterphase(xs,ys)
    SOC = None
    while SOC == None:
        event, values = window.read()
        if event == 'Submit':
            SOC = int(values['-SOC-'])
    total_energy = car.batteryCapacity*(SOC/100)*3600 #J
    window['-AVAENE-'].update(value=total_energy/3600)
    window.refresh()
    while not q.is_empty():
        s = 0
        section =  q.dequeue()
        section_energy = 0
        regenedSpeed = 0
        regenedEnetemp = 0
        a_lateral_forward = 0
        while s < section.distance:
            if int(z) < len(xs):
                currentPosition(dot, fig_canvas_agg, xs[int(z)], ys[int(z)])
            else: break
            if v != 0:
                dt = stepsize/v
            else: dt = 1
            a_lateral_forward = previewNextSection(1, s, v, section, q)
            a_lateral = lateralAcc(v, section.radius)
            type, v_max = calculateMaxSpeed(v,s,section,q,1)
            if v_max != None:
                P_max = calculatePower(a, v_max, math.radians(math.atan(section.slope/100)))
            else: P_max = 0
            pid.SetPoint = min(P_target, P_max)
            P = calculatePower(a, v, math.radians(math.atan(section.slope/100)))
            pidFactor = pid.update(P)
            a = pidFactor/10
            if abs(v-v_max)<1/4:
                v += a*dt
            else:
                if type == 1 and pidFactor < 0: # Represents enginebraking
                    v -= 2/3.6 * dt
                    regenedSpeed = 2/3.6 * dt
                    if z%10 == 0:
                        flashButton(window, '-FLASH-')
                    P = 0

                elif type == 2 and pidFactor < 0: # Represents braking
                    
                    v -= 4/3.6 * dt
                    P = 0
                    if z%10 == 0:
                        flashButton(window, '-FLASH2-')

                else: # e.g. pidFactor > 0
                    v += a*dt
            window['-ACC-'].update(value=round(a,3))
            regenedEnetemp = (car.RegenEfficiency*car.mass*regenedSpeed**2)/2
            totalRegenedSpeed += regenedSpeed
            regenedEnergy += regenedEnetemp
            window['-REGENE-'].update(value=round(regenedEnergy/3600,3))
            if P < 0: P = 0
            v_list.append(v*3.6)
            p_list.append(P)
            time += dt
            E += P*dt
            E -= regenedEnetemp
            section_energy += P*dt
            if E>total_energy:
                print("Energy has run out")
                break
            s+=stepsize
            z+=1
            vs = round(v*3.6,0)
            Ps = round(P,0)
            window['-SPEEDLIM-'].update(value=section.speedLimit)
            window['-SPEED-'].update(value=vs)
            window['-POWER-'].update(value=Ps)
            window['-ENERGY-'].update(value=round(E/3600,3))
            window['-TIME-'].update(value=round(time,1))
            window['-LATACC-'].update(value=round(a_lateral,3))
            window['-LATACCPRED-'].update(value=round(a_lateral_forward,3))
            window.refresh()
            #t.sleep(0.05)
        total_distance += s
        if E>total_energy:
                break
    print("total motorbromsad hastighet: ",totalRegenedSpeed)
    plt.figure('Eco-Driving',figsize=(10,5))
    plt.subplot(1,2,1)
    plt.plot(v_list)
    plt.title("Hastighet mot sträcka")
    plt.ylabel("Hastighet (km/h)")
    plt.xlabel("Avstånd (m)")
    plt.subplot(1,2,2)
    plt.plot(p_list)
    plt.title("Effekt mot sträcka")
    plt.ylabel("Effekt (W)")
    plt.xlabel("Avstånd (m)")
    plt.tight_layout()
    #plt.show()
    print("Wh/km Eco: ", (E/3600)/(total_distance/1000))
    print(E/3600)
    print("Total återintjänad energi: ", regenedEnergy/3600)
    return E/3600


def main2():
    time = 0
    E = 0
    v = 0
    a = 0           # Hur ska a användas här? vi rör aldrig denna, utan förändrar bara hastigheten direkt...
    P_target = car.power*1000
    v_list = []
    p_list = []
    z = 0
    stepsize = 1  # meter 
    total_distance = 0
    xs, ys = drawRoad(q, stepsize)
    fig_canvas_agg, window, dot = createGraphicInterphase(xs,ys)

    SOC = None
    while SOC == None:
        event, values = window.read()
        if event == 'Submit':
            SOC = int(values['-SOC-'])
    total_energy = car.batteryCapacity*(SOC/100)*3600 #J
    window['-AVAENE-'].update(value=total_energy/3600)
    window.refresh()
    
    while not q.is_empty():
        s = 0
        section =  q.dequeue()
        section_energy = 0
        while s < section.distance:
            if int(z) < len(xs):
                currentPosition(dot, fig_canvas_agg, xs[int(z)], ys[int(z)])
            else: break
            a_lateral_forward = previewNextSection(1, s, v, section, q)
            a_lateral = lateralAcc(v, section.radius)
            type, v_max = calculateMaxSpeed(v,s,section,q,1)
            if v != 0:
                dt = stepsize/v
            else: dt = 1
            if v_max != None:
                P_max = calculatePower(a, v_max, math.radians(math.atan(section.slope/100)))
            else: P_max = 0
            pid.SetPoint = min(P_target, P_max)
            P = calculatePower(a, v, math.radians(math.atan(section.slope/100)))
            pidFactor = pid.update(P)
            a = pidFactor/10
            if abs(v-v_max)<1/4:
                v += a*dt
            else:
                if type == 2 and pidFactor < 0: # Represents braking
                    v -= 4/3.6 * dt
                    P = 0
                    if z%10 == 0:
                        flashButton(window, '-FLASH2-')
                else: # e.g. pidFactor > 0
                    v += a*dt
            window['-ACC-'].update(value=round(a,3))
            if P<0: P = 0
            v_list.append(v*3.6)
            p_list.append(P)
            time += dt
            E += P*dt
            section_energy += P*dt
            
            if E>total_energy:
                print("Energy has run out")
                break

            s+=stepsize
            z+=1
            vs = round(v*3.6,0)
            Ps = round(P,0)
            window['-SPEEDLIM-'].update(value=section.speedLimit)
            window['-SPEED-'].update(value=vs)
            window['-POWER-'].update(value=Ps)
            window['-ENERGY-'].update(value=round(E/3600,3))
            window['-TIME-'].update(value=round(time,1))
            window['-LATACC-'].update(value=round(a_lateral,3))
            window['-LATACCPRED-'].update(value=round(a_lateral_forward,3))
            window.refresh()
        total_distance += s
        if E>total_energy:
                break
    
    plt.figure('Normal driving',figsize=(10,5))
    plt.subplot(1,2,1)
    plt.plot(v_list)
    plt.title("Hastighet mot sträcka")
    plt.ylabel("Hastighet (km/h)")
    plt.xlabel("Avstånd (m)")
    plt.subplot(1,2,2)
    plt.plot(p_list)
    plt.title("Effekt mot sträcka")
    plt.ylabel("Effekt (W)")
    plt.xlabel("Avstånd (m)")
    plt.tight_layout()
    plt.show()
    print("Wh/km Normal: ", (E/3600)/(total_distance/1000))
    return E/3600


def createQueue():
    # q.enqueue(distance, % slope, radius(-höger, vänster), speedlimit)
    q.enqueue(50, 0, 0, 70)
    q.enqueue(200, 0, 200, 70)
    q.enqueue(500, 20, 0, 100)
    q.enqueue(150, 0, -60, 70)
    q.enqueue(500, 0, 0, 70)
    q.enqueue(300, 0, 0, 50)
    q.enqueue(200, 0, 100, 40)
    q.enqueue(200, 0, -100, 40)
    q.enqueue(500, -20, 0, 70)

createQueue()
E_eco = main()
createQueue()
E_normal = main2()
print("Eco: ", E_eco,"Normal: ", E_normal)

#address1 = "KTH Entré"
#address2 = "Stadshuset, Stockholm"
#r.route(address1, address2)
#time.sleep(100)