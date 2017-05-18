#!/usr/bin/python

import subprocess
import os
import os.path
import json
import codecs
import time
import datetime

# curl
curl = "curl"
curlOptions = "--compressed --silent"

# URL params
messagesURL = "https://messenger.yahoo.com/archive/messages"
messageURL = "https://messenger.yahoo.com/archive/message"

messagesOutput = "msgs.json"
messageOutput = "msg.json"

# TODO: edit these IDs
wssid = ""
mailboxID = ""
cookie = "" 
start = 0
fromAddress = "someid%40yahoo.com"

# headers
acceptEncoding = "gzip, deflate, sdch, br"
acceptLanguage = "en-US,en;q=0.8,ca;q=0.6,cs;q=0.4,da;q=0.2,de;q=0.2,es;q=0.2,fr;q=0.2,hu;q=0.2,it;q=0.2,ja;q=0.2,nl;q=0.2,pt;q=0.2,ro;q=0.2,ru;q=0.2,sv;q=0.2,tr;q=0.2"
userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
contentType = "application/json"
accept = "application/json"
referer = "https://messenger.yahoo.com/archive/"
authority = "messenger.yahoo.com"

headers = "-H 'accept-encoding: %s' -H 'accept-language: %s' -H 'user-agent: %s' -H 'content-type: %s' -H 'accept: %s' -H 'referer: %s' -H 'authority: %s' -H 'cookie: %s'" % \
    (acceptEncoding, acceptLanguage, userAgent, contentType, accept, referer, authority, cookie)

messageDir = "messages"

while 1:
    print "Downloading 10 messages starting from %d" % (start)
    messagesCommand = "%s '%s?wssid=%s&mailboxId=%s&start=%d&prefix=%%2Farchive%%2F&from=%s' %s %s > %s" % \
        (curl, messagesURL, wssid, mailboxID, start, fromAddress, headers, curlOptions, messagesOutput)

    while 1:
        p = subprocess.Popen(messagesCommand, shell=True)
        os.waitpid(p.pid, 0)
        time.sleep(1)

        messagesFile = open(messagesOutput)
        line = messagesFile.readline()
        messagesFile.close()
            
        if "<!DOCTYPE html>" not in line:
            break
        else:
            print "Got HTML, retrying"

    with open(messagesOutput) as messagesFile:    
        messagesJSON = json.load(messagesFile)

        for i in range(0, 10):
            messageID = messagesJSON["messages"][i]["mid"]
            messageCommand = "%s '%s?wssid=%s&mailboxId=%s&messageIds=%s&prefix=%%2Farchive%%2F' %s %s > %s" % \
                (curl, messageURL, wssid, mailboxID, messageID, headers, curlOptions, messageOutput)
            
            while 1:
                p = subprocess.Popen(messageCommand, shell=True)
                os.waitpid(p.pid, 0)
                time.sleep(1)
            
                messageFile = open(messageOutput)
                line = messageFile.readline()
                messageFile.close()
            
                if "<!DOCTYPE html>" not in line:
                    break
                else:
                    print "Got HTML, retrying"
            
            with open(messageOutput) as messageFile:    
                messageJSON = json.load(messageFile)
            
                messageFrom = messageJSON["message"][0]["response"]["result"]["message"]["headers"]["from"][0]["email"]
                messageTo   = messageJSON["message"][0]["response"]["result"]["message"]["headers"]["to"]  [0]["email"]
            
                messagePartner = messageFrom
                if messagePartner == "" or messagePartner == "myid@yahoo.com" or messagePartner == "myotherid@yahoo.com":
                    messagePartner = messageTo
                if messagePartner == "" or messagePartner == "myid@yahoo.com" or messagePartner == "myotherid@yahoo.com":
                    messagePartner = "myid@yahoo.com"

                messagePartnerDir = "%s/%s" % (messageDir, messagePartner)
                if not os.path.exists(messagePartnerDir):
                    os.makedirs(messagePartnerDir)
            
                messageDate = messageJSON["message"][0]["response"]["result"]["message"]["headers"]["date"]
                messageDateReadable = messageJSON["message"][0]["response"]["result"]["message"]["headers"]["mimeDate"]
                messageDateFileName = datetime.datetime.utcfromtimestamp(int(messageDate)).strftime('%Y-%m-%dT%H-%M-%S')

                htmlFileName = "%s/%s.html" % (messagePartnerDir, messageDateFileName)
            
                counter = 0
                while os.path.isfile(htmlFileName):
                    htmlFileName = "%s/%s-%d.html" % (messagePartnerDir, messageDateFileName, counter)
                    counter = counter + 1
            
                print "Conversation with %s at %s" % (messagePartner, messageDateReadable)
            
                htmlFile = codecs.open(htmlFileName, "w", "utf-8")
                htmlFile.write(messageJSON["message"][0]["response"]["result"]["simpleBody"]["html"])
                htmlFile.close()

    start = start + 10