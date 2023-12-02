import time
from mpi4py import MPI
import threading
import sys
import enum
import random

# MPI Variables
comm = MPI.COMM_WORLD
pid = comm.Get_rank()

# Raymond's algorithm variables
parent = -1
pending_requests = []


class State(enum.Enum):
    OUT = 0
    REQUESTER = 1
    IN = 2


state = State.OUT
has_token = False   #  000000000000000

# intialize state variables
if pid == 0:
    # this is the very first node
    # we make it root and give it three children
    parent = -1
    has_token = True   #0000000
    # children = [1, 2, 3]
elif pid < 4:
    # first three nodes are direct children of the root node
    parent = 0
else:
    # each node after root and first three is going to be child of a respective node
    # 4 - 3 => child of node 1
    # 5 - 3 => child of node 2
    # 6 - 3 => child of node 3
    parent = pid - 3


# Helper function to print messages quicker and not repeat code
# the file argument is for saying (Error or Just a normal message)



def request_cs():
    global state
    global parent     #00000  
    global has_token   #00000  
    print(pid,'REQUESTs CS') # :I m process',pid , 'and I requests CS') 
    if parent != -1:
        #print('I m process',pid , 'and my parent is', parent)
        pending_requests.append(pid)
        #print('I m process',pid , 'and my list is', pending_requests)
        if state == State.OUT:
            state = State.REQUESTER
            comm.send(['req', pid ], dest=parent, tag=0)  #00000  
    else:
        if has_token == True:    #000000
            enter_cs()


def enter_cs():
    global state
    global parent     #00000  
    global has_token   #00000 
    print(pid ,'ENTERs CS','list',pending_requests) # : I m process',pid , 'and these are my pending requests', pending_requests )
    sys.stdout.flush()

    state = State.IN
    
    #print('I m process number', pid , 'and I m in the CS')
    sys.stdout.flush()
    # simulate a very long time calculating or something
    time.sleep(random.uniform(1, 3))

    release_cs()


def release_cs():
    global state
    global parent     #00000  
    global has_token   #00000 
    state = State.OUT

    print(pid,'RELEASes CS') # : I m process' , pid , 'and I m releasing CS')
    if len(pending_requests) > 0:
        parent = pending_requests.pop(0)
        #print('I m process', pid, 'and I m sending token to' , parent )
        sys.stdout.flush()
        has_token = False    #0000000
        comm.send(['tok',pid], dest=parent, tag=1)
        #time.sleep(1)
        if len(pending_requests) > 0:
            state = State.REQUESTER
            #print('I m process', pid,' and I m sending request to (after releasing CS)', parent)
            sys.stdout.flush()
            comm.send(['req', pid ], dest=parent, tag=0)   #00000000000000


def receive_message() :
    global parent
    global state
    global has_token
    
    while True :
            message = comm.recv(source=MPI.ANY_SOURCE)
            if message[0] == 'req': 
                #print('RECEIVING REQ : I m', pid, 'and I have recieved a request from',message[1])
                sys.stdout.flush()
                if parent == -1 and state == State.OUT and has_token == True :
                    #print('racine recoit requete')
                    parent = message[1]
                    has_token = False 
                    comm.send(['tok', pid] , dest = parent, tag = 1)
                    #print(pid, 'sending tok to' , parent)
                else: 
                #    print('******')
                    pending_requests.append(message[1])
                    #print('list',pending_requests)
                    if state == State.OUT :
                        state = State.REQUESTER
                        comm.send(['req', pid], dest  = parent , tag=0 ) 
            elif  message[0] == 'tok': 
                  print('RECEIVING TOK : I m', pid, 'and I have recieved a token from', message[1])
                  sys.stdout.flush()
                  parent = pending_requests.pop(0)
                  if  parent == pid :
                    parent = -1 
                    has_token = True
                    #print('my pid',pid,'parent',parent,'has tok',has_token)
                    enter_cs()
                  else:
                    comm.send( ['tok', pid ], dest = parent , tag =1) 
                    if len(pending_requests) != 0 :
                        state = State.REQUESTER
                        comm.send( ['req', pid], dest = parent , tag = 0)
                    else:
                        state = State.OUT
                                                
                    
    
    
try:
    thread_receiver = threading.Thread(target=receive_message)
    thread_receiver.start()
except:
    print('There was an error in the thread' )
    sys.stdout.flush()

while True:
      # print('pid',pid,'has tok', has_token,'parent', parent, 'state', state)
      time.sleep(random.uniform(1, 3))
      if state == State.OUT:
         request_cs()
#threading.active_count()