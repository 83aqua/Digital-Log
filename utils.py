
from math import cos,sin,pi,exp
import serial
import pynmea2
from pynmea2.stream import NMEAStreamReader
from pynmea2.nmea import NMEASentence
from time import *

def test(canvas):
    xCentre,yCentre =250,250
    #
#     xPoint,yPoint =112,250
#     drawLine(canvas,xCentre,yCentre,xPoint,yPoint)
#     print("speed to theta"+str(speedToTheta(1)))
    speed=14
    theta=speedToTheta(speed)
#     i=15
#     theta=i*pi/12
    xPoint,yPoint=thetaToEndPt(theta)
    drawLine(canvas, xCentre, yCentre, xPoint,yPoint)
    
def drawLine(canvas,pointer,xCentre,yCentre,xPoint,yPoint):
    if (pointer!=None):
        canvas.delete(pointer)
    lineId=canvas.create_line(xCentre,yCentre,xPoint,yPoint,width=10,fill='white',arrow='last',arrowshape=(8,10,3))
    return lineId
    
def speedToTheta(speed):
    return (7.5-speed/2)*3.1416/6
def thetaToEndPt(theta):
    return (250.0+120.0*cos(theta),250.0-120.0*sin(theta))

def ReadValFromDataFile(lineNo):
    file1=open("Test Data.txt")
    ProcValue=file1.readlines()
    return ProcValue[lineNo]

def ReadValueToProcValue(ReadValue):
    #print "\nReadValue",ReadValue 
    return ((int(ReadValue) / 65535.0) * 20)

def CurrentToPsi(ProcVal):
    return (ProcVal) / 2.0
    #return (ProcVal - 4.0) / 1.6
    
    
def PrToSpeed(DeltaP):
    a = -1.40475726474414E-03
    b = -2.56522894530918E-05
    c = 7.2133893593594

    result = ((a + (b * exp(DeltaP))) + (c * (DeltaP**.5)))
    return result

def WriteToSerialNmea(speed):
    #GPVTG.Format("%s\r\n","$VWVHW, , ,231.8,M,5.0,N,8.0,K*2b")
    try:
        ser = serial.Serial('COM3')
        #ser.write("$VWVHW, , , ,M,"+str(speed)+",N,"+str(speed*1.852)+",K*48")
        nmeaSentenceVWVHW="VWVHW, , , ,M,"+str(speed)+",N,"+str(speed*1.6)
        #adding Checksum
        i=0
        checksum = 0
        while i < len(nmeaSentenceVWVHW):
            checksum = checksum ^ ord(nmeaSentenceVWVHW[i])
            i+=1
            finalChecksum=(hex(checksum)[2:]).upper()
        finalVWVHW="$"+nmeaSentenceVWVHW+","+finalChecksum
        ser.write(finalVWVHW)
        print (finalVWVHW)
        ser.close()
        pass
    except Exception as msg:
        print("exception:",msg)
        
def WriteToFile(DeltaP, Speed, RegValue):
    file1 = open("log.txt", "a")
    file1.write(strftime("%H:%M:%S-%d/%m/%Y") + "," + str(DeltaP) + "," + str(Speed)+"," + str(RegValue)+"\n")
    file1.close()
    
def updateLine(canvas,ref,xPoint,yPoint):
    canvas.delete(ref)
    drawLine(canvas,250,250,xPoint,yPoint)
    



    
       

