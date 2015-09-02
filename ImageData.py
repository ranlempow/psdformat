import struct
from packbits import *

"""
Compression method:

0 = Raw image data
1 = RLE compressed the image data starts with the byte counts
for all the scan lines (rows * channels), with each count stored as a two-byte value.
The RLE compressed data follows, with each scan line compressed separately.
The RLE compression is the same compression algorithm used by 
the Macintosh ROM routine PackBits , and the TIFF standard.

2 = ZIP without prediction
3 = ZIP with prediction
"""
def DecodeChannelImageData(data, compression, width, height):
	#def loadPackBitsSection(data, width, height):
	if compression == 0:
		# Raw Data
		if len(data) == width * height:
			return data
		else:
			raise
	elif compression == 1:
		# RLE compressed
		# 取得前面的 bytecount
		bc = struct.unpack(">" + "H"*height, data[0: height*2])
		# 先嘗試把所有的 bytecount 加總起來作成 sum(bc)
		sumbc = sum(bc)
		dst_size = width * height * 8 // 8
		# 取得RLE壓縮的資料
		adv, cdata = fast_decodePackBits(data[height*2: height*2+sumbc], dst_size)
	elif compression == 2:
		#  ZIP without prediction
		pdata = zlib.decompress(data)
		if len(pdata) != width * height:
			raise
		return pdata
	
	elif compression == 3:
		#  ZIP with prediction
		pdata = zlib.decompress(data)
		if len(pdata) != width * height:
			raise
		
		return fast_depredict(pdata, width, height)
		
	return cdata

def DecodeFinalImageData(data, compression, channelcounts, width, height):
	row_length = width
	rows = channelcounts * height
	
	cdatas = []
	if compression == 0:
		if len(data) != channelcounts*width*height:
			raise
		#for ch in range(channelcounts):
		#	cdatas.append(data[ch*width*height:(ch+1)*width*height])
		return data
	elif compression == 1:
		# 取得前面的 bytecount
		bc = struct.unpack(">" + "H"*(rows), data[:(rows)*2])
		# 先嘗試把所有的 bytecount 加總起來作成 sum(bc)
		sumbc = sum(bc)
		dst_size = row_length * rows * 8 // 8
		adv, cdata = fast_decodePackBits(data[rows*2: rows*2+sumbc], dst_size)
		'''
		ptr = (channelcounts)*height*2
		for ch in range(channelcounts):
			# 取得前面的 bytecount
			bc = struct.unpack(">" + "H"*height, data[ch*height*2: (ch+1)*height*2])
			# 先嘗試把所有的 bytecount 加總起來作成 sum(bc)
			sumbc = sum(bc)
			dst_size = width * height * 8 / 8
			print(dst_size)
			# 取得RLE壓縮的資料
			adv, cdata = fast_decodePackBits(data[ptr: ptr+sumbc], dst_size)
			ptr += sumbc
			cdatas.append(cdata)
		'''
		return cdata
	elif compression == 2:
		pdata = zlib.decompress(data)
		if len(pdata) != channelcounts*width*height:
			raise
		#for ch in range(channelcounts):
		#	cdatas.append(pdata[ch*width*height:(ch+1)*width*height])
		return pdata
	elif compression == 3:
		pdata = zlib.decompress(data)
		if len(pdata) != channelcounts*width*height:
			raise

		return fast_depredict(pdata, width, height)

	
	
def _EncodeImageData(cdata, compression, row_length, rows):
	if len(cdata) != row_length * rows:
		raise
	
	if compression == 0:
		# Raw Data
		return cdata
	elif compression == 1:
		# RLE compressed
		data = fast_encodePackBits(cdata, row_length, rows)
		return data
	elif compression == 2:
		# ZIP without prediction
		zlib_data = zlib.compress(cdata, 6)
		return zlib_data
	elif compression == 3:
		#  ZIP with prediction
		'''
		bdata = bytearray(cdata)
		for y in range(rows):
			for x in range(row_length-1, 0, -1):
				b = bdata[y*row_length+x] - bdata[y*row_length+x-1]
				if b < 0: b += 256
				bdata[y*row_length+x] = b
		'''
		#pdata = fast_depredict(cdata, row_length, rows)
		pdata = fast_predict(cdata, row_length, rows)
		
		zlib_data = zlib.compress(pdata, 6)
		
		return zlib_data
	
def EncodeChannelImageData(cdata, compression, width, height):
	return _EncodeImageData(cdata, compression, width, height)

def EncodeFinalImageData(cdata, compression, channelcounts, width, height):
	data = _EncodeImageData(cdata, compression, width, height*channelcounts)
	# photoshop沒辦法知道壓縮的長度是多少, 所以只好給它多讀更多的空白資料
	# 但是也不知道要多少空白資料在結尾
	if compression == 2 or compression == 3:
		#data = struct.pack(">I", len(data)) + data
		data = data + '\0' * 1024 * 512
	return data