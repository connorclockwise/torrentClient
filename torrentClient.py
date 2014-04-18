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
	# fileThread = threading.Thread(name = 'File Thread', target = fileManagementThread, args = (destinationPath, pieceBytes))
	# fileThread.start()

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
	decodedTuple = decodeMessage(response, torrentData)
	print decodedTuple
	print len(decodedTuple[1])
	print torrentData.numPieces
	print repr(MessageGenerator.request(0,0,torrentData.pieceSize))
	# trackerSocket.close()

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
		return "\x00\x00\x00\x00"

	# choke: <len=0001><id=0>
	@staticmethod
	def choke():
		return "\x00\x00\x00\x01\x00"

	# unchoke: <len=0001><id=1>
	@staticmethod
	def unChoke():
		return "\x00\x00\x00\x01\x01"

	#interested: <len=0001><id=2>
	@staticmethod
	def interested():
		return "\x00\x00\x00\x01\x02"

	# not interested: <len=0001><id=3>
	@staticmethod
	def notInterested():
		return "\x00\x00\x00\x01\x03"

	# have: <len=0005><id=4><piece index>
	@staticmethod
	def have(index):
		return "\x00\x00\x00\x05\x04" + struct.pack(">I", index)

	# bitfield: <len=0001+X><id=5><bitfield>
	@staticmethod
	def bitField(bitarray):
		tempShort = 0;
		bitString = ""
		index = 0
		for bit in bitarray:
			bitOffset = index % 8
			tempShort = (int(bit) >> bitOffset) | tempShort
			if(index % 8 == 7):
				bitString = bitString + struct.pack("B", tempShort)
				tempShort = 0
			index+=1
		return bitString

	# request: <len=0013><id=6><index><begin><length>
	@staticmethod
	def request(index, begin, length):
		return ("\x00\x00\x00\x0D\x06" + 
				struct.pack(">I", index) +
				struct.pack(">I", begin) +
				struct.pack(">I", length))

	# piece: <len=0009+X><id=7><index><begin><block>
	@staticmethod
	def piece(index, begin, block):
		return (struct.pack(">I", 9 + sys.getsizeof(block) +
				"\x07" + 
				struct.pack(">I", index) +
				struct.pack(">I", begin) +
				block))
	# cancel: <len=0013><id=8><index><begin><length>
	@staticmethod
	def cancel(index, begin, length):
		return ("\x00\x00\x00\x0D\x04" + 
				struct.pack(">I", index) +
				struct.pack(">I", begin) +
				struct.pack(">I", length))
def decodeMessage(message, torrentData):
	stringResponse = repr(message)
	if (message > 1):
		# print stringResponse + "\n"

		# print len(response[:8])
		messageLength = struct.unpack(">I", message[:4])[0]
		print messageLength
		if(messageLength == 0):
			return ("keepAlive")
		else:
			
			# print repr(testmessage)
			print repr(message)
			messageId = struct.unpack(">B", message[4])[0]
			if(messageId == 0):
				return ("choke",)
			elif(messageId == 1):
				return ("unchoke",)
			elif(messageId == 2):
				return ("interested",)
			elif(messageId == 3):
				return ("notinterested",)
			elif(messageId == 4):
				pieceIndex = struct.unpack(">I", message[5:])[0]
				return ("have",pieceIndex)
			elif(messageId == 5):
				messageBody = message[5:6+messageLength]
				messageByteArray = bytearray(messageBody)
				bitarray = {}
				bitlist = [False]*torrentData.numPieces
				for index in range(0, torrentData.numPieces - 1):
					bitarray[index] = False 
				if( len(messageByteArray) != 0):
					index = 0
					for byte in messageByteArray:
						for bitIndex in range(0,8):
							bitmask = int('0b10000000', 2) >> bitIndex
							if(((byte &  bitmask) >> (7 - bitIndex)) == 1):
								bitarray[index] = True
							index+=1
					bitlist = list(bitarray.values())
				return ("bitfield", bitlist)
			# request: <len=0013><id=6><index><begin><length>	
			elif(messageId == 6):
				pieceIndex = struct.unpack(">I", message[5:9])[0]
				begin = struct.unpack(">I", message[9:13])[0]
				length = struct.unpack(">I", message[13:17])[0]
				return ("request",pieceIndex, begin, length)
			elif(messageId == 7):
				pieceIndex = struct.unpack(">I", message[5:9])[0]
				begin = struct.unpack(">I", message[9:13])[0]
				block = message[13:]
				return ("piece",pieceIndex, begin, block)
			elif(messageId == 8):
				pieceIndex = struct.unpack(">I", message[5:9])[0]
				begin = struct.unpack(">I", message[9:13])[0]
				length = struct.unpack(">I", message[13:17])[0]
				return ("cancel",pieceIndex, begin, length)


	else:
			print("bad message")


main(sys.argv)
