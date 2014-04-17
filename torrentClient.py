#!/usr/bin/python

import bencode
import binascii
import hashlib
import Queue
import socket
import sys
import struct
import threading
import urllib
import urllib2

def FindRarestPieces(peerBitLists, pieceCount):
    sortedPieces = []
    for piece in range(pieceCount):
	count = 0
	for bitList in peerBitLists:
	    if bitList[piece]:
		count += 1
	sortedPieces.append((count, piece))
    sort(sortedPieces)
    return map(lambda x: x[1], sortedList)
		



def main(args):



	if len(args) != 3:
		sys.exit("\nInvalid syntax, please use the arguments 'arg1: torrent file path, arg2: finished file path")

	metaDataPath = args[1]
	destinationPath = args[2]

	metaDataList = bencode.bdecode(open(metaDataPath, 'rwb').read())


	torrentBytes = int(metaDataList["info"]["length"])
	pieceBytes = int(metaDataList["info"]["piece length"])
	fileThread = threading.Thread(name = 'File Thread', target = fileManagementThread, args = (destinationPath, pieceBytes))
	fileThread.start()

	torrentData = TorrentWrapper(destinationPath, torrentBytes, pieceBytes)
	pieceIndexQueue = Queue.Queue()
	# print torrentData.numPieces
	# for index in range(0, torrentData.numPieces):
	# 	pieceIndexQueue.put(index)



	hashed_info = hashMetaData(metaDataList)
	peer_id = "RS-RemiliaScarlet!!!" #This is legal apparently
	peerList = getPeerList(metaDataList, hashed_info, peer_id)

	# messageGenerator = MessageGenerator()
	handShake = MessageGenerator.handShake(hashed_info, peer_id)
	keepAlive = MessageGenerator.keepAlive()
	choke = MessageGenerator.choke()
	# handShake = messageGenerator.keepAlive()
	# print 

	# for peer in peerList:
	# 	t = threading.Thread(target=peerThread, args=(torrentData, pieceIndexQueue))
	# 	t.start()

	print "Peer 1: " + peerList[0][0]

	# #<pstrlen><pstr><reserved><info_hash><peer_id>
	# handshake = chr(19)+"BitTorrent protocol"(+chr(0)*8)+hashed_info+peer_id
	# print handshake


	trackerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	trackerSocket.connect((peerList[0][0],int(peerList[0][1])))
	trackerSocket.send(handShake)
	#These are enough bytes for the handshake
	recievedHandshake = trackerSocket.recv(68) + "\n" 
	print recievedHandshake
	recievedPeerId =  recievedHandshake[-21:]
	# trackerSocket.send(keepAlive)
	# print repr(trackerSocket.recv(4096)) + "\n"
	response = trackerSocket.recv(1024)
	stringResponse = repr(response)
	print response + "\n"
	print stringResponse + "\n"
	# print len(response[:8])
	messageLength = struct.unpack(">I", response[:4])
	messageId = struct.unpack(">B", response[4])
	messageBody = response[5:]
	print messageLength
	print messageId
	print torrentData.numPieces
	messageByteArray = bytearray(messageBody)
	print repr(messageByteArray)
	print len(messageByteArray) + 1
	if( len(messageByteArray) != 1473):
		print bin(messageByteArray[0])
		bitarray = {}
		index = 0
		for byte in messageByteArray:
			for bitIndex in range(0,8):
				bitmask = int('0b10000000', 2) >> bitIndex
				# print(bin(bitmask))
				# print(bin(messageByteArray[0] &  bitmask))
				bitarray[index] = ((byte &  bitmask) >> (7 - bitIndex))
				# print(bin(((byte &  bitmask) >> (7 - bitIndex))))
				# print index
				index+=1

		print bitarray

	# print binascii.unhexlify(messageByteArray) 
	# fixedResponse = (response[1:-1] + "\n").replace("\\x","")
	# print repr(fixedResponse)
	# print struct.unpack(">l", stringResponse[:8] )
	# fixedResponse = (response[1:-1] + "\n").replace("\\x","")
	# print str(list(bytearray(fixedResponse)))
	# print repr(bytearray(fixedResponse))
	# print (bytearray(fixedResponse)[:8])
	# length = response[1:17]
	# print response.encode("unicode_internal")
	# print int(length, 16)
	# print hex.decode(length,"utf-8")
	# print length
	# print int(length, 16)
	# print repr(int.fromhex(length))
	# print repr(bytes.fromhex(response[19:21]))
	


	# def keepAlive(response):
	# 	print("Keep Alive")
	# def choke(response):
	# 	print("choke")
	# def unChoke(response):
	# 	print("unChoke")
	# def interested(response):
	# 	print("interested")
	# def notInterested():
	# 	print("nonInterested")
	# def have(response):
	# 	print("have")
	# def bitField(response):
	# 	print("bitField")
	# def request(response):
	# 	print("unchoke")
	# def piece(response):
	# 	print("unchoke")
	# def cancel(response):
	# 	print("unchoke")



	# def messageSwitch(response):

	# 	# message_id = int(response[19:21], 16)

	# 	if(int(length, 16) != 0):
	# 		return {
	# 			0:choke,
	# 			1:unChoke,
	# 			2:interested,
	# 			3:notInterested,
	# 			4:have,
	# 			5:bitField,
	# 			6:request,
	# 			7:piece,
	# 			8:cancel,
	# 		}.get(message_id, -1)
	# 		#keep-alive: <len=0000>
	# 		# choke: <len=0001><id=0>
	# 		# unchoke: <len=0001><id=1>
	# 		# interested: <len=0001><id=2>
	# 		# not interested: <len=0001><id=3>
	# 		# have: <len=0005><id=4><piece index>
	# 		# bitfield: <len=0001+X><id=5><bitfield>
	# 		# request: <len=0013><id=6><index><begin><length>
	# 		# piece: <len=0009+X><id=7><index><begin><block>
	# 		# cancel: <len=0013><id=8><index><begin><length>
			
	# 	else:
	# 		return keepAlive

	
	# messageSwitch(response)(response)

	# trackerSocket.send(choke)
	# response1 = trackerSocket.recv(4096)
 # 	print response1




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

def peerThread(torrentData, queue, peer):

    am_choking = 1
    am_interested = 0
    peer_choking = 1
    peer_interested = 0


def WritePiece(pieceNumber, pieceData):
	fileCommandMutex.acquire()
	fileCommandQueue.enqueue((pieceNumber, pieceData))
	fileCommandNotEmpty.notify()
	fileCommandMutex.release()

def ReadPiece(pieceNumber):
	fileCommandMutex.acquire()
	fileCommandQueue.enqueue((pieceNumber))
	fileCommandMutex.release()
	while True:
		readPiecesNotEmpty.acquire()
		while len(readPiecesQueue) <= 0:
			readPiecesNotEmpty.wait()
		readPiecesNotEmpty.release()
		readPiecesMutex.acquire()
		mapped = [x[1] for x in readPiecesQueue]
		if pieceNumber in mapped:
			index = mapped.index(pieceNumber)			
			piece = readPiecesQueue[index]
			del readPiecesQueue[index]
			return piece

fileCommandQueue = Queue.Queue()
readPiecesQueue = []
fileCommandMutex = threading.Lock()
readPiecesMutex = threading.Lock()
fileCommandNotEmpty = threading.Condition()
readPiecesNotEmpty = threading.Condition()

def fileManagementThread(destinationPath, pieceSize):
	targetFile = open(destinationPath, 'w+')
	while True:
		fileCommandNotEmpty.acquire()
		while fileCommandQueue.qsize() <= 0:
			fileCommandNotEmpty.wait()
		command = fileCommandQueue.pop()
		fileCommandNotEmpty.release()
		if len(command) > 1:
			WritePieceToFile(targetFile, command[0], pieceSize, command[1])
		else:
			piece = ReadPieceFromFile(targetFile, command[0], pieceSize)
			readPiecesMutex.acquire()
			readPiecesQueue.append((command[0], piece))
			readPiecesMutex.release()
	
def ReadPieceFromFile(targetFile, pieceNumber, pieceSize):
	targetFile.seek(pieceNumber * pieceSize)
	return targetFile.read(pieceSize)

def WritePieceToFile(targetFile, pieceNumber, pieceSize, data):
	targetFile.seek(pieceNumber * pieceSize)
	targetFile.write(str(data))

	# while not queue.empty():
	# 	print(str(queue.get()) + "\n")

class TorrentWrapper:
	def __init__(self, filePath, length, pieceSize):
		self.length = length
		self.pieceSize = pieceSize
		self.numPieces = length/pieceSize
		self.pieces = []
		self.filePath = filePath

class MessageGenerator:

	def __init__(self):
		pass

	# <pstrlen><pstr><reserved><info_hash><peer_id>
	@staticmethod
	def handShake(hashed_info, peer_id):
		return chr(19)+"BitTorrent protocol"+(chr(0)*8)+hashed_info+peer_id

	#message syntax:<length prefix><message ID><payload>

	#keep-alive: <len=0000>
	@staticmethod
	def keepAlive():
		return str(chr(0)*4)

	# choke: <len=0001><id=0>
	@staticmethod
	def choke():
		return str(chr(0)*3) + str(chr(1)) + str(chr(0))

	# unchoke: <len=0001><id=1>
	@staticmethod
	def unChoke():
		return str(chr(0)*3) + str(chr(1)) + str(chr(1))

	#interested: <len=0001><id=2>
	@staticmethod
	def interested():
		return str(chr(0)*3) + str(chr(1)) + str(chr(2))

	# not interested: <len=0001><id=3>
	@staticmethod
	def notInterested():
		return str(chr(0)*3) + str(chr(1)) + str(chr(3))

	# have: <len=0005><id=4><piece index>
	@staticmethod
	def have(index):
		return str(chr(0)*3) + str(chr(5)) + str(chr(4)) + str(index)

	# bitfield: <len=0001+X><id=5><bitfield>
	@staticmethod
	def bitField(bitfield):
		return str(chr(0)*3) + str(chr(1)) + str(chr(5)) + str(bitfield)

	# request: <len=0013><id=6><index><begin><length>
	@staticmethod
	def request(index, begin, length):
		return str(chr(0)*2) + str(chr(13)) + str(chr(6)) + str(index) + str(begin) + str(length)

	# piece: <len=0009+X><id=7><index><begin><block>
	@staticmethod
	def piece(index, begin, length):
		return str(chr(0)*3) + str(chr(9)) + str(chr(7)) + str(index) + str(begin) + str(length)

	# cancel: <len=0013><id=8><index><begin><length>
	@staticmethod
	def cancel(index, begin, length):
		return str(chr(0)*2) + str(chr(13)) + str(chr(8)) + str(index) + str(begin) + str(length)

	# @staticmethod
	# def decode(message):
	# 	if(message)


main(sys.argv)
