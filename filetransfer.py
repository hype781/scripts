#function for connecting and uploading data
def sftp_put(client, host, port, key, zip, gpg_key,sign,armor, user, local_dir, mask, remote_dir, archive_dir):
    connected = True
    print 'Connecting to: ' + host + ' Port: ' + port
    logMessage = client + ' connecting to: ' + host + ' Port: ' + port
    #logging.info(logMessage)
    try:
        transport = paramiko.Transport((host, int(port)))
    except Exception, e:
        print "Error:",e
        subject = client + " Connection error to " + host
        errorMessage = "Connection error " + client + " cannot connect to " + host + " Error message: " + str(e) 
        send_mail("Critical", subject, errorMessage)
        logging.warning(errorMessage)
        connected = False
        
    
    if os.path.exists(key): 
        rsa_key = paramiko.RSAKey.from_private_key_file(key)
    else:
        subject = client + " Key file missing to " + host
        print "Key file missing !", key
        errorMessage = "Key file missing! " + client 
        send_mail("Warning", subject, errorMessage)
        logging.warning(errorMessage)
        connected = False
    
    if connected:
        try: 
            transport.connect(username = user, pkey=rsa_key)
        #except paramiko.AuthenticationException:
        except Exception, e:
            print "We had an authentication exception!",e
            subject = client + " " + str(e)
            errorMessage = "Authentication error " + client + " cannot connect to " + host + " Error message: " + str(e) 
            send_mail("Warning", subject, errorMessage)
            logging.warning(errorMessage)
            connected = False
    
    # Go!
    if connected:
        try:
            sftp = paramiko.SFTPClient.from_transport(transport)        
        except Exception, e:
            print "Error:",e
            subject = client + " Connection error to " + host
            errorMessage = "Connection error " + client + " cannot connect to " + host + " Error message: " + str(e) 
            send_mail("Critical", subject, errorMessage)
            logging.warning(errorMessage)
            connected = False
            
    
        
    # Upload
    if connected:
      
        #files = os.listdir(local_dir)          
        #opt1
        localdir = local_dir + mask
        print localdir
        for send_file in glob.glob(localdir):
            #check for file is not a directory
            if os.path.isfile(send_file):
                file_name = os.path.basename(send_file)
                
                print file_name
                print 'Uploading: ' + send_file
                localpath = send_file
                remotepath = remote_dir + file_name
                archivepath = localpath
                #Zip compress if set
                if zip == "yes":
                    file_name = os.path.splitext(file_name)[0] + ".zip"
                    localpath = os.path.splitext(send_file)[0] + ".zip"
                    archivepath = localpath
                    remotepath = remote_dir + file_name 
                    #archivepath = file_name + ".zip"
                    print 'Compressing: ' + send_file + ' to ' + localpath
                    zf = zipfile.ZipFile(localpath, mode="w", compression=zipfile.ZIP_DEFLATED)
                    zf.write(send_file, basename(send_file))
                    zf.close()
                    os.remove(send_file)
                #zip
                #Encrypting if gpg_key is set
                if gpg_key:
                    if armor == "yes":
                        print 'Encrypting: ' + send_file + ' to ' + localpath
                        if sign:
                            if os.path.exists(basedir + "keys/" + sign + ".sgn"):
                                print "Singing with key: " + "keys/" + sign + ".sgn"
                                file = open(basedir + "keys/" + sign + ".sgn", 'r')
                                encoded = file.read()
                                passphrase = encoded.decode('base64')
                                file.close()
                                return_code = subprocess.call([gpgBinPath, "--multifile", "--batch", "--sign", "-u", sign, "--passphrase", passphrase, "--armor", "--yes", "-e", "-r", gpg_key, localpath])
                            else:
                                errorMessage = client + " Sign file " + "keys/" + sign + ".sgn" + " not exits"
                                subject = client + " Sign error"
                                send_mail("Warning", subject, errorMessage)
                                print "Sign file not found " + "keys/" + sign + ".sgn"
                                logging.warning(errorMessage)
                                connected = False
                        else:
                            return_code = subprocess.call([gpgBinPath, "--multifile", "--batch", "--armor", "--yes", "-e", "-r", gpg_key, localpath])
                        archivepath = localpath 
                        localpath = localpath + ".asc"
                        remotepath = remotepath + ".asc"
            
                    else:
                        print 'Encrypting: ' + send_file + ' to ' + localpath
                        if sign:
                            if os.path.exists(basedir + "keys/" + sign + ".sgn"):
                                print "Singing with key: " + "keys/" + sign + ".sgn"
                                file = open(basedir + "keys/" + sign + ".sgn", 'r')
                                encoded = file.read()
                                passphrase = encoded.decode('base64')
                                file.close()
                                return_code = subprocess.call([gpgBinPath, "--multifile", "--sign", "-u", sign, "--passphrase", passphrase, "--batch", "--yes", "-e", "-r", gpg_key, localpath])
                            else:
                                errorMessage = client + " Sign file " + "keys/" + sign + ".sgn" + " not exits"
                                subject = client + " Sign error"
                                send_mail("Warning", subject, errorMessage)
                                print "Sign file not found " + "keys/" + sign + ".sgn"
                                logging.warning(errorMessage)
                                connected = False
                        else:                       
                            return_code = subprocess.call([gpgBinPath, "--multifile", "--batch", "--yes", "-e", "-r", gpg_key, localpath])
                        archivepath = localpath 
                        localpath = localpath + ".gpg"
                        remotepath = remotepath + ".gpg"
                    
                    logMessage = 'GPG encryption done on ' + localpath
                    logging.info(logMessage)
                
                    #gpg encryption
                if connected:   
                    if os.path.exists(localpath):
                        try:
                            print "localpath: " + localpath + " Remotepath: " + remotepath
                            sftp.put(localpath, remotepath)
                            print "sftp done"
                            f = open('report.txt','a')
                            text = str(time) + " " + client + ' ' + localpath + ' uploaded \n' 
                            f.write(text)
                            logMessage = client + ' Uploading: ' + localpath 
                            logging.info(logMessage)
                        except Exception, e:
                            print "Error:",e
                            subject = client + " " + str(e)
                            errorMessage = "File transfer error " + client + " file: " + localpath + " to " + remotepath + " on "  + host + " Error message: " + str(e) 
                            send_mail("Warning", subject, errorMessage)
                            logging.warning(errorMessage)
                            connected = False
                    else:
                        subject = client + " " + localpath + " not found"
                        errorMessage = "File transfer error " + client + " file: " + localpath + " not found " 
                        send_mail("Warning", subject, errorMessage)
                        logging.warning(errorMessage)
                        connected = False
                    
                if connected:
                    
                    if os.path.isdir(archive_dir):
                        destination = archive_dir + file_name
                        print "Moving files to archive"
                        print archivepath, destination
                        #from shutil import move
                        #os.rename(localpath, destination)
                        try:
                            #shutil.move(localpath,destination)
                            shutil.copy(archivepath,destination)
                            return_code = subprocess.call([gpgBinPath, "--multifile", "--batch", "--yes", "-e", "-r", "Infrastructure", destination])
                            os.remove(localpath)
                            if gpg_key:
                                os.remove(archivepath)
                            os.remove(destination)
                        except Exception, e:
                            print "Error:",e
                            subject = client + " " + str(e)
                            errorMessage = "File Move error " + client + " file: " + localpath + " to " + destination  + " on "  + host + " Error message: " + str(e) 
                            send_mail("Warning", subject, errorMessage)
                            logging.warning(errorMessage)
                    else:
                        print "Directory not exist: " + archive_dir
                        subject = client + " Archive folder not exist"
                        errorMessage = client + " Archive folder: " + archive_dir + " not exits"  
                        send_mail("Warning", subject, errorMessage)
                        logging.warning(errorMessage)
                    #if archive_dir exist
                    
            #isfile
        #for        
                        
        
    # Close
    if connected:
        sftp.close()
        transport.close()
#sftp_put   

#function for connecting and downloading data
def sftp_get(client, host, port, key, user, local_dir,mask,  remote_dir, archive_dir, post_job, opt1):
    connected = True
    print 'Connecting to: ' + host + ' Port: ' + port
    logMessage = client + ' connecting to: ' + host + ' Port: ' + port
    #logging.info(logMessage)
    
    try:
        transport = paramiko.Transport((host, int(port)))
    except Exception, e:
        print "Error:",e
        subject = client + " Connection error to " + host
        errorMessage = "Connection error " + client + " cannot connect to " + host + " Error message: " + str(e) 
        send_mail("Critical", subject, errorMessage)
        logging.warning(errorMessage)
        connected = False
        
    if os.path.exists(key): 
        rsa_key = paramiko.RSAKey.from_private_key_file(key)
    else:
        subject = client + " Key file missing to " + host
        print "Key file missing !", key
        errorMessage = "Key file missing! " + client 
        send_mail("Warning", subject, errorMessage)
        logging.warning(errorMessage)
        connected = False
    
    if connected:
        try: 
            transport.connect(username = user, pkey=rsa_key)
        #except paramiko.AuthenticationException:
        except Exception, e:
            print "We had an authentication exception!",e
            subject = client + " " + str(e)
            errorMessage = "Authentication error " + client + " cannot connect to " + host + " Error message: " + str(e) 
            send_mail("Warning", subject, errorMessage)
            logging.warning(errorMessage)
            connected = False
    
    # Go!
    
    if connected:
        try:
            sftp = paramiko.SFTPClient.from_transport(transport)
            
        except Exception, e:
            print "Error:",e
            subject = client + " Connection error to " + host
            errorMessage = "Connection error " + client + " cannot connect to " + host + " Error message: " + str(e) 
            send_mail("Critical", subject, errorMessage)
            logging.critical(errorMessage)
            connected = False
            
        
    
    # Download
    if connected:
        if command == 'default':
            #get remote file list. if its not working than clear the remoteList variable
            try:
                remoteList = sftp.listdir(path = remote_dir)
            except Exception, e:
                print "Remote listing failed, error: ", e
                remoteList = ""
                subject = client + " Remote listing failed: " + str(e)
                errorMessage = "Remote listing failed: " + client + " folder: " + remote_dir + " Error message: " + str(e) 
                send_mail("Warning", subject, errorMessage)
                logging.warning(errorMessage)
                    
            for get_file in remoteList:
        
                print 'Downloading: ' + remote_dir + get_file
                remotepath = remote_dir + get_file
                localpath = local_dir + get_file
                isdir = oct(sftp.stat(remotepath).st_mode)
                print isdir[0:2]
                #check that file or directory dont download directory
                if str(isdir[0:2]) != "04":
                    try:
                        sftp.get(remotepath, localpath)
                        sftp.remove(remotepath)
                        f = open('report.txt','a')
                        text = str(time) + " " + client + ' ' + remotepath + ' downloaded \n' 
                        f.write(text)
                    
                        logMessage = client + ' Downloading ' + remotepath 
                        logging.info(logMessage)
                        #copy or move file to the archive dir
                        destination = archive_dir + get_file
                        if archive_dir:
                            if opt1:
                                    
                                shutil.copy(localpath, destination)
                            else:
                                shutil.copy(localpath, destination)
                        #move file to the final location if set
                        if opt1:
                            print "moving file", opt1
                            #win32file.MoveFile (localpath, opt1)
                            try: 
                                #shutil.move(localpath.strip(), opt1)
                                shutil.copy(localpath.strip(), opt1)
                                os.remove(localpath)
                                #subprocess.all(["move",localpath, opt1])
                                logMessage = client + ' Moving file ' + localpath + ' to ' + opt1
                                logging.info(logMessage)
                            except Exception, e:
                                print "Error:",e
                                subject = client + " " + str(e)
                                errorMessage = "File Move error " + client + " file: " + localpath + " to " + opt1  + " on "  + host + " Error message: " + str(e) 
                                send_mail("Warning", subject, errorMessage)
                                logging.warning(errorMessage)
                                
                        #running post process job if exists
                        if post_job:
                            job_path = basedir + "cmd/" + post_job
                            print post_job
                            try:
                                subprocess.call([job_path])
                                logMessage = "Job execution done " + client + " job: " + post_job 
                                logging.info(logMessage)
                            except Exception, e:
                                subject = client + " job execution error: " + str(e)
                                errorMessage = "Job execution error " + client + " job: " + post_job + " Error message: " + str(e) 
                                send_mail("Warning", subject, errorMessage)
                                logging.warning(errorMessage)
                                    
                    except Exception, e:
                        print "Error:",e
                        subject = client + " " + str(e)
                        errorMessage = "File transfer error " + client + " file: " + remotepath + " to " + localpath  + " on "  + host + " Error message: " + str(e) 
                        send_mail("Warning", subject, errorMessage)
                        logging.warning(errorMessage)
                else:
                    print remotepath + " is a directory"
            #isdir
    
    # Close
    if connected:
        sftp.close()
        transport.close()
#sftp_get

def send_mail(severity, subject, message):

    from email.MIMEMultipart import MIMEMultipart
    from email.MIMEText import MIMEText
    hostname = socket.gethostname()
    fromaddr = "filetransfer@something.com"
    toaddr = "alerts@something.com"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = severity + " from " + hostname + " " + subject

    body = message
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('10.172.10.99')
        server.ehlo()
    except Exception, e:
        print "Can't connect to mail server !"
        errorMessage = "Error in mail sending. The error message is: " + str(e)
        logging.critical(errorMessage)
    #server.starttls()
    #server.ehlo()
    #server.login("youremailusername", "password")
    text = msg.as_string()
    try:
        server.sendmail(fromaddr, toaddr, text)
        logMessage = 'Mail sent to ' + toaddr 
        logging.info(logMessage)
    except Exception, e:
        errorMessage = "Error in mail sending. The error message is: " + str(e)
        logging.critical(errorMessage)
    
    
#send_mail

#main starts here
    
import sys
import csv
import os
import datetime
from os.path import basename
import os.path
import traceback
import socket
import base64
import shutil
import glob
import smtplib
import subprocess
import logging
import paramiko
import getpass
import zipfile
import zlib

command = "default"

#base configuration variables

basedir = "/opt/scripts/filetransfer/"
controlfile = "clients.csv"
archive_default = "/var/sftp/archive"
gpgBinPath = "/usr/bin/gpg"

#paramiko.util.log_to_file('paramiko.log')
logging.getLogger("paramiko").setLevel(logging.WARNING)
#create timestamp and logging
now = datetime.datetime.now()
time = now.strftime("%Y/%m/%d %H:%M:%S")
logging.basicConfig(filename='filetransfer.log',level=logging.INFO,format='%(asctime)s %(levelname)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logging.info('===== Script started =====')


print str(time) + " Script started" 
#checking lockfile if exists send email and log
if not os.path.exists('lock'): 
    open('lock', 'w').close() 
else:
    print "Lock file found !"
    send_mail("Critical", "Lock file found!", "Lock file found !!!")
    logging.critical('Lock file found !')



#open and parse csv file for clients data
if os.path.isfile(controlfile):
    reader = csv.DictReader(open(controlfile), delimiter=',',dialect="excel")
#if
else:
    print "Control file not found !!!"
    send_mail("Critical", "Control file not found !", "Control file not found !!!")
    logging.critical('Control file not found !')
    exit (1)
 
for row in reader:

    
    client = (row["client"])
    active = (row["active"])
    host = (row["host"])
    port = (row["port"])
    key = basedir + "keys/" + (row["key"])
    zip = (row["zip"])
    sign = (row["sign"])
    armor = (row["armor"])
    gpg_key = (row["gpg_key"])
    user = (row["user"])
    local_dir = (row["local_dir"])
    mask = (row["mask"])
    remote_dir = (row["remote_dir"])
    archive_dir = (row["archive_dir"])
    action = (row["action"])
#   command = (row["method"])   
    post_job = (row["post_job"])
    opt1 = (row["opt1"])
    alert = (row["alert"])
    fileCount = (row["files"])
    
    if not mask:
        mask = "*"
    #if
    if not archive_dir:
        archive_dir = archive_default
    
    if not local_dir.endswith('/'):
        local_dir = local_dir + "/"

    if not remote_dir.endswith('/'):
        remote_dir = remote_dir + "/"
        
    if archive_dir:
        if not archive_dir.endswith('/'):
            archive_dir = archive_dir + "/"
    
    localdir = local_dir + mask

    
    
    #main processing if job is active
    if active == "yes":
        print "Processing: ", client
        if action == "put":
            if os.path.isdir(local_dir):
                if glob.glob(localdir):
                    print "start put"
                    #start sftp_put function
                    sftp_put(client, host, port, key, zip, gpg_key,sign,armor, user, local_dir, mask, remote_dir, archive_dir)
                    
                else:
                    print "empty"                   
            
            else:
                print "folder missing!"
                send_mail("Warning", "Folder Missing", "Folder missing")
                logging.warning('%s Folder missing !', client)
        else:
            print 'start get'
            sftp_get(client, host, port, key, user, local_dir,mask,  remote_dir, archive_dir, post_job, opt1)
        
        #check for the result files for any transfer until alert
        if alert:
            fileResult = 0
            if os.path.exists('report.txt'):
                reportAlert = True
                for line in open("report.txt"):
                
                    if client in line:
                        fileResult = fileResult + 1
                        
                if fileResult >= int(fileCount):        
                    reportAlert = False
                
                if reportAlert:
                    
                    alertTime = now.replace(hour=int(alert), minute=0, second=0, microsecond=0)             
                    if now > alertTime:
                        f = open('report.txt','a')
                        text = str(time) + ' ' + client + ' alarm send no files until ' + str(alert) + '\n'
                        f.write(text)
                        f.close()
                        print "ALERT!!!"
                        subject = client + " Time Alert"
                        errorMessage = "Number of files (" + str(fileResult) + ")" + " less than needed (" + fileCount + ")" + " on client " + client + " until " + str(alert)
                        print errorMessage
                        send_mail("Warning", subject, errorMessage)
                        logging.warning('%s Time Alert', client)
            
            else:
                open('report.txt', 'w').close()
        #if

#for
#remove lock file
os.remove('lock')
logging.info('===== Script stopped =====')
print str(time) + " Script stopped" 
