def writepsd(f, f_src, psdformat, verbose=-1):
	class PLInfo(object):
		pass
	pl_info = PLInfo()
	
	pl_info.total_image_length = 0
	pl_info.exlen = 0
	
	def mark_setion_pos_u32(_name):
		#ptrof_ImageResourcesSection = f.tell()
		t = f.tell()
		writeUInt(f, 0)
		pl_info.__dict__['ptrof' + _name] = t
		pl_info.__dict__['lenof' + _name] = 0
		
	def write_length_u32(_name, _len, jump=False):
		if jump:
			ptr  = pl_info.__dict__['ptrof' + _name]
			_temp = f.tell()
			f.seek(ptr, os.SEEK_SET)
			if _len is None:
				_len = pl_info.__dict__['lenof' + _name]
			writeUInt(f, _len)
			f.seek(_temp, os.SEEK_SET)
			debug(verbose, "{0:s} postition: {1:d} bytes".format(_name, ptr+4))
		else:
			writeUInt(f, _len)
		info(verbose, "{0:s} length: {1:d} bytes".format(_name, _len))
		
	def write_pascal_string(string, _padding):
		plen = len(string)
		if plen > 255:
			raise
		
		plen += 1
		if plen % _padding != 0:
			more = (_padding-plen % _padding)
		else:
			more = 0
		plen -= 1
		
		writeUByte(f, plen)
		f.write(string)
		f.write('\0'*more)
		
		# 開頭的 1 byte
		plen += more + 1
		
		return plen
		
	def writeExtra(obj, attr):
		if attr in obj:
			elen = len(obj[attr])
			data = obj[attr]
		else:
			elen = 0
			data = ""
		writeUInt(f, elen)
		f.write(data)
		return elen + 4
		
	def write8BIMList(obj, alignment=0, silentpadded=True, useId=False, hasName=False):
		
		totallength = 0
		for part in obj:
			
			f.write("8BIM")
			if useId:
				id = part['Id']
				key = str(id)
				writeUShort(f, id)
				keylen = 2
			else:
				key = part['Key']
				f.write(key)
				keylen = 4
			
			if hasName:
				# Pstring
				pstrlen = write_pascal_string(part['Name'], 2)
			else:
				pstrlen = 0
				
			data = part['_getter'](part, f_src)
			datalen = len(data)
			
			# padding to even or others
			more = 0
			if alignment:
				if datalen % alignment != 0:
					more = alignment - (datalen % alignment)
					
					if not silentpadded:
						datalen += more
						more = 0
			
			writeUInt(f, datalen)
			f.write(data)
			f.write('\0'*more)
			
			# 偷偷加在 skip 裡面, 而不直接加在 datalen
			if silentpadded:
				datalen += more
			
			partlength = 4 + keylen + pstrlen + 4 + datalen
			totallength += partlength
			
			detail(verbose, '   8BIM Part %s, %s, %d, %d' % ("8BIM", key, datalen-more, more))
		return totallength
		
	def check_exlen(_name, _add):
		pl_info.exlen += _add
		if f.tell() != pl_info.exlen:
			raise Exception(f.tell(), pl_info.exlen)
		print_ex(verbose, "{0:s}: {1:d}, {2:d}".format(_name, pl_info.exlen, _add))
	
	# -------------------------
	#### File Header Section ##
	# -------------------------
	
	Basic = psdformat['Basic']
	f.write(Basic['Sign'])
	writeUShort(f, 1)
	f.write("\0"*6)
	writeUShort(f, Basic['ChannelCounts'])
	writeUInt(f, Basic['Height'])
	writeUInt(f, Basic['Width'])
	writeUShort(f, Basic['BitsPerChannel'])
	writeUShort(f, Basic['ColorMode'])
	
	check_exlen("FileHeaderSection", 26)
	
	# -----------------------------
	#### Color Mode Data Section ##
	# -----------------------------
	
	debug(verbose, "ColorModeDataSection postition: {0:d} bytes".format(f.tell()))
	
	
	if 'ColorModeData' in psdformat:
		lenofColorModeData = len(psdformat['ColorModeData'])
		write_length_u32("ColorModeDataSection", lenofColorModeData)
		#info(verbose, "ColorModeDataSection length: {0:d} bytes".format(len(psdformat['ColorModeData'])))
		writeUInt(f, len(psdformat['ColorModeData']))
		#f.write(psdformat['ColorModeData'])
	else:
		lenofColorModeData = 0
		write_length_u32("ColorModeDataSection", lenofColorModeData)
		#info(verbose, "ColorModeDataSection length: {0:d} bytes".format(0))
		#writeUInt(f, 0)
		
	check_exlen("ColorModeDataSection", lenofColorModeData + 4)
		
	# -----------------------------
	#### Image Resources Section ##
	# -----------------------------

	mark_setion_pos_u32("ImageResourcesSection")
	
	
	#lenof_ImageResourcesSection = 0
	# write8BIMList(obj, alignment=0, silentpadded=True, useId=False, hasName=False)
	pl_info.lenofImageResourcesSection += write8BIMList(
		psdformat['Resources'], alignment=2, silentpadded=False, useId=True, hasName=True)

	
	write_length_u32("ImageResourcesSection", None, jump=True)
	
	check_exlen("ImageResourcesSection", pl_info.lenofImageResourcesSection + 4)
	
	# ----------------------------------------
	#### Layer and Mask Information Section ##
	# ----------------------------------------
	
	mark_setion_pos_u32("LayerMaskInfoSection")

	# ----------------
	# -- Layer info --
	
	mark_setion_pos_u32("LayerInfo")
	pl_info.lenofLayerMaskInfoSection += 4
	pl_info.exlenLayerMaskInfoHead = 4
	
	# TODO: 這裡可能有BUG因為無法存回負數
	writeShort(f, psdformat['Layer']['LayerCounts'])
	pl_info.lenofLayerInfo += 2
	pl_info.exlenLayerMaskInfoHead += 2
	
	cdata_ptrs = []
	for layer in psdformat['Layer']['Layers']:
		lenof_LayerRecordHeader = 0
		writeInt(f, layer['Top'])
		writeInt(f, layer['Left'])
		writeInt(f, layer['Bottom'])
		writeInt(f, layer['Right'])
		writeUShort(f, layer['ChannelCounts'])
		
		cdata_ptrs.append([])
		for ch in layer['Channels']:
			writeShort(f, ch['Id'])
			cdata_ptr  = f.tell()
			writeUInt(f, ch['Length']+2)
			cdata_ptrs[-1].append(cdata_ptr)
			
		f.write("8BIM")
		f.write(layer['BlendMode'])
		
		writeUByte(f, layer['Opacity'])
		writeUByte(f, layer['Clipping'])
		writeUByte(f, layer['Flags'])
		# padding 1 bytes
		f.write('\0')
		
		lenof_LayerRecordHeader += 16 + 2 + 6*layer['ChannelCounts'] + 8 + 4
		
		
		mark_setion_pos_u32("ExtraLayerDataField")
		
		pl_info.lenofExtraLayerDataField += writeExtra(layer, "Mask")
		pl_info.lenofExtraLayerDataField += writeExtra(layer, "BlendingRanges")

		
		# Layer name: Pascal string, padded to a multiple of 4 bytes.
		name = layer['Name'].encode('big5')
		plen = write_pascal_string(name, 4)

		pl_info.lenofExtraLayerDataField += plen
		
		# -- Additional Layer Information --
		#remaining = dstposof_ExtraLayerDataField - f.tell()
		#debug(verbose, "    AdidtionalLayerInfo[{0:d}] length: {1:d} bytes".format(i, remaining))
		
		# write8BIMList(obj, alignment=0, silentpadded=True, useId=False, hasName=False)
		BIM_len = write8BIMList(layer['AddtionInfos'])
		pl_info.lenofExtraLayerDataField += BIM_len

		
		write_length_u32("ExtraLayerDataField", None, jump=True)
		
		pl_info.lenofLayerInfo += pl_info.lenofExtraLayerDataField + 4 + lenof_LayerRecordHeader
		pl_info.exlenLayerMaskInfoHead += pl_info.lenofExtraLayerDataField + 4 + lenof_LayerRecordHeader
		
		#layer_record_total_length = lenof_LayerRecordHeader + 4 + lenof_LayerMask + 4 + lenof_LayerBlendingRangesData + 4 + pstrlen + tlen
		#pl_info.exlenLayerMaskInfoHead += layer_record_total_length
		
	check_exlen("LayerMaskInfoHead", pl_info.exlenLayerMaskInfoHead + 4)
	
	# -- Channel Image Data --
	
	debug(verbose, "  ChannelImageData")
	pl_info.exlenChannelImageData = 0
	count = 0
	skipcount = 0
	for j in range(len(psdformat['Layer']['Layers'])):
		layer = psdformat['Layer']['Layers'][j]
		for k in range(len(layer['Channels'])):
			# 不知道為什麼要+2才是正確的
			datalen = layer['Channels'][k]['Length'] + 2
			
			if datalen <= 2:
				skipcount += 1
				writeShort(f, 0)
				pl_info.lenofLayerInfo += 2
				pl_info.exlenChannelImageData += 2
				continue
			count += 1
			compression = layer['Channels'][k]['Compression']
			writeUShort(f, compression)
			t = f.tell()
			f_src.seek(layer['Channels'][k]['PosInFile'], os.SEEK_SET)
			data = f_src.read(datalen - 2)
			
			#zlib.compress(packed, 6)
			# 嘗試使用zlib 和其他的壓縮法
			want_compression = compression
			width = layer['Right'] - layer['Left']
			height = layer['Bottom'] - layer['Top']
			cdata = DecodeChannelImageData(data, compression, width, height)
			
			#print(width, height, len(cdata))
			edata = EncodeChannelImageData(cdata, want_compression, width, height)
			
			f.seek(-2, os.SEEK_CUR)
			compression = want_compression
			writeUShort(f, compression)
			f.write(edata)
			_temp = f.tell()
			f.seek(cdata_ptrs[j][k], os.SEEK_SET)
			writeUInt(f, len(edata)+2)
			f.seek(_temp, os.SEEK_SET)
			pl_info.lenofLayerInfo += len(edata) + 2
			pl_info.exlenChannelImageData += len(edata) + 2
			
			debug(verbose, "    ch_data: %5d %5d %5d %7d" % (j, k, compression, t))
			
			
		#read_layer(f, psdformat['layers'][j])
	
			
	detail(verbose, "  ChannelImageData: {0:d} records, {1:d} skips".format(count, skipcount))
	
	
	# lenof_LayersInfo 好像需要對齊 2 bytes
	# 完全搞不清楚對齊的機制是什麼
	padding = 0
	"""
	if f.tell() % 2 == 1:
	#if pl_info.lenofLayerInfo % 2 == 1:
		#pl_info.lenofLayerInfo += 1
		padding = 1
		f.write('\0')
	"""
	
	pl_info.lenofLayerMaskInfoSection += pl_info.lenofLayerInfo
	write_length_u32("LayerInfo", None, jump=True)
	info(verbose, "  LayerInfo layercounts: {0:d}".format(psdformat['Layer']['LayerCounts']))
	
	check_exlen("ChannelImageData", pl_info.exlenChannelImageData + padding)
	
	# ----------------------------
	# -- Global layer mask info --
	
	pl_info.exlenLayerMaskInfoTail = 0
	ptrof_GlobalLayerMaskInfoSection = f.tell()
	lenof_GlobalLayerMaskInfoSection = writeExtra(psdformat['Layer'], "GlobalLayerInfo")
	pl_info.lenofLayerMaskInfoSection += lenof_GlobalLayerMaskInfoSection
	pl_info.exlenLayerMaskInfoTail += lenof_GlobalLayerMaskInfoSection
	
	debug(verbose, "  GlobalLayerMaskInfoSection postition: {0:d} bytes".format(ptrof_GlobalLayerMaskInfoSection+4))
	info(verbose, "  GlobalLayerMaskInfoSection length: {0:d} bytes".format(lenof_GlobalLayerMaskInfoSection-4))
	

	# ----------------------------------
	# -- Additional Layer Information --
	
	#f.write('\0' * psdformat['padding'])
	
	debug(verbose, "  AdditionalLayerInformation postition: {0:d} bytes".format(f.tell()))

	# write8BIMList(obj, alignment=0, silentpadded=True, useId=False, hasName=False)
	BIM_len = write8BIMList(psdformat['Layer']['GlobalAdditionalLayerInfos'], alignment=4)
	pl_info.lenofLayerMaskInfoSection += BIM_len
	
	
	write_length_u32("LayerMaskInfoSection", None, jump=True)
	pl_info.exlenLayerMaskInfoTail += BIM_len
	check_exlen("LayerMaskInfoTail", pl_info.exlenLayerMaskInfoTail)
	
	# ------------------------
	#### Image Data Section ##
	# ------------------------
	debug(verbose, "ImageDataSection postition: {0:d} bytes".format(f.tell()))

	compression = psdformat['Image']['Compression']
	debug(verbose, "ImageDataSection compression: {0:d}".format(compression))
	channelcounts = psdformat['Basic']['ChannelCounts']
	width = psdformat['Basic']['Width']
	height = psdformat['Basic']['Height']
	want_compression = compression
	writeUShort(f, want_compression)
	ptr = psdformat['Image']['PosInFile']
	f_src.seek(ptr, os.SEEK_SET)
	
	cdata = DecodeFinalImageData(f_src.read(), compression, channelcounts, width, height)
	
	
	data = EncodeFinalImageData(cdata, want_compression, channelcounts, width, height)
	#print(len(data))
	f.write(data)
	pl_info.total_image_length += len(data) + 2
	
	
	info(verbose, "All Non-image Section length: {0:d}".format(f.tell()-pl_info.total_image_length))
	check_exlen("ImageDataSection", len(data) + 2)
	
	#read_final(f, psdformat)
	
	return