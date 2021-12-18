import socket
import threading
from copy import deepcopy
##keeping database and assocaites as objects leads to greater flexibility
#can write methods in to database which detct ID,name,ADDR collisions,retrive data,
#these methods may be used by other classes: for instance both client and server will likey use getHighestSCORE

##update scores method could be used to get an avg score from all Associates for each associate## with a maxdepth argumeant, naturally
##method Called on the PeerClass instance of Database

class GMSG:
  pass

class Associate:
  def __init__(self,ID = None,NAME = None,ADDR = None,SCORE = None,myAUTH = None, thAUTH = None):
    self.ID = ID
    self.NAME = NAME
    self.ADDR = ADDR
    self.SCORE = SCORE
    self.myAUTH = myAUTH
    self.thAUTH = thAUTH    
  def AddDatabase(self,inputs):
    self.Database = inputs
  ##more methods for associate may be useful: comparative operator, 

class Database:
  def __sub__(self,other) :
    retlist = self.lst[:]
    for Ass1 in self.lst:
      for Ass2 in other.lst:
        if Ass1.ADDR == Ass2.ADDR or Ass1.ID == Ass2.ID: ##and "or" or?
          retlist.remove(Ass1)
    return Database(lst = retlist)
  
  def __init__(self,lst = []):
    self.lst = lst
  
  def getAssociateByID(self,ID):## the getByID Commands could return instance of database.
    out = []
    for Friend in self.lst:
      if Friend.ID == ID:
        out.append(Friend)
    return out

  def getAssociateByNAME(self,Name):
    out = []
    for Friend in self.lst:
      if Friend.Name == Name:
        out.append(Friend)
    return out

  def getAssociateByADDR(self,ADDR):
    out = []
    for Friend in self.lst:
      if Friend.ADDR == ADDR:
        out.append(Friend)
    return out
  
  def append(self,Associate):
    self.lst.append(Associate)

  def getTopScore(self):
    return sorted(self.lst, key= lambda Ass: Ass.SCORE)

  def freeID(self,ID):
    out = []
    for Friend in self.lst:
      if Friend.ID == ID:
        return False
    return True
  
  @property
  def share(self,ID):
    string = ""
    for Ass in self.lst:
      string += ("{Ass.ID}/{Ass.ADDR}/{Ass.SCORE}")
    return string.encode("utf-8")

  def __init__(self,lst = None):##expects list of associates
    if lst != None:
      self.lst = lst
    else:
      self.lst = []

##i think that the methods  of server should use Adresses,
class Server:
  ##could have a temp databases which gets cleared every several commands. temp databses stores the details of peers which have been invovled in comms with
  def __init__(self,ID,ADDR,database = Database()):
    self.ID = ID
    self.ADDR = ADDR
    self.Database = database

  def CHANGEID(self,packit,conn):
    CMD,DATA  = packit.split(":")
    OLDID,AUTH,NEWID  = DATA.split("/")
    if self.Database.getAssociateByID(OLDID).thAUTH == AUTH and self.Database.freeID(NEWID):
      Ass = self.Database.getAssociateByID(OLDID)[0]
      Ass.ID = NEWID##Ass is not a copy it is the same instance
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
      Ass = self.Database.getAssociateByID(ID)[0]
      Ass.ADDR = ADDR##Ass is not a copy it is the same instance
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
    while True:
      conn,addr  = myserver.accept()
      packit = conn.recv(2040).decode("utf-8")
      CMD = packit[:packit.find(":")]
      self.commands[CMD](packit,conn)

  def VALSEND(self,Associate):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(Associate.ADDR)##uses any availible socket
    validata = "861"
    client.send(f"VAL:{self.ID}/{Associate.thAUTH}/{validata}".encode("utf-8"))##could return ID
    res = client.recv(2040).decode("utf-8")
    client.close()
    return res == validata

  def REG(self,packit,conn):##scoring mechanism
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
              "CHANGEADDR":self.CHANGEADDR}

  def FINDID(self,packit,conn):
  ##every step of the line back the packit should be validated, 
  #if a server reports the packit as malicous it could report it to all serers on the line and the client which sent it
  # if the line is being tested the reporters score won't suffer
  ##future validations: every server along the line is inforemd of the pakit recieved by everyother server.
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
      packit += str("TGTID:"+str(self.Database.getAssociateByID(TGTID)[0].ADDR))
      conn.send(packit.encode("utf-8"))
    except IndexError:
      newDatabase = self.Database - relayHistory
      while True:
        newDatabase = newDatabase - relayHistory
        try:
          NextAss = newDatabase.getTopScore()[0]
          History += f"/{NextAss.ID}-{str(NextAss.ADDR)[1:-1]}"
          newpack = f"{CMD}:{self.ID},{NextAss.myAUTH}:{TGTID}:{History}"
          client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          client.connect(NextAss.ADDR)
          client.send(packit.encode("utf-8"))
          queryresponse = client.recv(2040)
          restring = queryresponse.decode("utf-8")
          client.close()
          if restring.count("TGTID") >= 1:
            conn.send(queryresponse)
            break
        except IndexError:##if database exhausted
          #or another error such as one genreate through subtraction of databases
          conn.send(History.encode("utf-8"))
          break 
      conn.close()

#why the method of finding ids is best:
#gives more info for scores to be updated:
#but why not retrive Assocaites databses, and search through them dircetly
## there are pros and cons to both methods.
##pro is less communication on network better network speed.
##so the algorythm is done on the client side instead of distributed across the network
##allowing the client to perform its own searching algorythm
## con is that there is less incentive to have a high score, and that in the future, certain servers want to be 
##quered by a smaller number of other servers, so going through proxies is a way for this to happen
##both implemntations can exist side by side

class Client:
  ##IF A NODE does not respond directly, the client should query them 
  ##if node doesnt respond, its accepted it was off,
  ##if a node does respond, but says it wasnt queried, (the node directly connected to it)'s integraty is called into question
  ##if a node responds and says it was queried but had no results, then  it was that nodes own fault and its score is reduced
  ## any deviations are forwded to the nodes directly connected to those with the deviations
  ##scores updated accordingly
  ##everyone knows everything, shared knowledge is what runs the network.
  def FINDID(self,TGTID,Associate,History = None):
    NEXTID = Associate.ID
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(Associate.ADDR)
    packit = f"FINDID:{self.ID},{Associate.myAUTH}:{TGTID}:{self.ID}-{str(self.ADDR)[1:-1]}/{Associate.ID}-{str(Associate.ADDR)[1:-1]}".encode("utf-8")
    client.send(packit)
    res = client.recv(2040).decode("utf-8")
    return res

  def __init__(self,ID,ADDR,database = Database()):
    self.ID = ID
    self.ADDR = ADDR
    self.Database = database

  def REG(self,Associate,AUTH): 
    ip,port = self.ADDR
    myAUTH = AUTH
    packit = f"REG:{self.ID}/{AUTH}/{ip}/{port}".encode("utf-8")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(Associate.ADDR)
    client.send(packit)
    conf = client.recv(2040).decode("utf-8")##get serversID from this
    client.close()
    return (conf)
##need to updaye myAUTH Associate attribuuet
  def CHANGEID(self,Associate,NEWID):##to individual server##could implement myID per Associate, for malicous nodes
    packit = f"CHANGEID:{self.ID}/{Associate.myAUTH}/{NEWID}".encode("utf-8")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(Associate.ADDR)
    client.send(packit)
    res = client.recv(2040).decode("utf-8")
    return res

  def GETDATA(self,Associate):
    ### response used to decide whether/how to update ID
    packit = f"GETDATA:{self.ID}/{Associate.myAUTH}".encode("utf-8")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(Associate.ADDR)
    client.send(packit)
    return client.recv(2040)

  def GETINFO(self,Associate):
    packit = f"GETINFO:{self.ID}/{Associate.myAUTH}".encode("utf-8")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(Associate.ADDR)
    client.send(packit)
    return client.recv(2040)

  @property
  def commands(self):
    return    {"REG":REG,
              "CHANGEID":CHANGEID,
              "FINDID":FINDID,
              "GETDATA":GETDATA}

class Peer:
  def __init__(self,ID,ADDR,database = None):
    self.ID = ID
    self.ADDR = ADDR
    self.Database = Database()
    self.server = Server(self.ID,self.ADDR,self.Database)##copy of or is?
    self.client = Client(self.ID,self.ADDR,self.Database)
    self.server.client = self.client
    self.client.server = self.server
    self.server.client.peer = self##allows peer methods and attributes to be acceced from server and client sub instances
    self.client.server.peer = self#strange recursion?


## so client can use server methods and server can use client methods
##potentialfuture
##Differnt ID and AUTH pair used for every single Association
##so self.ID is used as defualt
##nothing wrong with using only one id
##but allows you to move in different circles.
##also accepting a "myID,theirID" argument allows a server to treat clients differently depending upon how they found you


  def CHANGEID(self,ID):##needs more thought, much more thought
    if self.client.CHANGEID(ID):
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

PORT = 5051
ip = socket.gethostbyname(socket.gethostname())

p0 = Peer("A0",(ip,5000))
p1 = Peer("A1",(ip,5001))
p2 = Peer("A2",(ip,5002))
p3 = Peer("A3",(ip,5003))
print(p1.info.ADDR)
p0.Database.append(p1.info)
p1.Database.append(p2.info)
p2.Database.append(p3.info)
'''all the databases are the same instance!!'''
p0.start()
p1.start()
p2.start()
print(p0.client.REG(p0.Database.getAssociateByID("A1")[0],"cabbage"))##p0 registers with p1
print(p0.client.FINDID("A3",p0.Database.getAssociateByID("A1")[0],History = None))##p0 sends to p1 a request to find adress of "A2"
