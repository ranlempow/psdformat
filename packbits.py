#
# 解碼 adobe 專有格式 PackBits
#
from ctypes import cdll
from ctypes import create_string_buffer
packbits = cdll.LoadLibrary("packbits.dll")


def decodePackBits(src, decodelen=None, depth=8):
	dst = ''
	
	i = 0
	while(i < len(src)):
	#for i in range(len(src)):
		count = ord(src[i])
		if count > 128:
			count = 256 - count  # Two's Complement
			count += 1
			dst += src[i+1] * (count)
			i+=2
		elif count == 128:
			i+=1
		else:
			count += 1
			dst += src[i+1:i+count+1]
			i+=1+count
		if decodelen is not None and len(dst) >= decodelen:
			return i, dst
			
	return i, dst
	
def depredict(data, row_length, rows):
	bdata = bytearray(data)
	for y in range(rows):
		for x in range(0, row_length-1):
			b = bdata[y*row_length+x+1] + bdata[y*row_length+x]
			if b > 255: b -= 256
			bdata[y*row_length+x+1] = b
	return str(bdata)
	
def predict(data, row_length, rows):
	bdata = bytearray(data)
	for y in range(rows):
		for x in range(row_length-1, 0, -1):
			b = bdata[y*row_length+x] - bdata[y*row_length+x-1]
			if b < 0: b += 256
			bdata[y*row_length+x] = b
	return str(bdata)




def fast_decodePackBits(src, decodelen, depth=8):
	result = create_string_buffer(decodelen)
	r = packbits.MyDecodePSDPixels(len(src), src, 8, decodelen, result)
	if r == decodelen:
		return r, result.raw
	else:
		return r, result.raw[:r]
	
def fast_encodePackBits(src, width, height, depth=8):
	encodelen = int(len(src) * (132.0 / 128.0))
	result = create_string_buffer(encodelen)
	result_bytecounts = create_string_buffer(height*2)
	r = packbits.MyEncodePSDPixels2(len(src), src, 8, width, height, result_bytecounts, encodelen, result)
	if r == -1 or r == 0:
		print(r)
		raise 
	return result_bytecounts.raw + result.raw[:r]
	
def fast_predict(src, row_length, rows):
	src = create_string_buffer(src, row_length*rows)
	packbits.Predict(row_length, rows, src)
	#result = repr(src.raw)
	#result = src.raw

	return src.raw
	'''
	bdata = bytearray(pdata)
	for y in range(rows):
		for x in range(0, row_length-1):
			b = bdata[y*row_length+x+1] + bdata[y*row_length+x]
			if b > 255: b -= 256
			bdata[y*row_length+x+1] = b
	return str(bdata)
	'''
	
def fast_depredict(src, row_length, rows):
	src = create_string_buffer(src, row_length*rows)
	packbits.Depredict(row_length, rows, src)
	return src.raw
	'''
	bdata = bytearray(pdata)
	for y in range(rows):
		for x in range(row_length-1, 0, -1):
			b = bdata[y*row_length+x] - bdata[y*row_length+x-1]
			if b < 0: b += 256
			bdata[y*row_length+x] = b
	return str(bdata)
	'''

# Test PackBits Methed
if __name__ == "__main__":
    test_src = '\xFE\xAB\x02\x80\x00\x2A\xFD\xAA\x03\x80\x00\x2A\x22\xFE\xAA'
    test_result = 'ababab80002aaaaaaaaa80002a22aaaaaa'
    print(decodePackBits(test_src, 24)[1].encode('hex_codec') == test_result)
    print(fast_decodePackBits(test_src, 24)[1].encode('hex_codec') == test_result)
    print(fast_encodePackBits(test_result.decode('hex_codec'), len(test_result)/2, 1).encode('hex_codec') == '000f' + test_src.encode('hex_codec'))
