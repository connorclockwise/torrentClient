#!/usr/bin/python

import bencode
import hashlib
import Queue
import os
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
		


finished = False

def main(args):


	destinationPath = ""
	if len(args) > 3 and len(args) < 2:
		sys.exit("\nInvalid syntax, please use the arguments 'arg1: torrent file path, (optional)arg2: finished file path")
	elif len(args) == 3:
		destinationPath = args[2]

	metaDataPath = args[1]

	metaDataList = bencode.bdecode(open(metaDataPath, 'rwb').read())


	torrentBytes = int(metaDataList["info"]["length"])
	pieceBytes = int(metaDataList["info"]["piece length"])
	fileThread = threading.Thread(name = 'File Thread', target = fileManagementThread, args = (destinationPath +metaDataList["info"]["name"], pieceBytes))
	fileThread.start()

	# print "name" + metaDataList["info"]["name"]

	torrentData = TorrentWrapper(metaDataList["info"]["name"], torrentBytes, pieceBytes)
	pieceIndexQueue = Queue.Queue()

	# hashed_info = hashMetaData(metaDataList)
	hashed_info = hashData(bencode.bencode(metaDataList["info"]))
	peer_id = "RS-RemiliaScarlet!!!" #This is legal apparently
	peerList = getPeerList(metaDataList, hashed_info, peer_id)
	hashStr = metaDataList["info"]["pieces"]
	pieceHashes = {}
	for i in range(0,len(hashStr),20):
		pieceHashes[i/20] = hashStr[i:i+20]

	pieceIndexQueue = []

	for index in range(0, torrentData.numPieces):
		pieceIndexQueue.insert(0, index)
	
	handShake = MessageGenerator.handShake(hashed_info, peer_id)

	peers = 1
	for peer in peerList:
	 	t = threading.Thread(target=peerThread, args=(torrentData, peer, pieceIndexQueue, handShake, pieceHashes))
	 	t.start()
	 	peers-=1
	 	if peers == 0:
	 		break


def getPeerList(metaDataList, hashed_info, peer_id):

	# print  metaDataList["announce"]
	print  metaDataList["announce-list"]

	torrentTrackerUrl = metaDataList["announce"]
	hashed_info_urlSafe = urllib.quote(hashed_info)
	port = "6881"
	uploaded = 0
	downloaded = 0 
	left = metaDataList["info"]["length"]
	compact = 0
	no_peer_id = 0
	event = "started"

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
	response = ""
	try:
		response = urllib2.urlopen(getRequest)
	except:
		getRequest = ( metaDataList["announce-list"][2][0] +
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

def hashData(data):
	sha1 = hashlib.sha1()
	sha1.update(data)
	hashed_info = sha1.digest()
	return hashed_info
	sha1 = None



def peerThread(torrentData, peer, pieceIndexQueue, handShake, pieceHashes):

	try:
		peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		peerSocket.connect((peer[0],int(peer[1])))
		peerSocket.send(handShake)
		peerSocket.settimeout(60.0)

		#These are enough bytes for the handshake
		recievedHandshake = peerSocket.recv(68) + "\n" 
		print "Handshake: " + recievedHandshake
		if len(recievedHandshake) != 69:
			print "Worst handshake ever"
			sys.exit()
		recievedPeerId =  recievedHandshake[-21:]
	except:
		print "Dropped by peer"
		sys.exit()


	currentPiece = -1
	currentBlock = -1
	blockQueue = []

	am_choking = True
	am_interested = False
	peer_choking = True
	peer_interested = False

	responseBuffer = ""
	pieceBuffer = ""
	remainingResponse = 0
	responseQueue = []
	pieceList = []

	unchoke = MessageGenerator.unChoke()
	peerSocket.send(unchoke)
	interested = MessageGenerator.interested()
	peerSocket.send(interested)
	am_choking = True
	am_interested = True
	timeout = False
	requestSent = False

	currentPiece = pieceIndexQueue.pop()

	print "This is my current index i'm trying to get: " + str(currentPiece)
	
	if not pieceIndexQueue:
		lastPiece = True

	for blockIndex in range(0, 32):
		blockQueue.insert(0, blockIndex)

	# print blockQueue

	currentBlock = blockQueue.pop()

	while not timeout or not finished:

				

		response = ""
		try:
			response = peerSocket.recv(1024)
		except:
			print("Socket timeout")
			timeout = True

		responseLength = -1
		if(len(response[:4]) == 4):
			responseLength = struct.unpack(">I",response[:4])[0]


		if(len(response) > 1):
			
			if responseBuffer:
				if remainingResponse == 0:
					decodeMessage(responseBuffer + response, torrentData, responseBuffer,responseQueue)
					remainingResponse = 0
					responseBuffer = ""
				elif remainingResponse < len(response):
					tempbuffer = responseBuffer
					responseBuffer = ""
					decodeMessage(tempbuffer + response, torrentData, responseBuffer,responseQueue)
					if(len(responseBuffer[:4]) == 4):
						remainingResponse = struct.unpack(">I",responseBuffer[:4])[0]
					elif(len(responseBuffer[:4]) == 0):
						remainingResponse = 0
				elif remainingResponse > len(response):
					responseBuffer += response
					remainingResponse = remainingResponse - len(response)
			else:
				if(responseLength == len(response[4:])):
					decodeMessage(response, torrentData, responseBuffer,responseQueue)
				elif(responseLength > len(response[4:])):
					responseBuffer += response 
					remainingResponse = responseLength - len(response)
				elif(responseLength < len(response[4:])):
					decodeMessage(response, torrentData, responseBuffer, responseQueue)

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
				pieceBuffer += decodedResponse[3]
				requestSent = False
				if not blockQueue and pieceIndexQueue:
					pieceHash = hashData(pieceBuffer)
					print currentPiece
					print repr(pieceHashes[currentPiece])
					print repr(pieceHash)
					if pieceHashes[currentPiece] == pieceHash:
						WritePiece(decodedResponse[1], pieceBuffer)
						currentPiece = pieceIndexQueue.pop()
					else:
						print "Incorrect Hash, retrying piece"
					pieceBuffer = ""
					for blockIndex in range(0, 32):
						blockQueue.insert(0, blockIndex)
					currentBlock = blockQueue.pop()
					if not pieceIndexQueue:
						lastPiece = True
				elif blockQueue:
					currentBlock = blockQueue.pop()
				elif not blockQueue and not pieceIndex:
					global finished
					finished = True
					sys.exit()

				# WritePiece(0, 0, "butts")

			if(decodedResponse[0] != "badmessage"):
				print decodedResponse[0]

		if not peer_choking and not requestSent:
			print "Current block: " + str(currentBlock)
			requestPiece = MessageGenerator.request(currentPiece, currentBlock*16384,16384)
			peerSocket.send(requestPiece)
			requestSent = True

	if timeout:
		print "This peer gives up, relinquishing piece:" + currentPiece
		pieceIndexQueue.append(currentPiece)


def WritePiece(pieceNumber, pieceData):
	fileCommandNotEmpty.acquire()
	print "Requesting Write of Piece #", pieceNumber
	fileCommandQueue.put((pieceNumber, pieceData))
	fileCommandNotEmpty.notify()
	fileCommandNotEmpty.release()

def ReadPiece(pieceNumber):
	fileCommandMutex.acquire()
	print "Requesting Read of Piece #", pieceNumber
	fileCommandQueue.put((pieceNumber))
	fileCommandMutex.release()
	while True:
		readPiecesNotEmpty.acquire()
		while len(readPiecesQueue) <= 0:
			readPiecesNotEmpty.wait()
		readPiecesNotEmpty.release()
		readPiecesMutex.acquire()
		mapped = [x[0] for x in readPiecesQueue]
		if pieceNumber in mapped:
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
piecesDictionary = {}


def fileManagementThread(destinationPath, pieceSize):
	while True:
		if os.path.exists("myfile.dat"):
			f = file(destinationPath, "r+")
		else:
			f = file(destinationPath, "w")
		targetFile = open(destinationPath, 'r+')
		fileCommandNotEmpty.acquire()
		while fileCommandQueue.qsize() <= 0:
			fileCommandNotEmpty.wait()
		command = fileCommandQueue.get()
		fileCommandNotEmpty.release()
		if len(command) > 1:
			WritePieceToFile(targetFile, command[0], pieceSize, command[1])
		else:
			block = ReadPieceFromFile(targetFile, command[0], pieceSize)
			readPiecesNotEmpty.acquire()
			readPiecesQueue.append((command[0], piece))
			readPiecesNotEmpty.notify()
			readPiecesNotEmpty.release()
		targetFile.close()
	
def ReadPieceFromFile(targetFile, pieceNumber, pieceSize):
	print "READ", pieceNumber
	targetFile.seek(pieceNumber * pieceSize)
	return targetFile.read(pieceSize)

def WritePieceToFile(targetFile, pieceNumber, pieceSize, data):
	print "WRITE", pieceNumber
	targetFile.seek(pieceNumber * pieceSize)
	# print data
	# print "this is the data being written " + data
	targetFile.write(data)
	targetFile.flush()
	# print data > "help.txt"
	# targetFile.close()
	
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
		print "Index: " + str(index)
		print "Begin: " + str(begin)
		print "Length: " + str(length)

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
				pieceIndex = struct.unpack(">I", message[5:9])[0]
				begin = struct.unpack(">I", message[9:13])[0]
				block = message[13:]
				queue.insert(0,("piece", pieceIndex, begin, block))
				# print("Receiving a piece")
			elif(messageId == 8):
				pieceIndex = struct.unpack(">I", message[5:9])[0]
				begin = struct.unpack(">I", message[9:13])[0]
				length = struct.unpack(">I", message[13:17])[0]
				queue.insert(0,("cancel",pieceIndex, begin, length))

			if(messageLength < len(message[4:])):
				# decodeMessage(message[:4+messageLength], torrentData, stringBuffer, queue)
				decodeMessage(message[4+messageLength:], torrentData, stringBuffer, queue)
			else:
				stringbuffer = message

	else:
			return (("badmessage",))


main(sys.argv)
