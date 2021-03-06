import socket
import threading
from copy import deepcopy
import sys
import datetime
##keeping database and assocaites as objects leads to greater flexibility
#can write methods in to database which detct ID,name,ADDR collisions,retrive data,
#these methods may be used by other classes: for instance both client and server will likey use getHighestSCORE

##update scores method could be used to get an avg score from all Associates for each associate## with a maxdepth argumeant, naturally
##method Called on the PeerClass instance of Database

class Associate:
  ''' Data structure to store attributes of peers'''
  def __init__(self,ID = None,NAME = None,ADDR = None,SCORE = None,myAUTH = None, thAUTH = None,conn = None):
    self.ID = ID
    self.NAME = NAME
    self.ADDR = ADDR
    self.SCORE = SCORE
    self.myAUTH = myAUTH
    self.thAUTH = thAUTH    
    self.conn = conn
  def AddDatabase(self,inputs):
    self.Database = inputs

  def send(self,msg):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(self.ADDR)
    client.send(msg)

class Database:
  '''Data structure to store peers, with useful methods '''
  def __sub__(self,other) :
    ''' return the complement of other with respect to self'''
    retlist = self.lst[:]
    for associate1 in self.lst:
      for associate2 in other.lst:
        if associate1.ADDR == associate2.ADDR or associate1.ID == associate2.ID: ##and "or" or?
          retlist.remove(associate1)
    return Database(lst = retlist)
  
  def __init__(self,lst = []):
    self.lst = lst

  def __getitem__(self,idx):
    return self.lst[idx]

##should return instance of Database?
  def getAssociateByID(self,ID):
    out = []
    for associate in self.lst:
      if associate.ID == ID:
        out.append(associate)
    return out

  def getAssociateByNAME(self,Name):
    out = []
    for associate in self.lst:
      if associate.Name == Name:
        out.append(associate)
    return out

  def getAssociateByADDR(self,ADDR):
    out = []
    for associate in self.lst:
      if associate.ADDR == ADDR:
        out.append(associate)
    return out

  def append(self,Associate):
    self.lst.append(Associate)


  ##will soon be redundant, refresh scores then index the database instnace (__getitem__)
  def getTopScore(self):
    return sorted(self.lst, key= lambda associate: associate.SCORE)

  def refreshScores(self):
    self.lst.sort(key = lambda associate: associate.SCORE)


  def freeID(self,ID):
    out = []
    for associate in self.lst:
      if associate.ID == ID:
        return False
    return True

  @property
  def share(self,ID):
    string = ""
    for assoicate in self.lst:
      string += ("{assoicate.ID}/{assoicate.ADDR}/{assoicate.SCORE}")
    return string.encode("utf-8")

  def __init__(self,lst = None):##expects list of associates
    if lst != None:
      self.lst = lst
    else:
      self.lst = []


class GMSG:
  '''for live messaging (messages unsaved)'''
  def __init__(self,peer,packit):
    self.peer = peer
    self.members = []
    self.threads = []
    self.packit = packit
    _,_,_ ,self.datestr = packit.split(":")
  def add(self,Associate):
    self.members.append(Associate)
  def listen(self,Associate):
    while True:
      msg = Associate.conn.recv(2040).decode("utf-8")
      ##if self.val(msg): then print , check if everyone got the same message
      print(f"\n{Associate.ID} {Associate.ADDR}: {msg}\n")
  def sendMSG(self,msg):
    for member in self.members:
      member.conn.send(msg.encode("utf-8"))
  def join(self):
    for member in self.members:
      self.threads.append(threading.Thread(target = self.listen, args = [member]))
      self.threads[-1].start()
    while True:
      self.sendMSG(input("\n"))
  
  @property
  def commands(self):
    {"ADD":self.ADD,
     "LEAVE":self.LEAVE,
     "SEND":self.SEND}

class Server:
''' This class handles incomming pakits, returning data to the requestor, updateing database, or initiating groupchat ''' 
  def GMSG(self,packit,conn):
    '''This code initializes the connections between this and all other members of the group chat 
    It is over-complicated and unresilient, decetnralization in the initialization of the groupchat is completely unneccasary. Instead, the first in the chain should make conn with all 
    Then THe second in chain makes conn wth all but the first, the thrird makes conn with all (who are't connected to it) etc'''
    CMD,Req,members,datestr = packit.split(":")
    ID,ADDR = Req.split("-")
    newAssociate = Associate(ID= ID,ADDR = ADDR, conn = conn)
    myAUTH = None
    #print("marker1")
    if str(self.gmsg.datestr) != str(datestr) or conn == None:##act as server, recieveing 
      print(f"recieved (first time): {ADDR}")
      self.gmsg = GMSG(self,packit)
      if conn != None: self.gmsg.add(newAssociate)
      mystrpos = members.find(f"{str(self.ADDR)[1:-1]}")
      mypos = members[:mystrpos].count("/")
      memberlst = members.split("/")
      for x in range(len(memberlst)):
        #print(f"marker3 {x}")
        if x%2 == 1 and mypos+x < len(memberlst):
          ID,ADDRstr = memberlst[x+mypos].split("-")
          ADDRstr = ADDRstr[1:-1]
          ip,port = ADDRstr.split(",")
          ADDR = (ip[1:-1],int(port[1:]))
          newconn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          newconn.connect(ADDR)
          newAssociate = Associate(ID= ID,ADDR = ADDR, conn = newconn)
          newpackit = f"{CMD}:{self.ID}-{self.ADDR}:{members}:{datestr}"
          print(f"sent forwards {ADDR}")
          newAssociate.conn.send(newpackit.encode("utf-8"))
          self.gmsg.add(newAssociate)
        if x%2 == 0 and mypos >= x and x > 0: 
          ID,ADDRstr = memberlst[mypos-x].split("-")
          ADDRstr = ADDRstr[1:-1]
          ip,port = ADDRstr.split(",")
          ADDR = (ip[1:-1],int(port[1:]))
          newconn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          newconn.connect(ADDR)
          newAssociate = Associate(ID= ID,ADDR = ADDR, conn = newconn)
          newpackit = f"{CMD}:{self.ID}-{self.ADDR}:{members}:{datestr}"
          print(f"sent backwards {ADDR}")
          newAssociate.conn.send(newpackit.encode("utf-8"))
          self.gmsg.add(newAssociate)
    elif conn != None:
      print(f"recieved {newAssociate.ADDR}")
      self.gmsg.add(newAssociate)


  def __init__(self,ID,ADDR,database = Database()):
    self.ID = ID
    self.ADDR = ADDR
    self.Database = database
    self.gmsg = GMSG(None,'N:o:n:e')
  
  def CHANGEID(self,packit,conn):
    CMD,DATA  = packit.split(":")
    OLDID,AUTH,NEWID  = DATA.split("/")
    if self.Database.getAssociateByID(OLDID).thAUTH == AUTH and self.Database.freeID(NEWID):
      associate = self.Database.getAssociateByID(OLDID)[0]
      associate.ID = NEWID##Ass is not a copy it is the same instance
      self.CONFIRM(packit,conn,True)
    else:
      self.CONFIRM(packit,conn,False)

  def CONFIRM(self,packit,conn,Bool):
    conn.send((packit+"-"+str(Bool)).encode("utf-8"))
    conn.close()
  
  def CHANGEADDR(self,packit,conn):##needs validation
    CMD,DATA  = packit.split(":")
    ID,AUTH,ADDR  = DATA.split("/")                       ##will VALSEND be evaluated if AUTH not ok?(hopefully not)
    if self.Database.getAssociateByID(ID).thAUTH == AUTH and self.VALSEND(ADDR):##new funcs VALSEND VALRECIEVE
      associate = self.Database.getAssociateByID(ID)[0]
      associate.ADDR = ADDR##Ass is not a copy it is the same instance
      self.CONFIRM(packit,conn,True)
    else:
      self.CONFIRM(packit,conn,False)

  def GETDATA(self,packit,conn):
    ID,auth = packit.split("/")
    conn.send("{self.Database.share}")
    conn.close()

  def GETINFO(self,packit):
    pass

  def handle_client(self):
    myserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    myserver.bind(self.ADDR)
    myserver.listen()
    threads = []
    while True:
      conn,addr  = myserver.accept()
      packit = conn.recv(2040).decode("utf-8")
      CMD = packit[:packit.find(":")]
      threads.append(threading.Thread(target = self.commands[CMD], args = (packit,conn)))
      threads[-1].start()

  def VALSEND(self,associate):
    '''sends a validation request to the  address, to check the address supplied in REG is valid'''
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(associate.ADDR)##uses any availible socket
    validata = "861"
    client.send(f"VAL:{self.ID}/{associate.thAUTH}/{validata}".encode("utf-8"))##could return ID
    res = client.recv(2040).decode("utf-8")
    client.close()
    return res == validata

  def REG(self,packit,conn):
    '''Handles Register request, so Details of the Peer are stored on the server '''
    CMD,DATA = packit.split(":")
    ID,thAUTH,ip,port= DATA.split("/")
    ADDR = (ip,int(port))
    newAssociate = Associate(ID  = ID, thAUTH = thAUTH,ADDR = ADDR)
    if newAssociate.ID not in self.Database.getAssociateByID(ID):
      if self.VALSEND(newAssociate):
        self.Database.append(newAssociate)
        return self.CONFIRM(packit,conn,True)
    return self.CONFIRM(packit,conn,False)

  def VAL(self,packit,conn):
    '''Responds to Validation request '''
    ##should do validation checks here
    CMD,DATA = packit.split(":")
    senderID,AUTH,validata = packit.split("/")##validation such as checking auth,id and other stuff
    conn.send(validata.encode("utf-8"))
    conn.close()
  @property
  def commands(self):
    return {"REG":self.REG,
              "VAL":self.VAL,
              "CHANGEID":self.CHANGEID,
              "CONFIRM":self.CONFIRM,
              "FINDID":self.FINDID,
              "GETDATA":self.GETDATA,
              "CHANGEADDR":self.CHANGEADDR,
              "MSG":self.MSG,
              "GMSG":self.GMSG}

  def FINDID(self,packit,conn):
  '''method may be redundant. It will be replaced with the GETDATA, and the node wanting to add an id will systematically send GETDATA commands 
  other peers in thoses databases, though I could see this command being usseful in some applications'''
    CMD,Req,TGTID,History = packit.split(":")
    ReqID,ReqAUTH = Req.split(",")##can do validation chaeck here
    ##history is equal to  IDone-ipone,portone/IDtwo-iptwo,porttwo/IDthree-ipthree,portthree
    lst = []
    for item in History.split("/"):
      Id,addr = item.split("-")
      ip,port = addr.split(",")
      lst.append(Associate(ID = Id,ADDR = (ip,int(port))))
    relayHistory = Database(lst = lst)
    Requestor = Associate(ID = ReqID,thAUTH = ReqAUTH)
    try:
      packit += str(f":TGTID-{TGTID}-{str(self.Database.getAssociateByID(TGTID)[0].ADDR)}")
      ##new packit should always be made, otherwise authentication keys are sent unneccasirly and to the wrong nodes
      conn.send(packit.encode("utf-8"))
    except IndexError:
      newDatabase = self.Database - relayHistory
      while True:
        newDatabase = newDatabase - relayHistory
        try:
          next_associate = newDatabase.getTopScore()[0]
          History += f"/{next_associate.ID}-{str(next_associate.ADDR)[1:-1]}"
          newpack = f"{CMD}:{self.ID},{next_associate.myAUTH}:{TGTID}:{History}"
          client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          client.connect(next_associate.ADDR)
          client.send(newpack.encode("utf-8"))
          queryresponse = client.recv(2040)
          restring = queryresponse.decode("utf-8")
          client.close()
          if restring.count("TGTID") >= 1:
            conn.send(queryresponse)
            break
        except IndexError:##if database exhausted
          conn.send(History.encode("utf-8"))
          break 
      conn.close()

  def MSG(self,packit,conn):
    def send(conn):
      try: 
        while True:
          inp = input("\n")
          conn.send(inp.encode("utf-8"))
          if inp == "stop": break
        return conn.close()
      except:
        return conn.close()
    def recieve(conn):
      try:
        while True:
          inp = conn.recv(2040).decode("utf-8")
          sys.stdout.write(f"\nthem: {inp}\n")
          if inp == "stop": break
        return conn.close()
      except:
        return conn.close()
    recievethread = threading.Thread(target = recieve, args = [conn]) 
    sendthread = threading.Thread(target = send, args = [conn]) 
    recievethread.start()
    sendthread.start()
    recievethread.join()
    sendthread.join()

class Client:
''' this class creates and send packits to Serverside of peers mainly derived from user commands'''
  def GMSG(self,others):
    ls = [f"{associate.ID}-{associate.ADDR}/" for associate in others]
    string = ''
    string += f"{self.ID}-{self.ADDR}/"
    for x in ls:
      string += x
    ##instead hand over to server method
    mydate = str(datetime.datetime.now()).replace(":",";")
    packit = f"GMSG:{self.ID}-{self.ADDR}:{string[:-1]}:{mydate}"
    self.server.gmsg = GMSG(self.server,packit)
    self.server.GMSG(packit,None)

  def MSG(self,associate):
    def send(client):
      try:
        while True:
          inp = input("\n")
          client.send(inp.encode("utf-8"))
          if inp == "stop": break
        client.close()
      except:
        client.close()
    def recieve(client):
        try:
          while True:
            inp = client.recv(2040).decode("utf-8")
            sys.stdout.write(f"\nthem: {inp}\n")
            if inp == "stop": break
          client.close()
        except:
          client.close()
    packit = f"MSG:{self.ID},{associate.myAUTH}".encode("utf_8")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(associate.ADDR)
    client.send(packit)
    recievethread = threading.Thread(target = recieve, args = [client]) 
    sendthread = threading.Thread(target = send, args = [client]) 
    recievethread.start()
    sendthread.start()
    recievethread.join()
    sendthread.join()
  
  def FINDID(self,TGTID,associate,History = None):
    ''' this command is not the most efficient way to get an address for an id, the GETDATA command is best. The purpose of this command is to 
    Show that it could be possible to implement this system through wireless communication and not through the internet (say if p2p communication was banned)
    Though thinking about it, now i realize it makes no difference: getting the databases back would be better, and signals just being relayed accross the network. 
    but it may be more efficent as databases grow'''
    NEXTID = associate.ID
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(associate.ADDR)
    packit = f"FINDID:{self.ID},{associate.myAUTH}:{TGTID}:{self.ID}-{str(self.ADDR)[1:-1]}/{associate.ID}-{str(associate.ADDR)[1:-1]}".encode("utf-8")
    client.send(packit)
    res = client.recv(2040).decode("utf-8")
    return res

  def __init__(self,ID,ADDR,NAME = None, database = Database()):
    self.ID = ID
    self.ADDR = ADDR
    self.NAME = NAME
    self.Database = database

  def REG(self,associate,AUTH): 
    ip,port = self.ADDR
    myAUTH = AUTH
    packit = f"REG:{self.ID}/{AUTH}/{ip}/{port}".encode("utf-8")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(associate.ADDR)
    client.send(packit)
    conf = client.recv(2040).decode("utf-8")##get serversID from this
    client.close()
    return (conf)
##need to updaye myAUTH associate attribuuet
  def CHANGEID(self,associate,NEWID):##to individual server##could implement myID per associate, for malicous nodes
    packit = f"CHANGEID:{self.ID}/{associate.myAUTH}/{NEWID}".encode("utf-8")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(associate.ADDR)
    client.send(packit)
    res = client.recv(2040).decode("utf-8")
    return res
  def GETDATA(self,associate):
    ### response used to decide whether/how to update ID
    packit = f"GETDATA:{self.ID}/{associate.myAUTH}".encode("utf-8")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(associate.ADDR)
    client.send(packit)
    return client.recv(2040)
  def GETINFO(self,associate):
    packit = f"GETINFO:{self.ID}/{associate.myAUTH}".encode("utf-8")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(associate.ADDR)
    client.send(packit)
    return client.recv(2040)
  @property
  def commands(self):
    return    {"REG":REG,
              "CHANGEID":CHANGEID,
              "FINDID":FINDID,
              "GETDATA":GETDATA}

class Peer:
''' structure to allow sharing of information between server a clinet instance'''
  def __init__(self,ID,ADDR,database = None):
    self.ID = ID
    self.ADDR = ADDR
    self.Database = Database()
    self.server = Server(self.ID,self.ADDR,self.Database)##IT IS SAME INSTANCE
    self.client = Client(self.ID,self.ADDR,self.Database)
    self.server.client = self.client
    self.client.server = self.server
    self.server.client.peer = self##allows peer methods and attributes to be acceced from server and client sub instances
    self.client.server.peer = self#strange recursion?

  def CHANGEID(self,ID,associate):
  '''does now work yet'''
    if self.client.CHANGEID(ID,associate):##needs more proccessing such that the Client method returns a true false value
      self.ID = ID
      self.client.ID = ID
      self.server.ID = ID
  def start(self):
    t1 = threading.Thread(target = self.server.handle_client)
    t1.start()
  @property
  def info(self):
    return Associate(ID = self.ID, ADDR = self.ADDR)
  def testAssociate(self, Associate):
    pass
  def testAllAssociates(self, lst = Database):
    pass
  def CHANGEIDFORALL(self,lst = Database):
    pass
  def estimateSCORE(self):
    pass
  def updateSCORE(self):
    ## closer to mistake, bigger score penalty!
    pass
  def GETDATA(self,others):
    '''return a database which has been built from the Databases of the associates in others list.
    not ready '''
    newDatabase = Database()
    for associate in others:
      newDatabase += self.client.GETDATA(associate)##this method should return a Database instance
    return newDatabase




'''
PORT = 5051
ip = socket.gethostbyname(socket.gethostname())

p0 = Peer("A0",(ip,5000))
p1 = Peer("A1",(ip,5001))
p2 = Peer("A2",(ip,5002))
p3 = Peer("A3",(ip,5003))
p4 = Peer("A4",(ip,5004))
p5 = Peer("A5",(ip,5005))
print(p1.info.ADDR)
p0.Database.append(p1.info)
p1.Database.append(p2.info)
p2.Database.append(p3.info)
p3.Database.append(p4.info)
p4.Database.append(p5.info)


#all the databases are the same instance!
p0.start()
p1.start()
p2.start()
p3.start()
p4.start()
p5.start()
print(p0.client.REG(p0.Database.getAssociateByID("A1")[0],"cabbage"))##p0 registers with p1
print(p0.client.FINDID("A5",p0.Database.getAssociateByID("A1")[0],History = None))##p0 sends to p1 a request to find adress of "A2"
'''