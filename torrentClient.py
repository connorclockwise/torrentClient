#!/usr/bin/python

import bencode
import hashlib
import Queue
import socket
import sys
import threading
import urllib
import urllib2


def main(args):

	if len(args) != 3:
		sys.exit("\nInvalid syntax, please use the arguments 'arg1: torrent file path, arg2: finished file path")

	metaDataPath = args[1]
	destinationPath = args[2]

	metaDataList = bencode.bdecode(open(metaDataPath, 'rb').read())

	torrentBytes = int(metaDataList["info"]["length"])
	pieceBytes = int(metaDataList["info"]["piece length"])


	torrentData = TorrentWrapper(destinationPath, torrentBytes, pieceBytes)
	pieceIndexQueue = Queue.Queue()
	# print torrentData.numPieces
	for index in range(0, torrentData.numPieces):
		pieceIndexQueue.put(index)



	hashed_info = hashMetaData(metaDataList)
	peer_id = "SA-SolaireOfAstora!!" #This is legal apparently
	peerList = getPeerList(metaDataList, hashed_info, peer_id)

	for peer in peerList:
		t = threading.Thread(target=peerThread, args=(torrentData, pieceIndexQueue))
		t.start()

	# print "Peer 1: " + peerList[0][0]

	# #<pstrlen><pstr><reserved><info_hash><peer_id>
	# handshake = chr(19)+"BitTorrent protocol"(+chr(0)*8)+hashed_info+peer_id
	# print handshake


	# trackerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	# trackerSocket.connect((peerList[0][0],int(peerList[0][1])))
	# trackerSocket.send(handshake)
	# print trackerSocket.recv(4096)




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

def peerThread(torrentData, queue):
	while not queue.empty():
		print(str(queue.get()) + "\n")

class TorrentWrapper:
	def __init__(self, filePath, length, pieceSize):
		self.length = length
		self.pieceSize = pieceSize
		self.numPieces = length/pieceSize
		self.pieces = [0]*self.numPieces
		self.dataArray = bytearray(length)
		self.filePath = filePath


main(sys.argv)
