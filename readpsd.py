import logging
import os
from byte import *
from layer import *
from descriptor import *

logging.basicConfig(level=logging.DEBUG)



def detail(verbose, string):
    if verbose:
        logging.debug("[DETAIL]" + string)

        

class PtrLength:
    def __init__(self, pl_info, name, pos, length, ptrsize=0, tab=0):
        self.pl_info = pl_info
        self.name = name
        self.srcpos = pos + ptrsize
        self.length = length
        self.dstpos = self.srcpos + self.length
        self.tab = tab
        logging.debug(" "*self.tab + "{0:s} postition: {1:d} bytes".format(name, pos))
        #logging.debug(" "*self.tab + "{0:s} length: {1:d} bytes".format(name, length))
        
    def remaining(self):
        pos = self.pl_info.file.tell()
        return self.dstpos - pos
        
    def addLength(self, length):
        self.length += length
        self.dstpos = self.srcpos + self.length
        
    def setLength(self, length):
        self.length = length
        self.dstpos = self.srcpos + self.length
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        self.pl_info.check_section_exit(self.name)
        
class PLInfo(object):
    def __init__(self, file):
        self.file = file
        
        self.total_data_length = 0
        self.total_image_length = 0
        self.total_skip_length = 0
        #self.exlen = 0
        
        self.check_points = {}
        
    def mark_section(self, name, length=None, tab=0):
        if length is not None:
            return self.mark_section_by_fixed_length(name, length, tab=tab)
        else:
            return self.mark_section_by_read_ptr(name, tab=tab)
    
    def mark_section_by_read_ptr(self, name, tab=0):
        pos = self.file.tell()
        length = readUInt(self.file)
        self.check_points[name] = PtrLength(self, name, pos=pos, length=length, ptrsize=4)
        return self.check_points[name]
        
    def mark_section_by_fixed_length(self, name, length, tab=0):
        pos = self.file.tell()
        self.check_points[name] = PtrLength(self, name, pos=pos, length=length, ptrsize=0)
        return self.check_points[name]
        
    
    def check_section_exit(self, name):
        pos = self.file.tell()
        
        if name not in self.check_points:
            raise Exception(name, "have not been mark")
        
        tab = self.check_points[name].tab
        
        if pos < self.check_points[name].dstpos:
            rem = self.check_points[name].dstpos - pos
            logging.warning(" "*tab + "{0:s} Remind: {1:d} bytes".format(name, rem))
            remdata = self.file.read(rem)
            logging.debug([remdata[:min(len(remdata), 8)]])
            self.total_skip_length += rem
            
        elif pos > self.check_points[name].dstpos:
            overhead = pos - self.check_points[name].dstpos
            logging.error(" "*tab + "{0:s} Overhead: {1:d} bytes".format(name, overhead))
            raise Exception(name, "overhead", overhead)
            
            
# 如果不指定 remaining 的話則持續搜尋到不是8BIM開頭為止
# 如果 direct_read=False 則跳過資料內容不直接讀取
# alignment 用來計算需要多少 padding, alignment=0 則不產生 padding
# 如果 silentpadded=True 則 padding 是不算在 datalen 之中的
#   而是在資料後面默默的補上'\0'
def read8BIMList(f, remaining=None, alignment=0, direct_read=True, silentpadded=True, useId=False, hasName=False, verbose=False):
    
    objects = []
    totallength = 0
    
    while((remaining!=None and remaining > 0) or (remaining==None)):
        
        # read sign
        sign = f.read(4)
        if sign != b"8BIM":
            if remaining != None:
                raise Exception(remaining, sign)
            else:
                logging.debug("  seek at: %s" % (sign))
                f.seek(-4, os.SEEK_CUR)
                break
        
        # read Key or Id
        if useId:
            key = readUShort(f)
            keylen = 2
        else:
            key = f.read(4)
            keylen = 4
        
        # read Pascal String
        pstrlen = 0
        if hasName:
            pstrlen, pstring = read_pascal_string(f, 2)
            name = pstring
        
        datalen = readUInt(f)
        # padding to even or others
        more = 0
        if alignment:
            if datalen % alignment != 0:
                more = alignment - (datalen % alignment)
                if not silentpadded:
                    datalen += more
                    more = 0
        
        BIMobj = {}
        BIMobj['PosInFile'] = f.tell()
        BIMobj['Length'] = datalen
        def _getter():
            t = f.tell()
            f.seek(BIMobj['PosInFile'], os.SEEK_SET)
            data = f.read(BIMobj['Length'])
            f.seek(t, os.SEEK_SET)
            return data
        
        if useId and hasName:
            objects.append(Resource(sign, key, name, data_getter=_getter, direct=direct_read))
        else:
            objects.append(Descriptor(sign, key, data_getter=_getter, direct=direct_read))
        
        f.seek(datalen, os.SEEK_CUR)
        f.seek(more, os.SEEK_CUR)
        
        partlen = 4 + keylen + pstrlen + 4 + datalen + more
        if remaining != None:
            remaining -= partlen
        totallength += partlen 
        detail(verbose, '   8BIM Part %s, %s, %d, %d' % ("8BIM", key, datalen, more))
        
    return totallength, objects
        
def readpsd(f, verbose=False, encoding='big5'):
    
    # pl_info 用來紀錄需要讀取檔案長度
    pl_info = PLInfo(f)
        
        
    psdformat = {}
    psdformat['Basic'] = {}
    
    # -------------------------
    #### File Header Section ##
    # -------------------------

    with pl_info.mark_section("FileHeaderSection", 26) as ptr:
        # Signature: always equal to '8BPS'
        sign = readString(f, 4)
        if sign != "8BPS":
            err_string = "Signature is not '8BPS', is {0}".format(sign)
            logging.error(err_string)
            raise Exception(err_string)
        
        psdformat['Basic']['Sign'] = sign
        # Version, always equal to 1 (**PSB** version is 2.)
        ver = readUShort(f)
        if ver != 1:
            err_string = "Version is not 1, is {0}".format(ver)
            logging.error(verbose, err_string)
            raise Exception(err_string) 
        # Reserved
        f.read(6)

        psdformat['Basic']['ChannelCounts'] = readUShort(f)
        psdformat['Basic']['Height'] = readUInt(f)
        psdformat['Basic']['Width'] = readUInt(f)
        psdformat['Basic']['BitsPerChannel'] = readUShort(f)
        psdformat['Basic']['ColorMode'] = readUShort(f)
        
    
    # -----------------------------
    #### Color Mode Data Section ##
    # -----------------------------
    with pl_info.mark_section("ColorModeDataSection") as ptr:
        if ptr.length != 0:
            psdformat['ColorModeData'] = f.read(ptr.length)
            
    
    # -----------------------------
    #### Image Resources Section ##
    # -----------------------------
    
    
    with pl_info.mark_section("ImageResourcesSection") as ptr:
        remaining = ptr.remaining()
        tlen, psdformat['Resources'] = read8BIMList(f, remaining, alignment=2, direct_read=True, silentpadded=False, useId=True, hasName=True, verbose=verbose)
        #logging.info("ImageResourcesSection: {0:d} records".format(len(psdformat['Resources'])))
        

    
    # ----------------------------------------
    #### Layer and Mask Information Section ##
    # ----------------------------------------
    
    
    #read_length_u32("LayerMaskInfoSection")
    
    with pl_info.mark_section("LayerMaskInfoSection") as LayerMaskInfoSection_ptr:
        # 0. legnth
        # 1. Layer info
        # 2. Global layer mask info
        # 3. (Global) Additional Layer Information
        
        # ----------------
        # -- Layer Info --
        with pl_info.mark_section("LayerInfo") as LayerInfo_ptr:
            # 0. legnth
            # 1. Layer count
            # 2. Layer records
            # 3. Channel image data
            
            psdformat['Layer'] = {}
            psdformat['Layer']['Layers'] = []
            psdformat['Layer']['LayerCounts'] = readShort(f)
            
            layercounts = psdformat['Layer']['LayerCounts']
            logging.info("  LayerInfo layercounts: {}".format(layercounts))
            
            # 負數好像另有用途
            # 請參見 adobe 手冊
            if layercounts < 0:
                layercounts = -layercounts
                
            
            # -- Layer records --
            for i in range(layercounts):
                # adobe docs 沒有定義 LayerRecord 的長度
                LayerRecord_ptr = pl_info.mark_section("LayerRecord{}".format(i), 0)
                
                # adobe docs 沒有 LayerRecordHeader 這個名詞
                LayerRecordHeader_ptr = pl_info.mark_section("LayerRecordHeader{}".format(i), 0)
                
                layer = {}
                layer['Top'] = readInt(f)
                layer['Left'] = readInt(f)
                layer['Bottom'] = readInt(f)
                layer['Right'] = readInt(f)
                layer['ChannelCounts'] = readUShort(f)
                layer['Channels'] = []
                for j in range(layer['ChannelCounts']):
                    cid = readShort(f)
                    datalen = readUInt(f)
                    layer['Channels'].append({"Id":cid, "Length":datalen})
                
                if readString(f, 4) != "8BIM":
                    raise
                layer['BlendMode'] = readString(f, 4)
                layer['Opacity'] = readUByte(f)
                layer['Clipping'] = readUByte(f)
                layer['Flags'] = readUByte(f)
                f.read(1)
                
                # 事後追加長度
                LayerRecordHeader_ptr.addLength( 16 + 2 + 6*layer['ChannelCounts'] + 8 + 4)
                LayerRecordHeader_ptr.__exit__(None, None, None)
                LayerRecord_ptr.addLength( LayerRecordHeader_ptr.length)
                
                logging.debug("    Layer[{0:d}]: {1:d} {2:s}".format(i, layer['ChannelCounts'], layer['BlendMode']))
                
                with pl_info.mark_section("ExtraLayerDataField{}".format(i)) as ExtraLayerDataField_ptr:
                    
                    with pl_info.mark_section("LayerMask{}".format(i)) as ptr:
                        data = f.read(ptr.length)
                        layer['Mask'] = data
                        
                    with pl_info.mark_section("LayerBlendingRangesData{}".format(i)) as ptr:
                        data = f.read(ptr.length)
                        layer['BlendingRanges'] = data
                    
                    # Layer name: Pascal string, padded to a multiple of 4 bytes.
                    pstrlen, pstring = read_pascal_string(f, 4)
                    layer['Name'] = pstring
                    
                    logging.debug("    LayerName[{0:d}] length: {1:d} bytes".format(i, pstrlen))
                    
                    # -- Additional Layer Information --
                    remaining = ExtraLayerDataField_ptr.remaining()
                    #read8BIMList(remaining=None, alignment=0, direct_read=True, silentpadded=True, useId=False, hasName=False)
                    tlen, layer['AddtionInfos'] = read8BIMList(f, remaining, verbose=verbose)
                
                    logging.debug("    AdidtionalLayerInfo[{0:d}] length: {1:d} bytes".format(i, tlen))
                    detail(verbose, "    AdidtionalLayerInfo[{0:d}]: {1:d} records".format(i, len(layer['AddtionInfos'])))
                    
                    psdformat['Layer']['Layers'].append(layer)
                    
                    # 如果還有剩餘的未知資料就要用這個方法
                    #check_section_end("ExtraLayerDataField", 4)
                
                layer['Name'] = layer['Name'].decode(encoding)
                layer['NameEncoding'] = encoding
                
                LayerRecord_ptr.addLength( ExtraLayerDataField_ptr.length + 4) # TODO: ptr size
                LayerRecord_ptr.__exit__(None, None, None)
                
                #logging.debug("Layer[{0:d}] total length: {1:d}".format(i, layer_record_total_length))
                
                detail(verbose, "    Layer[{0:d}]: {1:s}".format(i, layer['Name']))
                detail(verbose, "-----------------")
                
            
            #logging.info("  LayerInfo: {0:d} records".format(layercounts))
            
            
            # -- Channel Image Data --
            
            ChannelImageData_ptr = pl_info.mark_section("ChannelImageData", 0)
            count = 0
            skipcount = 0
            for j in range(len(psdformat['Layer']['Layers'])):
                layer = psdformat['Layer']['Layers'][j]
                for k in range(len(layer['Channels'])):
                    datalen = layer['Channels'][k]['Length']
                    if datalen <= 2:
                        # 空白的圖層, 通常佔用 2btye
                        skipcount += 1
                        layer['Channels'][k]['PosInFile'] = 0
                        layer['Channels'][k]['Length'] = datalen - 2
                        f.read(2)
                        ChannelImageData_ptr.addLength(2)
                        continue
                    count += 1
                    compression = readUShort(f)
                    ChannelImageData_ptr.addLength(2)
                    
                    pos = f.tell()
                    layer['Channels'][k]['Compression'] = compression
                    layer['Channels'][k]['PosInFile'] = pos
                    # 不知道為什麼要-2才是正確的, 有可能是包含 compression 的長度
                    datalen -= 2
                    layer['Channels'][k]['Length'] = datalen
                    f.seek(datalen, os.SEEK_CUR)
                    ChannelImageData_ptr.addLength(datalen)
                    
                    #detail(verbose, "    ch_data: %5d %5d %5d %7d" % (j, k, compression, pos))
                    
                    
            detail(verbose, "  ChannelImageData: {0:d} records, {1:d} skips".format(count, skipcount))
            
            
            
            # 我猜這裡應該要 aligament 2 bytes, 也有可能是 4 bytes
            '''
            padding = 0
            #print(f.tell())
            if f.tell() % 4 != 0:
                #pl_info.lenofLayerInfo += 1
                padding = 4 - (f.tell() % 4)
                f.read(padding)   
            #print(f.tell())
            '''
            
            # exit LayerInfo
        
    
        # ----------------------------
        # -- Global layer mask info --
        
        
        with pl_info.mark_section("GlobalLayerMaskInfoSection") as GlobalLayerMaskInfoSection_ptr:
            # 這一節應該不會太長
            # 如果太長一定是這一節被省略了
            # 導致讀取到了 Image Data Section 的前面4byte 00 01 xx xx
            # 也可能讀到 Additional Layer Information 的 "8BIM"
            if GlobalLayerMaskInfoSection_ptr.length < 65536:
                if GlobalLayerMaskInfoSection_ptr.length != 0:
                    data = f.read(GlobalLayerMaskInfoSection_ptr.length)
                    psdformat['Layer']['GlobalLayerInfo'] = data
                #pl_info.exlenLayerMaskInfoTail += pl_info.lenofGlobalLayerMaskInfoSection
            else:
                GlobalLayerMaskInfoSection_ptr.setLength(-4)
                logging.warning("  !Special Skip GlobalLayerMaskInfoSection" )
                f.seek(-4, os.SEEK_CUR)
                

        # ----------------------------------
        # -- Additional Layer Information --
        
        '''
        padding = 0
        s = f.read(1)
        while(s == '\0'):
            s = f.read(1)
            padding+=1
        psdformat['padding'] = padding
        f.seek(-1, os.SEEK_CUR)
        '''

        AdditionalLayerInformation_ptr = pl_info.mark_section("AdditionalLayerInformation_ptr", 0)
        #read8BIMList(remaining=None, alignment=0, direct_read=True, silentpadded=True, useId=False, hasName=False)
        tlen, psdformat['Layer']['GlobalAdditionalLayerInfos'] = read8BIMList(
            f, None, alignment=4, direct_read=False, silentpadded=True, verbose=verbose)
        
        AdditionalLayerInformation_ptr.addLength(tlen)
        AdditionalLayerInformation_ptr.__exit__(None, None, None)
        
        # exit LayerMaskInfoSection_ptr
        
    
    # ------------------------
    #### Image Data Section ##
    # ------------------------
    
    '''
    logging.debug("ImageDataSection postition: {0:d} bytes".format(f.tell()))
    t = f.tell()
    f.seek(0, os.SEEK_END)
    dstposImageDataSection = f.tell()
    logging.debug("FileTell postition: {0:d} bytes".format(dstposImageDataSection))
    f.seek(t, os.SEEK_SET)
    lenofImageDataSection = dstposImageDataSection - f.tell()
    logging.info("ImageDataSection length: {0:d} bytes".format(lenofImageDataSection))
    '''
    
    
    ImageDataSection_ptr = pl_info.mark_section("ImageDataSection", 0)
    compression = readUShort(f)
    logging.debug("ImageDataSection compression: {0:d}".format(compression))
    ImageDataSection_ptr.addLength(2)
    
    psdformat["Image"] = {}
    psdformat["Image"]['Compression'] = compression
    psdformat["Image"]['PosInFile'] = f.tell()
    
    # 計算ImageDataSection長度
    #   有可能原本就是長度會剛好到到結尾, 可能不用計算長度
    chcounts = psdformat['Basic']['ChannelCounts']
    height = psdformat['Basic']['Height']
    width = psdformat['Basic']['Width']
    
    
    if compression == 0:
        ImageDataSection_ptr.addLength(chcounts*width*height)
        
    elif compression == 1:
        packbits_header = f.read(chcounts*height*2)
        bc = struct.unpack(">" + "H"*chcounts*height, packbits_header)
        # 先嘗試把所有的 bytecount 加總起來作成 sum(bc)
        f.seek(-chcounts*height*2, os.SEEK_CUR)
        ImageDataSection_ptr.addLength(sum(bc) + chcounts*height*2)
    elif compression == 2 or compression == 3:
        t = f.tell()
        f.seek(0, os.SEEK_END)
        ImageDataSection_ptr.addLength( f.tell() - t )
        f.seek(t, os.SEEK_SET)

    
    psdformat["Image"]["Length"] = ImageDataSection_ptr.length
    f.seek(ImageDataSection_ptr.length - 2, os.SEEK_CUR)
    
    ImageDataSection_ptr.__exit__(None, None, None)
    
    return psdformat
    

        
if __name__ == '__main__':
    import sys
    f = open(sys.argv[1], "rb")
    
    psdformat = readpsd(f, verbose=True)
    read_layer(SaveLayerHandler2(), f, psdformat)
    #read_final(f, psdformat)
    