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
    #Associate could have Database atribute, which would be found by using the getdatabase command which does not send auths
    ##could have sanitze method which returns an instance with no sensitive data
    
  def AddDatabase(self,inputs):
    self.Database = inputs


class Database:##beware oop
  #database could 
  ##note the friend varname must change
  ##unbound methods so Server, Client and Associate can access them, but use of instances useful for ...
  ##i want to find a way of 

  def __sub__(self,other) :
    retlist = lst[:]
    for Ass1 in self.lst:
      for Ass2 in other.lst:
        if Ass1.ADDR == Ass2.ADDR or Ass1.ID == Ass2.ID##lambda function better: and "or" or?
          retlist.remove(Ass1)
    return Database(retlist)


  def __init__(self):
    self.lst = [] 

  
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

  def getHighestSCORE(self):
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

  def __init__(lst = None):##expects list of associates
    if lst != None:
      self.lst = lst
    else:
      self.lst = []

##i think that the methods  of server should use Adresses,
class Server:
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

  def REG(self,packit,conn):##scoring mechanism here would be good
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
    CMD,DATA = packit.split(":")
    senderID,AUTH,validata = packit.split("/")##validation such as checking auth,id and other stuff
    conn.send(validata.encode("utf-8"))
    conn.close()
    ##could do some validation checks here
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
  ##every step of the line back the packit can be validated, 
  #if a server reports the packit as malicous it could report it to all serers on the line and the client which sent it
  # if the line is being tested the reporters score won't suffer
    CMD,Req,TGTID,History = packit.split(":")
    ReqID,ReqAUTH = Req.split(",")##can do validation chaeck here
    templst = History.split("/")
    relayHistroy = Database.create(templst)
    Requestor = Associate(ID = ReqID,thAUTH = AUTH)
    try:
      packit += str("/RESULT:" + str(self.Database.getAssociateByID(TGTID)[0].ADDR))
      conn.send(packit)
    except KeyError:
      newDatabase = self.Database - relayHistroy
      while True:
        newDatabase = newDatabase - relayHistroy
        try:
          NextAss = newDatabase.getTopScore()[0]
          History += "/{NextAss.ID},{NextAss.ADDR}"
          newpack = "{CMD}:{self.ID},{self.myAUTH}:{TGTID}:{History}"
          client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          client.connect(NextAss.ADDR)
          client.send(packit)
          queryresponse = client.recv(2040)
          client.close()
          if queryresponse is good:
            conn.send(myqueryresponse)
            conn.recv(2040)##recieving feedback from request(expected outcome, or malicous outcome)
            break
        except IndexError:##if database exhausted
        ##or another error such as one genreate through subtraction of databases
          #also a confirmation packit to original initiator
          #but with reg first so they know im not lying about my identity
          ## this will prevent the findown score method, but in future when requests are prioritized by score, score will be derivable
          conn.send(myresponsetorequestor)
          self.client.REG(iinitiator)
          self.inform initaor of results
          break 
      conn.close()


#why the method of finding ids is best:
#gives more info for scores to be updated:
#but why not retrive Assocaites databses, and search through them dircetly
## there are pros and cons to both methods.
##pro is less communication on network better network speed.
##so the algorythm is done on the client side instead of distributed across the network
##allowing the client to perform its own searching algorythm
##i am sold on it now
##that way is best
## i might make a git repo 







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
    packit = f"FINDID:{self.ID},{self.myAUTH}:{TGTID}:{self.ID},{self.ADDR}/{Associate.ID},{Associate.ADDR}".encode("utf-8")#unsure of NEXTID, perhaps it should be past addresses instead, or even json format of associates!
    client.send(packit)
    res = client.recv(2040).decode("utf-8")
    return res

##this way findid command can be used to estimate ones own score on the network::how fast the commmand comes back to you, by not appending your own address to the end of command
##instead appending a pretendId and address in the history field. !!very useful

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

  def CHANGEID(self,Associate,NEWID):##to individual server##could implement myID per Associate, for malicous nodes
    packit = f"CHANGEID:{self.ID}/{Associate.myAUTH}/{NEWID}".encode("utf-8")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(Associate.ADDR)
    client.send(packit)
    res = client.recv(2040).decode("utf-8")
    return res

    ### response used to decide whether/how to update ID
  def GETDATA(self,Associate):
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
## so client can use server methods and server can use client methods


##potentialfuture
##Differnt ID and AUTH pair used for every single Association
##so self.ID is used as defualt
##nothing wrong with using only one id
##but allows you to move in different circles.
##also accepting a "myID,theirID" argument allows a server to treat clients differently depending upon how they found you


  ##reserveID, id reserved fdor 10secs,
  ##then confirm
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

  def testAllAssociates(self, lst = self.Database):
    pass

  def CHANGEIDFORALL(self,lst = self.Database):
    pass

  def estimateSCORE(self):
    pass

  def updateSCORE(self):
    ## closer to mistake, bigger score penalty!
    pass



PORT = 5051
ip = socket.gethostbyname(socket.gethostname())
p0 = Peer("A0",(ip,5050))
p1 = Peer("A1",(ip,5051))
p2 = Peer("A2",(ip,5052))
p3 = Peer("A3",(ip,5053))
print(p1.info.ADDR)
p0.Database.append(p1.info)
p1.Database.append(p2.info)
p2.Database.append(p1.info)
'''all the databases are the same instance!!'''
p0.start()
p1.start()
p2.start()

print(p0.client.REG(p0.Database.getAssociateByID("A1")[0],"cabbage"))

