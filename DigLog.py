
from tkinter import *
from tkinter import ttk
from PIL import Image,ImageTk
from utils import *
from adam6000 import *



class digLog:
    #Speed="0"
    def __init__(self, master):
        self.initialiseFile()
        self.initialiseFrames(master)
        #self.Speed = 0
        self.counter=0
        self.readings=[]
        self.maxreadings=50
        self.pointer=None
        #self.runDigLog()
    
        
        print("finished")
        
    def initialiseFile(self):
        """ Open/create log.txt in current directory and write 'Time,DeltaP,Speed\n'
        """
        self.file1 = open("log.txt", "w")
        self.file1.write("Time,DeltaP,Speed\n")
        self.file1.close()
    
    def initialiseFrames(self,master):
        self.Speed=StringVar()
        self.Speed.set('0')
        self.speedString=self.Speed.get()
        mainframe = ttk.Frame(master,padding="3 3 12 12")
        mainframe.pack(fill=BOTH,expand=YES)

        logButton=ttk.Button(mainframe,text='DIGITAL LOG',command=self.runDigLog)
        logButton.grid(column=0,row=0)

        self.logCanvas=Canvas(mainframe,width=500,height=500)
        self.img = ImageTk.PhotoImage(Image.open("Dial2.jpg"))
        #print("img",img)
        #img=PhotoImage(file="dial2.ppm")
        self.logCanvas.create_image(0,0,anchor=NW, image=self.img)
# photoimage = ImageTk.PhotoImage(Image.open('pointer.jpg'))
#logCanvas.create_image(0, 0, anchor=NW,image=photoimage)
        self.logCanvas.grid(column=1,row=0)
#print(photoimage)
        
        #self.Speed.set("Roopes")
        entryStyle=ttk.Style()
        entryStyle.configure('orange.TEntry', background='orange')
        self.digEntry=ttk.Entry(self.logCanvas,width=7,textvariable=self.Speed,font = "Helvetica 34 bold",style='orange.TEntry',justify='center')
        self.logCanvas.create_window(250,420,window=self.digEntry)
        
    def runDigLog(self):
        try:

#             adamModule = Adam6000("169.254.107.55")
#             RegValue = adamModule.ReadRegisterWord(0000)
#             print ("RegValue",RegValue)
#             ProcValue = ReadValueToProcValue(RegValue[4:])
#             print ("ProcValue",ProcValue)
#                 # print ProcValue
#             DeltaP = CurrentToPsi(ProcValue)
#                 # print DeltaP
#             self.speedString = PrToSpeed(DeltaP)
#                 #WriteToSerial(self.Speed)
#             WriteToSerialNmea(self.speedString)
#                 #GenNmeaSentence(self.Speed)
#                 #ReadFromSerial()
#                 # print Speed
#             WriteToFile(DeltaP, self.speedString,RegValue[4:])
#             self.counter+=5
#             theta=speedToTheta(float(self.speedString))
#             xPoint,yPoint=thetaToEndPt(theta)
#             self.pointer=drawLine(self.logCanvas,self.pointer, 250, 250, xPoint, yPoint)
#             self.digEntry.after(1000, self.runDigLog)
#             
            if self.counter<65535:
                self.Speed.set('{0:5.3f}'.format(float(self.speedString)))
                 
                RegValue = ReadValFromDataFile(self.counter)
                print ("RegValue",RegValue)
                ProcValue = ReadValueToProcValue(RegValue[4:])
                print ("ProcValue",ProcValue)
                # print ProcValue
                DeltaP = CurrentToPsi(ProcValue)
                # print DeltaP
                self.speedString = PrToSpeed(DeltaP)
                #WriteToSerial(self.Speed)
                WriteToSerialNmea(self.speedString)
                #GenNmeaSentence(self.Speed)
                #ReadFromSerial()
                # print Speed
                WriteToFile(DeltaP, self.speedString,RegValue[4:])
                self.counter+=5
                theta=speedToTheta(float(self.speedString))
                xPoint,yPoint=thetaToEndPt(theta)
                self.pointer=drawLine(self.logCanvas,self.pointer, 250, 250, xPoint, yPoint)
                self.digEntry.after(1000, self.runDigLog)
            pass
        except Exception as msg:
            print ("exception", msg)
        pass
        print("In DIGILOG")
        
        
root=Tk()
root.title("Digital Log")

digLog(root)

root.mainloop()