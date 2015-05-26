#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import numpy
import errno

try:
    import xwiimote
except:
    print "Sorry, I can't seem to import xwiimote for some reason."
    print "Please check that it and it's python bindings are installed"
    sys.exit(1)
    
named_zero = { 'right_top': 0,
		'right_bottom': 0,
		'left_top': 0,
		'left_bottom': 0,
	      }

def stado_inicial(mdevice, p1):
    # display some information and open the iface
    try:
        #print("syspath:" + mdevice.get_syspath())
        #fd = mdevice.get_fd()
        #print("fd:", fd)
        #print("opened mask:", mdevice.opened())
        #mdevice.open(mdevice.available() | xwiimote.IFACE_WRITABLE)
        print("opened mask:", mdevice.opened())
        bateria = mdevice.get_battery()
        print("capacity:", bateria, "%")
        print("devtype:", mdevice.get_devtype())
        print("extension:", mdevice.get_extension())
    except SystemError as e:
        print("ooops", e)
        exit(1)
    
    #mdevice.set_mp_normalization(10, 20, 30, 40)
    #mdevice.set_mp_normalization(0, 0, 0, 0)
    #x, y, z, factor = mdevice.get_mp_normalization()
    #print("mp", x, y, z, factor)
    #calibrate(mdevice, p1)
    #mdevice.close(0)
    return bateria
  
def recalibrar(mdevice):
    mdevice.close(0)
    mdevice.open(mdevice.available() | xwiimote.IFACE_WRITABLE)
	
def sumarSensores( readings ):
    """
    Determine the weight of the user on the board in hundredths of a kilogram
    """
    weight = 0
    #weight = sum(calibrations.next())
    #print("Peso")
    #print(weight)
    for sensor in ('right_top', 'right_bottom', 'left_top', 'left_bottom'):
        reading = readings[sensor]
        weight += reading
    
    return weight

def calcweight( readings, calibrations ):
    """
    Determine the weight of the user on the board in hundredths of a kilogram
    """
    weight = 0
    #weight = sum(calibrations.next())
    #print("Peso")
    #print(weight)
    for sensor in ('right_top', 'right_bottom', 'left_top', 'left_bottom'):
        reading = readings[sensor]
        calibration = calibrations[sensor]
        weight += (reading - calibration)
    
    return weight
	
def gsc(readings, pos, named_calibration = named_zero):
    reading = readings[pos]
    calibration = named_calibration[pos]
    
    return reading - calibration
		

def dev_is_balanceboard(dev):
    time.sleep(2) # if we check the devtype to early it is reported as 'unknown' :(
    
    iface = xwiimote.iface(dev)
    return iface.get_devtype() == 'balanceboard'

def wait_for_balanceboard():
    print("Waiting for balanceboard to connect..")
    mon = xwiimote.monitor(True, False)
    dev = None

    while True:
	mon.get_fd(True) # blocks
	connected = mon.poll()
	
	if connected == None:
	    continue
	elif dev_is_balanceboard(connected):
	    print("Found balanceboard:", connected)
	    dev = connected
	    break
	else:
	    print("Found non-balanceboard device:", connected)
	    print("Waiting..")
    
    return dev
    
def leerSensores(mdevice, p1, numlecturas):

    calibration = []
    valormin = 15000
    valorMax = 0
    
    for i in xrange(4):
        calibration.append(0)
        
    leidos = numlecturas

    event = xwiimote.event()
    #for i in xrange(numlecturas):
    while leidos > 0:
        #print str(i)
        p1.poll() # blocks
        #event = xwiimote.event()
        try:
            mdevice.dispatch(event)
            
            if event.type == xwiimote.EVENT_KEY:
                code, state = event.get_key()
                print "Key:", code, ", State:", state
            elif event.type == xwiimote.EVENT_GONE:
                print "Gone"
            elif event.type == xwiimote.EVENT_WATCH:
                print "Watch"
            elif event.type == xwiimote.EVENT_CLASSIC_CONTROLLER_KEY:
                code, state = event.get_key()
                print "Classical controller key:", code, state
                tv_sec, tv_usec = event.get_time()
                print tv_sec, tv_usec
                event.set_key(xwiimote.KEY_HOME, 1)
                code, state = event.get_key()
                print "Classical controller key:", code, state
                event.set_time(0, 0)
                tv_sec, tv_usec = event.get_time()
                print tv_sec, tv_usec
            elif event.type == xwiimote.EVENT_CLASSIC_CONTROLLER_MOVE:
                x, y, z = event.get_abs(0)
                print "Classical controller move 1:", x, y
                event.set_abs(0, 1, 2, 3)
                x, y, z = event.get_abs(0)
                print "Classical controller move 1:", x, y
                x, y, z = event.get_abs(1)
                print "Classical controller move 2:", x, y
            elif event.type == xwiimote.EVENT_IR:
                for i in [0, 1, 2, 3]:
                    if event.ir_is_valid(i):
                        x, y, z = event.get_abs(i)
                        print "IR", i, x, y, z
    
            #else:
            #    if event.type != xwiimote.EVENT_ACCEL:
            #        print "type:", event.type
            else:
		leidos -= 1
		# Type 3
		# print "type:", event.type
                calibration[0] += event.get_abs(0)[0]
                calibration[3] += event.get_abs(1)[0]
                calibration[2] += event.get_abs(2)[0]
                calibration[1] += event.get_abs(3)[0]
                temporal = 0
                #calculamos el peso instantaneo para sacar el max/min
                for z in xrange(4):
                    temporal += event.get_abs(z)[0]
                if temporal > valorMax:
                    valorMax = temporal
                elif temporal < valormin:
                    valormin = temporal
                #event.set_abs(0, 0, 0, 0)
                #event.set_abs(1, 0, 0, 0)
                #event.set_abs(2, 0, 0, 0)
                #event.set_abs(3, 0, 0, 0)
                
        except IOError as e:
	    if e.errno != errno.EAGAIN:
		print "Bad"

    calibration[0] = calibration[0] / numlecturas
    calibration[3] = calibration[3] / numlecturas
    calibration[2] = calibration[2] / numlecturas
    calibration[1] = calibration[1] / numlecturas
    
    named_calibration = { 'right_top': calibration[0],
                        'right_bottom': calibration[3],
                        'left_top': calibration[2],
                        'left_bottom': calibration[1],
    }
    
    #print(calibration)
    #print(named_calibration)
    #print("Max " + str(valorMax) + " min " + str(valormin))
    #print("Dif " + str(valorMax - valormin))
    
    #print("terminada lectura")
    return named_calibration, valorMax, valormin
    
def calcularPeso(mdevice, p1, calibrations):
    
    calibration = []
    
    for i in xrange(4):
        calibration.append(0)
    
    p1.poll() # blocks
    
    event = xwiimote.event()
    mdevice.dispatch(event)
    calibration[0] = event.get_abs(0)[0]
    calibration[3] = event.get_abs(1)[0]
    calibration[2] = event.get_abs(2)[0]
    calibration[1] = event.get_abs(3)[0]

    for i in xrange(50):
        p1.poll() # blocks
        event = xwiimote.event()
        mdevice.dispatch(event)
        calibration[0] = (calibration[0] + event.get_abs(0)[0]) / 2
        calibration[3] = (calibration[3] + event.get_abs(1)[0]) / 2
        calibration[2] = (calibration[2] + event.get_abs(2)[0]) / 2
        calibration[1] = (calibration[1] + event.get_abs(3)[0]) / 2
    
    named_calibration = { 'right_top': calibration[0],
                        'right_bottom': calibration[1],
                        'left_top': calibration[2],
                        'left_bottom': calibration[3],
    }
    
    print(calibration)
    print(named_calibration)
    
    print("terminada calibracion")
    #p1.close()
    return named_calibration
  
def measurements(iface, p, calibration):
    while True:
        p.poll() # blocks

        event = xwiimote.event()
        iface.dispatch(event)

        tl = event.get_abs(2)[0] - calibration['left_top']
        tr = event.get_abs(0)[0] - calibration['right_top']
        br = event.get_abs(3)[0] - calibration['right_bottom']
        bl = event.get_abs(1)[0] - calibration['left_bottom']
        if tl < 0:
        	tl = 0
        if tr < 0:
        	tr = 0
        if bl < 0:
        	bl = 0
        if br < 0:
        	br = 0
        
	if (tl + tr + br + bl) > 500:
	 # tl = tr = br = bl = 0
	    #sleep(0.5)
	    yield (tl,tr,br,bl)
	    #yield sleep(2)
	    
def average_mesurements(ms, max_stddev=55):
    last_measurements = RingBuffer(800)

    while True:
        weight = sum(ms.next())

        last_measurements.append(weight)

        mean = numpy.mean(last_measurements.data)
        stddev = numpy.std(last_measurements.data)

        if stddev < max_stddev and last_measurements.filled:
            yield numpy.array((mean, stddev))
            
class RingBuffer():
    def __init__(self, length):
        self.length = length
        self.reset()
        self.filled = False

    def extend(self, x):
        x_index = (self.index + numpy.arange(x.size)) % self.data.size
        self.data[x_index] = x
        self.index = x_index[-1] + 1

        if self.filled == False and self.index == (self.length-1):
            self.filled = True

    def append(self, x):
        x_index = (self.index + 1) % self.data.size
        self.data[x_index] = x
        self.index = x_index

        if self.filled == False and self.index == (self.length-1):
            self.filled = True


    def get(self):
        idx = (self.index + numpy.arange(self.data.size)) %self.data.size
        return self.data[idx]

    def reset(self):
        self.data = numpy.zeros(self.length, dtype=numpy.int)
        self.index = 0