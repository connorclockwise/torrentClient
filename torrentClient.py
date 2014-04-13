#!/usr/bin/python

import bencode
import hashlib
import socket
import sys
import threading
import urllib
import urllib2


def main(args):

	if len(args) != 3:
		sys.exit("\nInvalid syntax, please use the arguments 'arg1: torrent file path, arg2: finished file path")

	metaDataPath = args[1]
	metaDataList = bencode.bdecode(open(metaDataPath, 'rb').read())

	hashed_info = hashMetaData(metaDataList)
	peer_id = "abcdefghijklmonpqrst"
	peerList = getPeerList(metaDataList, hashed_info, peer_id)
	# print peerList
	print "Peer 1: " + peerList[0][0]

	handshake = chr(19)+"BitTorrent protocol"+chr(0)*8+hashed_info+peer_id
	print handshake


	trackerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	trackerSocket.connect((peerList[0][0],int(peerList[0][1])))
	trackerSocket.send(handshake)
	print trackerSocket.recv(4096)
	# while 1:
	# 	connectionSocket, addr = serverSocket.accept()
	# 	print trackerSocket.recv(4096)
	# 	sentence = connectionSocket.recv(1024)
	# 	print sentence

	# getRequest = urllib.quote(getRequest)
	# print getRequest


	# serverPort = 6881
	# serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# serverSocket.bind(("",serverPort))
	# serverSocket.listen(20)
	
	# 

	# addrInfo = socket.getaddrinfo(torrentTrackerHostName, 80, 0, 0, socket.SOL_TCP)
	# ipAddr = addrInfo[0][4][0]
	# port = addrInfo[0][4][1]
	# # print port
	# # print ipAddr

	# # print torrentTrackerHostName
	# trackerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
	# trackerSocket.connect((torrentTrackerHostName, port))
	# trackerSocket.send(getRequest)
	# print trackerSocket.recv(4096)
	# while 1:
	# 	connectionSocket, addr = serverSocket.accept()
	# 	print trackerSocket.recv(4096)
	# 	sentence = connectionSocket.recv(1024)
	# 	print sentence
		

		# capitalizedSentence = sentence.upper()
		# connectionSocket.send(capitalizedSentence)
	# connectionSocket.close()
	# print trackerSocket.recv(4096)

	# trackerSocket.close()

def getPeerList(metaDataList, hashed_info, peer_id):

	torrentTrackerUrl = metaDataList["announce"]
	slash = torrentTrackerUrl.find("/")
	torrentTrackerHostName = torrentTrackerUrl[slash + 2:]
	slash2 = torrentTrackerHostName.find("/")
	torrentTrackerHostName = torrentTrackerHostName[:slash2]
	colon = torrentTrackerHostName.find(":")
	torrentTrackerHostName = torrentTrackerHostName[:colon]
	# print torrentTrackerUrl
	# print torrentTrackerHostName

	

	hashed_info_urlSafe = urllib.quote(hashed_info)
	port = "6881"
	uploaded = 0
	downloaded = 0 
	left = metaDataList["info"]["length"]
	compact = 0
	no_peer_id = 0
	event = "started"

	# print(str(to"rrentTrackerHostName))
	# print decodedDict["announce-list"]

	getRequest = ( torrentTrackerUrl +
	"?info_hash=" + hashed_info_urlSafe  +
	"&peer_id=" + peer_id  +
	"&port=" + port +
	"&uploaded=" + str(uploaded)  +
	"&downloaded=" + str(downloaded)  +
	"&left=" + str(left) +
	"&compact=" + str(1) +
	"&no_peer_id=0" +
	"&event=started")

	response = urllib2.urlopen(getRequest)
	bencodedResponse = response.read()
	decodedResponse = bencode.bdecode(bencodedResponse)
	peerListString = decodedResponse["peers"]
	peerList = []

	for i in range(0, len(peerListString), 6):
		ipAddress = (str(ord(peerListString[i:i+1])) + "."
					+ str(ord(peerListString[i+1:i+2])) + "."
					+ str(ord(peerListString[i+2:i+3])) + "."
					+ str(ord(peerListString[i+3:i+4])))
		portNumber = str((ord(peerListString[i+4:i+5]) << 8) |  ord(peerListString[i+5:i+6]))
		peerList.append((ipAddress,portNumber))
	
	return peerList

def hashMetaData(metaDataList):
	sha1 = hashlib.sha1()
	bencodedInfo = bencode.bencode(metaDataList["info"])
	sha1.update(bencodedInfo)
	hashed_info = sha1.digest()
	return hashed_info

main(sys.argv)
