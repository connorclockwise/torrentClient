#!/usr/bin/python

import bencode
import hashlib
import socket
import sys
import threading
import urllib

def main(args):

	if len(args) != 3:
		sys.exit("\nInvalid syntax, please use the arguments 'arg1: source, arg2: destination")

	
	decodedDict= bencode.bdecode(open(args[1], 'rb').read())

	torrentTrackerUrl = decodedDict["announce"]
	slash = torrentTrackerUrl.find("/")
	torrentTrackerHostName = torrentTrackerUrl[slash + 2:]
	slash2 = torrentTrackerHostName.find("/")
	torrentTrackerHostName = torrentTrackerHostName[:slash2]
	colon = torrentTrackerHostName.find(":")
	torrentTrackerHostName = torrentTrackerHostName[:colon]
	print torrentTrackerUrl
	print torrentTrackerHostName



	sha1 = hashlib.sha1()
	bencodedInfo = bencode.bencode(decodedDict["info"])
	sha1.update(bencodedInfo)
	hashed_info = sha1.digest()
	info_hash = urllib.quote(hashed_info)
	# hexstring = hashed_info.encode("hex")
	# info_hash = ""
	# # print hexstring
	# for count in range(0, len(hexstring),2):
	# 	info_hash =  info_hash + "%" + hexstring[count:count+2]
	peer_id = "abcdefghijklmonpqrst"
	# peer_id = urllib.quote(peer_id)
	
	uploaded = 0
	downloaded = 0 
	left = decodedDict["info"]["length"]
	compact = 0
	no_peer_id = 0
	event = "started"

	# print(str(to"rrentTrackerHostName))
	# print decodedDict["announce-list"]

	getRequest = (
	"?info_hash=" + info_hash  +
	"&peer_id=" + peer_id  +
	"&port=6881" +
	"&uploaded=" + str(uploaded)  +
	"&downloaded=" + str(downloaded)  +
	"&left=" + str(left) +
	"&compact=" + str(1) +
	"&no_peer_id=0" +
	"&event=started HTTP/1.1 \n\r")

	# getRequest = urllib.quote(getRequest)
	print getRequest


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
	print trackerSocket.recv(4096)

	trackerSocket.close()

main(sys.argv)
