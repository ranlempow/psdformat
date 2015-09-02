import os
import struct


	
def read_pascal_string(file, padding):
	pstrlen = readUByte(file)
	pstrlen += 1
	if pstrlen % padding != 0:
		more = (padding - pstrlen % padding)
	else:
		more = 0
	pstrlen -= 1
	
	pstring = file.read(pstrlen)
	file.seek(more, os.SEEK_CUR)
	
	# 開頭的 1 byte
	pstrlen += more + 1
	return pstrlen, pstring
	

        
def read_unicode_string(file):
	unicounts = readUInt(file)
	ustring = file.read(unicounts*2)
	
	return unicounts*2+4, ustring
	
def readString(file, length):
    string = file.read(length)
    return string.decode("big5")
    
def readUByte(file):
	string = file.read(1)
	return struct.unpack(">B", string)[0]

def readUShort(file):
	string = file.read(2)
	return struct.unpack(">H", string)[0]

def readUInt(file):
	string = file.read(4)
	return struct.unpack(">I", string)[0]
	
def readULongLong(file):
	string = file.read(8)
	return struct.unpack(">Q", string)[0]
	
def readByte(file):
	string = file.read(1)
	return struct.unpack(">b", string)[0]

def readShort(file):
	string = file.read(2)
	return struct.unpack(">h", string)[0]

def readInt(file):
	string = file.read(4)
	return struct.unpack(">i", string)[0]
	
def readLongLong(file):
	string = file.read(8)
	return struct.unpack(">q", string)[0]
	
def writeUByte(file, num):
	string = struct.pack(">B", num)
	file.write(string)

def writeUShort(file, num):
	string = struct.pack(">H", num)
	file.write(string)

def writeUInt(file, num):
	string = struct.pack(">I", num)
	file.write(string)

def writeByte(file, num):
	string = struct.pack(">b", num)
	file.write(string)

def writeShort(file, num):
	string = struct.pack(">h", num)
	file.write(string)

def writeInt(file, num):
	string = struct.pack(">i", num)
	file.write(string)