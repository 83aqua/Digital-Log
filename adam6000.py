"""
:filename:  adam6000.py
:author:    per@tordivel.no
:version:   1.0
:copyright: 2000-2015 Tordivel AS
:license:   Tordivel AS' Scorpion Python Module License

Allows access to Adam 6050, 6051, 6017 and other 6000 series cards

.. code::

  methods:
    ReadInput(ch)                - read one digital input, specified by ch
    ReadOutput(ch)               - read one digital output, specifed by ch
    WriteOutput(ch,val)          - write one digital output, specifed by ch and val
    ReadWord(addr)               - read word starting at byte 0 + addr, in bytes
    WriteWord(addrOff,data)      - addressOffset - use 0 for 00001-000016 addresses values or 2 for 00017-00XXX values;
                                   data - write word starting at byte 0 + addr, in bytes
    ReadRegisterWord(addr)       - read word starting at address 40000 + addr, in words
    WriteRegisterWord(addr, val) - write word starting at address 40000 + addr, in words
    ResetCounter(counterNo)      - counter function, only for ADAM-6051
    ReadCounter(counterNo)       - counter function, only for ADAM-6051
    close()

  constructor:

    a=Adam6000(ip='10.0.0.1',KeepOpen=1,timeout=1.0,unit=1,port=502)
     KeepOpen - if 1 keep socket open until close() is called
     timeout  - socket read timeout value
     ip,port  - Adam IP,port
     unit     - unit number. Use default 1


Usage samples::

  try:
    a=Adam6000('10.0.0.1',1)
    ok,txt,msg = a.WriteOutput(0,1)
    ok,txt,val = a.ReadInput(0)
  except:
    print "exception"

Revision history::

 1.0.0.4  - 25Jun2015, RL: fixed ReadRelay
 1.0.0.3  - 10Jun2015, RL: supports Scorpion IO Interface, SIO (added Read/WriteRelay, ReadDI, ReadDIs, ReadRelays)
 1.0.0.2  - 31Jan2011, RL: direct access to advantech memory and registers - enables to control all 6000 series cards
 1.0.0.1  - 28Jan2011, PB: initial version

"""

from socket import *
from _thread import *

def _l2str(l):
    s=''
    for it in l: s+=chr(it)
    return s

def _str2l(s):
    l=[]
    for ch in s:
        l.append( ord(ch) )
    return l

class Adam6000:
    def __init__(self,ip='10.0.0.1',KeepOpen=1,timeout=1.0,unit=1,port=502):
        "a=Adam6000(ip,keepopen,timeout)"
        "ip='10.0.0.1', KeepOpen=1, timeout=1.0"
        self.ipproxy=''
        self.proxytrace =[]

        self._unit = unit
        self._timeout = timeout
        self._keepOpen = KeepOpen
        self._ip = ip
        self._port = port

        self.sock = socket(AF_INET,SOCK_STREAM)
        self.sock.settimeout(self._timeout)
        if KeepOpen:
            try:
                self.sock.connect( (ip, self._port) )
            except:
                self._keepOpen = 0
                self.close()
                raise Exception('Failed to connect to Adam module')

    def proxykill(self):
        "kill the proxy thread. Open a socket and let it time out.  The thread terminates after 1s"
        "Only for spying on communication"
        s=socket(AF_INET,SOCK_STREAM)
        try:
            s.connect( ( self.ipproxy,self._port) )
        except:
            pass
        s.close()
        return self.proxytrace[0:]



    def __p_spy(self,ip,port):
        "thread which implements a proxy between a client and the 6060 module"
        self.ipproxy=ip
        print ('__p_spy',ip,port)
        s=socket(AF_INET,SOCK_STREAM)
        s.bind( (ip,port) )
        while 1:
            s.listen(1)
            con,addr = s.accept()
            con.settimeout(1.0)
            try:
                rq=con.recv(255)
                self.proxytrace.append( ('proxy rq:%d chars' % len(rq)) +str(rq) )
            except:
                self.proxytrace.append( 'proxy: timeout - aborting' )
                con.close()
                s.close()
                return
            if not self._keepOpen:
                self.sock=socket(AF_INET,SOCK_STREAM)
                self.sock.connect( (ip,port) )
            self.sock.send(rq)
            try:
                resp=self.sock.recv(255)
            except:
                self.proxytrace.append( 'proxy: module not responding' )
                con.close()
                s.close()
                if not self._keepOpen: self.sock.close()
                return
            if not self._keepOpen: self.sock.close()
            con.send( resp )
            self.proxytrace.append( ('proxy rp:%d chars' % len(resp))+str(resp) )
        s.close()
        #callback ('proxy terminated')

    def proxy(self,ip):
        "Start the proxy thread"
        "ip=fake address port=502"
        print ('starting spy thread')
        #tid=start_new_thread(self.__p_spy,(ip,502))
        tid=self.__p_spy,(ip,502)
        print ('proxy started')


    def close(self):
        "close the socket if open"
        if self._keepOpen:
            self.sock.close()


    def _reconnect(self):
        if not self._keepOpen:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.settimeout(self._timeout)
            try:
                self.sock.connect( (self._ip, self._port) )
            except:
                self.close()
                return (0,'Adam6000 No Connection at: %s [%d]' % (self._ip, self._port),'')

    def _getCommandHead(self, transactionId = 0, protocolId = 0, lenghtField = 6):
        tId = transactionId & 0x0000ffff    # WORD
        pId = protocolId & 0x0000ffff    # WORD
        l = lenghtField & 0x0000ffff    # WORD
        return [tId>>8, tId & 0xff, pId>>8, pId & 0xff, l>>8, l & 0xff]

    def _getCommandBody(self, functionCode, startAddress, requestNumber, unitId = 1):
        fc = functionCode & 0xff
        sa = startAddress & 0x0000ffff  # WORD
        rn = requestNumber & 0x0000ffff #WORD
        return [unitId & 0xff, fc, sa>>8, sa & 0xff, rn>>8, rn & 0xff]

    def _sendAndVerify(self, command):
        # convert to string
        msg = _l2str(command)

        # send to ADAM
        try:
            self.sock.send( msg )
        except Exception as msg:
            return (0, "(Adam6000._sendAndVerify) Lost connection (%s)" % msg, "")

        # wait for reply
        try:
            reply = self.sock.recv(255)
        except Exception as msg:
            if not self._keepOpen:
                self.sock.close()
            return (0, "(Adam6000._readInputStatus) Timeout (%s)" % msg, "")

        if not self._keepOpen:
            self.sock.close()

        # decode result
        replyData = _str2l(reply)

        # verify that we have enough data
        if len(replyData) < 6:
            return (0, "Wrong response length (%d)" % len(replyData), replyData)

        # verify transaction and protocol
        if replyData[0:3] != command[0:3]:
            return (0, "Wrong transaction or protocol %s!=%s" % (str(replyData[0:3]), str(command[0:3])), replyData)

        dataSize = replyData[4]<<8
        dataSize = dataSize | replyData[5]
        if len(replyData) < dataSize:
            return (0, "Not enough data", replyData)

        return (1, "ok", replyData)

    def _forceSingleCoil(self, startAddress, forceData):
        self._reconnect()

        # format command header and command body
        command = self._getCommandHead(lenghtField = 6)
        command.extend( self._getCommandBody(0x05, startAddress, forceData, self._unit) )

        # send and verify response
        resp = self._sendAndVerify(command)
        if resp[0] != 1:
            return resp
        replyData = resp[2]

        # verify unit number and command number and byte count
        if replyData != command:
            return (0, "Command and response should match %s!=%s" % (str(replyData), str(command)), replyData)

        result = replyData[9:9 + replyData[8]]

        # success
        return (1, "ok", result)

    def _readCoilStatus(self, startAddress, coilCount):
        """ startAddress - register start address
            coilCount    - coil count to read (bits)

            returns tuple of (int, str, array) where:
                item 1 = 1 for success, 0 for error
                item 2 = Error message or empty if success
                item 3 = bytes read
        """
        self._reconnect()

        # format command header and command body
        command = self._getCommandHead(lenghtField = 6)
        command.extend( self._getCommandBody(0x01, startAddress, coilCount, self._unit) )

        # send and verify response
        resp = self._sendAndVerify(command)
        if resp[0] != 1:
            return resp
        replyData = resp[2]

        # verify unit number and command number and byte count
        if replyData[6:8] != command[6:8]:
            return (0, "Wrong unit or command or byte count %s!=%s" % (str(replyData[6:7]), str(command[6:7])), replyData)

        result = replyData[9:9 + replyData[8]]

        # success
        return (1, "ok", result)

    def _readHoldingRegisters(self, startAddress, wordCount):
        """ startAddress - register start address
            wordCount    - word count to read

            returns tuple of (int, str, array) where:
                item 1 = 1 for success, 0 for error
                item 2 = Error message or empty if success
                item 3 = words read
        """
        self._reconnect()

        # format command header and command body
        command = self._getCommandHead(lenghtField = 6)
        command.extend( self._getCommandBody(0x03, startAddress, wordCount, self._unit) )

        # send and verify response
        resp = self._sendAndVerify(command)
        if resp[0] != 1:
            return resp
        replyData = resp[2]

        # verify unit number and command number and byte count
        if replyData[6:8] != command[6:8]:
            return (0, "Wrong unit or command or byte count %s!=%s" % (str(replyData[6:7]), str(command[6:7])), replyData)

        result = replyData[9:9 + replyData[8]]

        # success
        return (1, "ok", result)

    def _readInputStatus(self, startAddress, coilCount):
        """ startAddress - register start address for outputs use 0x00000011 (17 dec)
            coilCount    - coil count to set (max 16)

            returns tuple of (int, str, array) where:
                item 1 = 1 for success, 0 for error
                item 2 = Error message or empty if success
                item 3 = raw response
        """
        self._reconnect()

        # format command header and command body
        command = self._getCommandHead(lenghtField = 6)
        command.extend( self._getCommandBody(0x02, startAddress, coilCount, self._unit) )

        # send and verify response
        resp = self._sendAndVerify(command)
        if resp[0] != 1:
            return resp
        replyData = resp[2]

        # verify unit number and command number and byte count
        if replyData[6:8] != command[6:8]:
            return (0, "Wrong unit or command or byte count %s!=%s" % (str(replyData[6:7]), str(command[6:7])), replyData)

        result = replyData[9:9 + replyData[8]]

        # success
        return (1, "ok", result)

    def _forceMultipleCoils(self, startAddress, coilCount, byteCount, forceData):
        """ startAddress - register start address
            coilCount    - coil count to set (1 to 16)
            byteCount    - data byte count (max 2)
            forceData    - WORD where bit values are explained below:

                Example: Request to force a series of 10 coils starting at address 00016 (10 hex) in ADAM-6000 module.
                         01 0F 00 11 00 0A 02 CD 01

                The query data contents are two bytes: CD 01 hex, equal to 1100
                1101 0000 0001 binary. The binary bits are mapped to the addresses in the following way.
                Bit:              1  1  0  0  1  1  0  1    0  0  0  0  0  0  0  1
                Address (000XX): 24 23 22 21 20 19 18 17   -  -  -  -  -  -  26 25

            returns tuple of (int, str, array) where:
                item 1 = 1 for success, 0 for error
                item 2 = Error message or empty if success
                item 3 = raw response

        """
        self._reconnect()

        fd = forceData & 0x0000ffff # force to WORD

        # format command header and command body
        command = self._getCommandHead(lenghtField = 9)
        command.extend( self._getCommandBody(0x0f, startAddress, coilCount, self._unit) )

        # add byte count and data
        command.extend( [byteCount & 0xff, fd>>8, fd & 0xff] )

        # send and verify response
        resp = self._sendAndVerify(command)
        if resp[0] != 1:
            return resp
        replyData = resp[2]

        # verify unit number and command number
        if replyData[6:7] != command[6:7]:
            return (0, "Wrong unit or command %s!=%s" % (str(replyData[6:7]), str(command[6:7])), replyData)

        # success
        return (1, "ok", "")

    def WriteWord(self, addrOffset, data):
        """ Writes two bytes (word) starting at address 0 plus addrOffset
               addrOffset - address offset in bytes
               data       - two bytes of data to write

            lowest bit is coil 0, highest is coil 15
            example: to turn on both coil 0 and 1, call WriteOutputsWord(3)
        """
        dta = data & 0x0000ffff         # force to WORD

        # because we need to pass bytes to force coils and 1st byte is lowest order we need to rearrange word
        low = (data & 0x00ff)<<8
        ordered = ((data & 0xff00)>>8) | low

        return self._forceMultipleCoils(addrOffset*8, 16, 2, ordered)


    def ReadWord(self, addr):
        """ Reads word starting at address 0
        """
        result = self._readInputStatus(addr*8, 16)
        if result[0] == 1:
            if len(result[2]) == 2:
                word = result[2][1]<<8 | result[2][0]
                return (result[0], result[1], word)
            else:
                return (0, "Invalid result", str(result))
        return result



    def ReadCounter(self, counterNo):
        """ Reads counter value
            index starts with 0
        """
        result = self._readHoldingRegisters(24 + (counterNo*2), 2)  # address here is just from tested device 6051 (its not in documetnation!!!)
        if result[0] == 1:
            if len(result[2]) == 4:
                int = result[2][2]<<24 | result[2][3]<<16 |result[2][0]<<8 | result[2][1]
                return (result[0], result[1], int)
            else:
                return (0, "Invalid result", str(result))
        return result


    def ResetCounter(self, counterNo):
        """ Resets counter value
            index starts with 0
        """
        num2 = (0x20 + ((12 + counterNo) * 4)) + 1;  # address not documented and is tested on device 6051 only
        result = self._forceSingleCoil(num2, 0xff00)
        return result


    def WriteOutput(self, ch, val):
        """ Write value to output channel ch
             if val == 0 then output is off else on
        """
        if val:
            val = 0xff00
        return self._forceSingleCoil(16 + ch, val)


    def ReadOutput(self, ch):
        """ Read output value for channel
             returns:
               1 if on
               0 if off (touple index 2)
        """
        ok, txt, val = self.ReadWord(2)
        if ok: return (ok, txt, (val >> ch) & 0x01 )
        else:  return (ok, txt, val)


    def ReadInput(self, ch):
        """ Read specified input channel
             returns:
               1 if on
               0 if off (touple index 2)
        """
        ok, txt, val = self.ReadWord(0)
        if ok: return (ok, txt, (val >> ch) & 0x01 )
        else:  return (ok, txt, val)


    def ReadRegisterWord(self, addr):
        """ read one byte at speciufied address
        """
        result = self._readHoldingRegisters(addr, 1)
        if result[0] == 1:
            if len(result[2]) == 2:
                val = result[2][0]<<8 | result[2][1]
                return (result[0], result[1], val)
            else:
                return (0, "Invalid result", str(result))
        return result


    def WriteRegisterWord(self, addr, val):
        """ write ome byte at specified address
        """
        self._reconnect()

        # format command header and command body
        command = self._getCommandHead(lenghtField = 6)
        command.extend( self._getCommandBody(0x10, addr, 1, self._unit) )

        # add byte count and data
        val = 0x0000ffff & val
        command.extend( [2, val>>8, val & 0xff] )

        # send and verify response
        resp = self._sendAndVerify(command)
        if resp[0] != 1:
            return resp
        replyData = resp[2]

        # verify unit number and command number and byte count
        if replyData[6:8] != command[6:8]:
            return (0, "Wrong unit or command or byte count %s!=%s" % (str(replyData[6:7]), str(command[6:7])), replyData)

        result = replyData[9:9 + replyData[8]]

        # success
        return (1, "ok", result)




    def WriteRelay(self, ch, val):
        """ SIO wrapper for doWriteBit"""
        return self.WriteOutput(ch, val)


    def ReadRelay(self, ch):
        """ SIO wrapper for doReadBit"""
        return self.ReadOutput(ch)


    def ReadDI(self, ch):
        """ SIO wrapper for diReadBit"""
        return self.ReadInput(ch)


    def ReadRelays(self):
        """ SIO wrapper for doReadByte"""
        return self.ReadWord(2)


    def ReadDIs(self):
        """ SIO wrapper for diReadByte"""
        return self.ReadWord(0)




