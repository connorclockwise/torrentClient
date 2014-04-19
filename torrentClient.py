#!/usr/bin/python

import bencode
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
	fileThread = threading.Thread(name = 'File Thread', target = fileManagementThread, args = (destinationPath, pieceBytes, 2 ** 14))
	fileThread.start()

	torrentData = TorrentWrapper(destinationPath, torrentBytes, pieceBytes)
	pieceIndexQueue = Queue.Queue()

	hashed_info = hashMetaData(metaDataList)
	peer_id = "RS-RemiliaScarlet!!!" #This is legal apparently
	peerList = getPeerList(metaDataList, hashed_info, peer_id)

	pieceIndexQueue = []

	for index in range(0, torrentData.numPieces):
		pieceIndexQueue.append(index)

	# print pieceIndexQueue

	handShake = MessageGenerator.handShake(hashed_info, peer_id)
	keepAlive = MessageGenerator.keepAlive()
	choke = MessageGenerator.choke()

	# for peer in peerList:
	# 	t = threading.Thread(target=peerThread, args=(torrentData, pieceIndexQueue))
	# 	t.start()

	print "Peer 1: " + peerList[0][0]

	peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	peerSocket.connect((peerList[0][0],int(peerList[0][1])))
	peerSocket.send(handShake)
	peerSocket.settimeout(60.0)

	#These are enough bytes for the handshake
	recievedHandshake = peerSocket.recv(68) + "\n" 
	print "Handshake: " + recievedHandshake
	recievedPeerId =  recievedHandshake[-21:]

	am_choking = True
	am_interested = False
	peer_choking = True
	peer_interested = False

	responseBuffer = ""
	remainingResponse = 0
	responseQueue = []
	pieceList = []

	unchoke = MessageGenerator.unChoke()
	peerSocket.send(unchoke)
	interested = MessageGenerator.interested()
	peerSocket.send(interested)
	am_choking = True
	am_interested = True
	sentRequest = False
	timeout = False

	targetFile = open(destinationPath, 'w+')

	while not timeout:

		response = ""
		try:
			response = peerSocket.recv(torrentData.blockSize + 5)
		except:
			print("Socket timeout")
			timeout = True

		responseLength = -1
		if(len(response[:4]) == 4):
			responseLength = struct.unpack(">I",response[:4])[0]


		if(len(response) > 1):
			# print "Response: " + repr(response)
			# print "Predicted length: " + str(responseLength)
			# print "Actual length: " + str(len(response[4:]))
			# print "Response Buffer: " + repr(responseBuffer)
			# print "Remaining length: " + str(remainingResponse)

			if sentRequest:
				print "Receiving piece"
				WritePiece(0, 0, response)
				# decodeMessage(responseBuffer, torrentData, responseBuffer,responseQueue)
				
			else:
				if responseBuffer:
					if remainingResponse == 0:
						print "Decoding buffer"
						decodeMessage(responseBuffer, torrentData, responseBuffer,responseQueue)
						response == 0
					elif remainingResponse < len(response):
						print "Splitting buffer"
						decodeMessage(responseBuffer + response, torrentData, responseBuffer,responseQueue)
						responselength = struct.unpack(">I",responseBuffer[:4])[0]
					elif remainingResponse > len(response):
						responseBuffer += response
						responselength = remainingResponse - len(response[4:])
					elif remainingResponse == len(response):
						responseBuffer += response
						responselength = remainingResponse - len(response[4:])
				else:
					if(responseLength == len(response[4:])):
						print "Length exactly as expected"
						decodeMessage(response, torrentData, responseBuffer,responseQueue)
					elif(responseLength > len(response[4:])):
						print "Length shorter than as expected"
						responseBuffer += response
						remainingResponse = responseLength - len(response[4:])
						print remainingResponse
					elif(responseLength < len(response[4:])):
						print "Length greater than as expected"
						decodeMessage(response, torrentData, responseBuffer,responseQueue)

		while responseQueue:
			decodedResponse = responseQueue.pop()

			if(decodedResponse[0] == "choke"):
				peer_choking = True
			elif(decodedResponse[0] == "unchoke"):
				peer_choking = False
			elif(decodedResponse[0] == "have"):
				bitList[decodedResponse[1]] = True
			elif(decodedResponse[0] == "bitfield"):
				bitList = decodedResponse[1]
			elif(decodedResponse[0] == "piece"):
				print("We are receiving a piece")
				writePiece(decodedResponse[1], decodedResponse[3])

			if(decodedResponse[0] != "badmessage"):
				print decodedResponse[0]

		if not peer_choking and not sentRequest:
			print("not being choked, we can request a piece now")
			print("requesting first piece")
			print("piece size: " + str(16384))
			
			requestPiece = MessageGenerator.request(0,0,16384)
			peerSocket.send(requestPiece)
			sentRequest = True

			


		



	# response = peerSocket.recv(1024)
	# print "First response: " + repr(response)
	# decodedTuple = decodeMessage(response, torrentData)
	# print decodedTuple
	# print len(decodedTuple[1])
	# print torrentData.numPieces
	# requestFirst = MessageGenerator.unChoke()
	# peerSocket.send(requestFirst)
	# print "My First Message: " + requestFirst

	# response = peerSocket.recv(1024)
	# decodedTuple = decodeMessage(response, torrentData)
	# print "Second response: " + repr(response)

	# requestSecond = MessageGenerator.request(0,0,torrentData.pieceSize)
	# peerSocket.send(requestSecond)
	# print "My Second Message: " + requestSecond

	# response = peerSocket.recv(1024)
	# print repr(response)

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


def WritePiece(pieceNumber, blockNumber, pieceData):
	fileCommandNotEmpty.acquire()
	print "Requesting Write of Piece #", pieceNumber, " Block #", blockNumber
	fileCommandQueue.put((pieceNumber, blockNumber, pieceData))
	fileCommandNotEmpty.notify()
	fileCommandNotEmpty.release()

def ReadPiece(pieceNumber, blockNumber):
	fileCommandMutex.acquire()
	print "Requesting Read of Piece #", pieceNumber, " Block #", blockNumber
	fileCommandQueue.put((pieceNumber, blockNumber))
	fileCommandMutex.release()
	while True:
		readPiecesNotEmpty.acquire()
		while len(readPiecesQueue) <= 0:
			readPiecesNotEmpty.wait()
		readPiecesNotEmpty.release()
		readPiecesMutex.acquire()
		mapped = [(x[0], x[1]) for x in readPiecesQueue]
		if (pieceNumber, blockNumber) in mapped:
			index = mapped.index(pieceNumber)			
			piece = readPiecesQueue[index]
			del readPiecesQueue[index]
			return piece

fileCommandQueue = Queue.Queue()
readPiecesQueue = []
fileCommandMutex = threading.Lock()
readPiecesMutex = threading.Lock()
fileCommandNotEmpty = threading.Condition(fileCommandMutex)
readPiecesNotEmpty = threading.Condition(readPiecesMutex)

def fileManagementThread(destinationPath, pieceSize, blockSize):
	targetFile = open(destinationPath, 'w+')
	while True:
		fileCommandNotEmpty.acquire()
		while fileCommandQueue.qsize() <= 0:
			fileCommandNotEmpty.wait()
		command = fileCommandQueue.get()
		fileCommandNotEmpty.release()
		if len(command) > 1:
			WriteBlockToFile(targetFile, command[0], command[1], pieceSize, blockSize, command[1])
		else:
			block = ReadBlockFromFile(targetFile, command[0], command[1], pieceSize, blockSize)
			readPiecesNotEmpty.acquire()
			readPiecesQueue.append((command[0], command[1], piece))
			readPiecesNotEmpty.notify()
			readPiecesNotEmpty.release()
	
def ReadBlockFromFile(targetFile, pieceNumber, blockNumber, pieceSize, blockSize):
	targetFile.seek(pieceNumber * pieceSize + blockNumber * blockSize)
	return targetFile.read(pieceSize)

def WriteBlockToFile(targetFile, pieceNumber, blockNumber, pieceSize, blockSize, data):
	targetFile.seek(pieceNumber * pieceSize + blockNumber * blockSize)
	targetFile.write(str(data))

	# while not queue.empty():
	# 	print(str(queue.get()) + "\n")

class TorrentWrapper:
	def __init__(self, filePath, length, pieceSize):
		self.length = length
		self.pieceSize = pieceSize
		self.blockSize = 16384
		self.numPieces = length/pieceSize
		self.numBlocks = pieceSize/self.blockSize
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
		return (struct.pack("!I", 1) + 
				struct.pack("!B", 1))

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
		return (struct.pack("!I", 13) + 
				struct.pack("!B", 6) + 
				struct.pack("!I", index) +
				struct.pack("!I", begin) +
				struct.pack("!I", length))

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

def decodeMessage(message, torrentData, stringBuffer, queue):
	# stringResponse = repr(message)
	# print "Decoding message" + stringResponse
	if (len(message) > 1):
		# print stringResponse + "\n"

		# print len(response[:8])
		# print(repr(message[:4]))
		# print(len(message[:4]))
		messageLength = struct.unpack(">I", message[:4])[0]
		# print messageLength
		if(messageLength == 0):
			queue.insert(0,("keepAlive",))
		else:
			
			# print repr(testmessage)
			# print repr(message)
			messageId = struct.unpack(">B", message[4])[0]
			if(messageId == 0):
				queue.insert(0,("choke",))
			elif(messageId == 1):
				queue.insert(0,("unchoke",))
			elif(messageId == 2):
				queue.insert(0,("interested",))
			elif(messageId == 3):
				queue.insert(0,("notinterested",))
			elif(messageId == 4):
				pieceIndex = struct.unpack(">I", message[5:9])[0]
				queue.insert(0,("have",pieceIndex))
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
				queue.insert(0,("bitfield", bitlist))
			elif(messageId == 6):
				pieceIndex = struct.unpack(">I", message[5:9])[0]
				begin = struct.unpack(">I", message[9:13])[0]
				length = struct.unpack(">I", message[13:17])[0]
				queue.insert(0,("request",pieceIndex, begin, length))
			elif(messageId == 7):
				# pieceIndex = struct.unpack(">I", message[5:9])[0]
				# begin = struct.unpack(">I", message[9:13])[0]
				# block = message[13:]
				# queue.insert(0,("piece", pieceIndex, begin, block))
				print("Receiving a piece")
			elif(messageId == 8):
				pieceIndex = struct.unpack(">I", message[5:9])[0]
				begin = struct.unpack(">I", message[9:13])[0]
				length = struct.unpack(">I", message[13:17])[0]
				queue.insert(0,("cancel",pieceIndex, begin, length))
			else:
				stringbuffer = message
				return

			if(messageLength != len(message[4:])):
				# decodeMessage(message[:4+messageLength], torrentData, stringBuffer, queue)
				decodeMessage(message[4+messageLength:], torrentData, stringBuffer, queue)
	else:
			return (("badmessage",))


main(sys.argv)
