#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

RECV_BUFFER_LENGTH = 1024

from threading import Thread
import socket
from KissHelper import SerialParser
from array import array


CRCTAB = array("H",[
61560,57841,54122,49891,46684,42965,38222,33991,31792,28089,24354,20139,14868,11165,6406,2191,
57593,61808,50155,53858,42717,46932,34255,37958,27825,32056,20387,24106,10901,15132,2439,6158,
53626,49395,62056,58337,38750,34519,46156,42437,23858,19643,32288,28585,6934,2719,14340,10637,
49659,53362,58089,62304,34783,38486,42189,46404,19891,23610,28321,32552,2967,6686,10373,14604,
45692,41973,37230,32999,62552,58833,55114,50883,15924,12221,7462,3247,30736,27033,23298,19083,
41725,45940,33263,36966,58585,62800,51147,54850,11957,16188,3495,7214,26769,31000,19331,23050,
37758,33527,45164,41445,54618,50387,63048,59329,7990,3775,15396,11693,22802,18587,31232,27529,
33791,37494,41197,45412,50651,54354,59081,63296,4023,7742,11429,15660,18835,22554,27265,31496,
29808,26105,22370,18155,12884,9181,4422,207,63544,59825,56106,51875,48668,44949,40206,35975,
25841,30072,18403,22122,8917,13148,455,4174,59577,63792,52139,55842,44701,48916,36239,39942,
21874,17659,30304,26601,4950,735,12356,8653,55610,51379,64040,60321,40734,36503,48140,44421,
17907,21626,26337,30568,983,4702,8389,12620,51643,55346,60073,64288,36767,40470,44173,48388,
13940,10237,5478,1263,28752,25049,21314,17099,47676,43957,39214,34983,64536,60817,57098,52867,
9973,14204,1511,5230,24785,29016,17347,21066,43709,47924,35247,38950,60569,64784,53131,56834,
6006,1791,13412,9709,20818,16603,29248,25545,39742,35511,47148,43429,56602,52371,65032,61313,
2039,5758,9445,13676,16851,20570,25281,29512,35775,39478,43181,47396,52635,56338,61065,65280
])

def logf(message):
    import sys
    print(message, file=sys.stderr)


class AXUDPServer(Thread):
    '''AXUDP Server to communicate with the digipeater'''

    txQueue = None

    # host and port as configured in aprx/aprx.conf.lora-aprs < interface > section
    def __init__(self, txQueue, localHost="127.0.0.1", localPort=10001, remoteHost="127.0.0.1", remotePort="20000"):
        Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((localHost, localPort))
        self.remoteHost=remoteHost
        self.remotePort=remotePort
        self.data = str()
        self.txQueue = txQueue

    def run(self):
        while True:
            frame = self.socket.recv(RECV_BUFFER_LENGTH)
            print("TX:",self.axtostr(frame))
            self.txQueue.put(frame, block=False)
            
    def __del__(self):
        self.socket.shutdown()

    def send(self, data, metadata):
        self.sendax(data, (self.remoteHost, self.remotePort), metadata)
        #self.socket.sendall(data)

    def axcall(self, text, pos):
        l=len(text)
        a=""
        print(text)
        while (pos<l) and (len(a)<6) and ((text[pos]>=ord("0")) and (text[pos]<=ord("9")) or (text[pos]>=ord("A")) and (text[pos]<=ord("Z"))):
            a+=chr(text[pos]<<1)
            pos+=1
        while len(a)<6: a+=chr(ord(" ")<<1)                     #fill with spaces
        ssid=0
        if (pos<l) and (text[pos]==ord("-")):
            pos+=1
            if (pos<l) and (text[pos]>=ord("0")) and (text[pos]<=ord("9")):
                ssid+=text[pos]-ord("0")
                pos+=1
            if (pos<l) and (text[pos]>=ord("0")) and (text[pos]<=ord("9")):
                ssid=ssid*10 + text[pos]-ord("0")
                pos+=1
            if ssid>15: ssid=15
        ssid=(ssid+48)<<1
        if (pos<l) and (text[pos]==ord("*")):
            ssid|=0x80
            pos+=1
        a+=chr(ssid)
        return a, pos


    def udpcrc(self, frame, topos):
        c=0
        for p in range(topos): c = (c >> 8) ^ CRCTAB[(ord(frame[p]) ^ c) & 0xff]
        return c
    def sendax(self, text, ip, values=False):
        a,p=self.axcall(text, 0)                                  #src call
        if (p>=len(text)) or (text[p]!=ord(">")): 
            print("fehler 1")
            return
        ax,p=self.axcall(text, p+1)                               #dest call
        ax+=a
        hbit=0
        while True:                                          #via calls
            if p>=len(text): 
                print("found no end of address")
                return                            #found no end of address
            if text[p]==ord(":"): break                             #end of address field
            if text[p]!=ord(","): 
                print("via path error")
                return                            #via path error
            if len(ax)>=70:  
                print("too many via calls")
                return                            #too many via calls           
            a,p=self.axcall(text, p+1)
            ax+=a 
            hp=len(ax)-1
            if (ord(ax[hp]) & 0x80)!=0: hbit=hp                #store last h-bit
        p+=1
        a=""

        if values:
            a="\x01\x30"                                       #axudp v2 start

            if 'level' in values.keys():
                v=values["level"]
                a+="V"+str(round(v))+" "                     #axudp v2 append level

            if 'quality' in values.keys():
                v=values["quality"]
                a+="Q"+str(round(v))+" "                     #axudp v2 append quality

            if 'txdel' in values.keys():
                v=values["txdel"]
                a+="T"+str(round(v))+" "                     #axudp v2 append quality

            if 'snr' in values.keys():
                v=values["snr"]
                a+="S"+str(round(v))+" "                     #axudp v2 append snr

            a+="\x00"                                          #axudp2 end

        i=0
        for i in range(len(ax)):
            ch=ord(ax[i])
            if (i%7==6) and (i>=20) and (i<hbit): ch|=0x80     #set h-bit on all via calls before
            if i+1==len(ax): ch|=1                             #set ent of address bit
            a+=chr(ch)
        a+="\x03\xf0"                                        #ui frame pid F0
        i=0
        while p<len(text) and i < 256:                                   #append payload
            a+=chr(text[p])
            p+=1
            i+=1                                #max 256bytes
        #for ch in b: print(hex(ord(ch)))     
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        c=self.udpcrc(a, len(a))
        a+=chr(c & 0xff)
        a+=chr(c>>8)
        sa=array("B",[0]*len(a))
        for i in range(0,len(a)): sa[i]=ord(a[i])
        print(sa)
        print(ip)
        res=sock.sendto(sa, ip)

    ## RX:
    def callstr(self, b, p):
        s=""
        for i in range(6):
            ch=ord(b[p+i])>>1
            if ch<32: s+="^"                                     #show forbidden ctrl in call
            elif ch>32:s+=chr(ch)                                #call is filled with blanks
        ssid=(ord(b[p+6])>>1) & 0x0f
        if ssid: s+="-"+str(ssid)
        return s
    def axtostr(self, axbuf):
        b=""
        for x in axbuf: 
            b+=chr(x)
        le=len(b)
        if le<2: 
            return ""
        le-=2
        c=self.udpcrc(b, le)
        if (b[le]!=chr(c & 0xff)) or (b[le+1]!=chr(c>>8)): 
            return ""  #crc error

        i=0
        if axbuf[0]==1:                                         #axudp v2
            while (i<len(axbuf)) and (axbuf[i]!=0): i+=1
            i+=1
        b=""
        while i<len(axbuf):
            b+=chr(axbuf[i])
            i+=1
        s=""
        le=len(b)
        if le>=18:                                             #2 calls + ctrl + pid + crc
            le-=2
            s=self.callstr(b, 7)                                      #src call
            s+=">"+self.callstr(b, 0)                                 #destination call
            p=14
            hbit=False
            while (((not (ord(b[p-1]) & 1)))) and (p+6<le):      #via path
                if ord(b[p+6])>=128: 
                    hbit=True
                elif hbit:                                         #call before had hbit
                    s+="*"
                    hbit=False   
                s+=","+callstr(b, p)
                p+=7
            if hbit: s+="*"                                      #last call had hbit
            p+=2                                                 #pid, ctrl
            s+=":"
            while p<le:                                          #payload may contain ctrl characters
                s+=b[p]
                p+=1
        return s
if __name__ == '__main__':
    '''Test program'''
    import time
    from multiprocessing import Queue

    TCP_HOST = "0.0.0.0"
    TCP_PORT = 10001

    # frames to be sent go here
    KissQueue = Queue()

    server = AXUDPServer(TCP_HOST, TCP_PORT, KissQueue)
    server.setDaemon(True)
    server.start()

    while True:
        server.send(
            "\xc0\x00\x82\xa0\xa4\xa6@@`\x9e\x8ar\xa8\x96\x90q\x03\xf0!4725.51N/00939.86E[322/002/A=001306 Batt=3.99V\xc0")
        data = KissQueue.get()
        print("Received KISS frame:" + repr(data))
