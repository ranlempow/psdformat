import logging
#import cStringIO as StringIO
import io as StringIO

class DataCarrier:
    def __init__(self, data_getter, data=None, direct=False):
        self._data_getter = data_getter
        if direct:
            self._data = self._data_getter()
        else:
            self._data = data
        
    @property
    def data(self):
        if self._data is None:
            self._data = self._data_getter()
        return self._data
        
class Resource(DataCarrier):
    def __init__(self, sign, id, name, data_getter, data=None, direct=False):
        DataCarrier.__init__(self, data_getter=data_getter, data=data, direct=direct)
        self.sign = sign
        self.id = id
        self.name = name

        
class Descriptor(DataCarrier):
    def __init__(self, sign, type, data_getter, data=None, direct=False):
        DataCarrier.__init__(self, data_getter=data_getter, data=data, direct=direct)
        self.sign = sign
        self.type = type


"""
[Linked Layer]

Key is 'lnkD' . Also keys 'lnk2' and 'lnk3' . Data is as follows:
=======================================================
The following is repeated for each linked file.
8            Length of the data to follow
4            Type ( = 'liFD' )
4            Version ( = 2 )
Variable    Pascal string. Unique ID.
Variable    Unicode string of the original file name
4            File Type
4            File Creator
8            Length of the data to follow
1            File open descriptor
Variable    Descriptor of open parameters. Only present when above is true.
Variable    Raw bytes of the file.
=======================================================
"""
""" in psdformat['Layer']['GlobalAdditionalLayerInfos'] """
class LinkedLayer(Descriptor):
    def __init__(self, desc):
        Descriptor.__init__(self, desc.sign, desc.type, None, desc.data)
        
        self.psds = {}
        
        reminding = len(self.data)
        data_f = StringIO.StringIO(self.data)
        f = data_f
        
        while(reminding > 0):
            length = readULongLong(f)
            sign = f.read(4)
            if sign != "liFD":
                err_string = "Signature is not 'liFD', is {0}".format(sign)
                logging.error(verbose, err_string)
                raise Exception(err_string)
            
            version = readUInt(f)
            if version != 2:
                raise Exception(version)
            
            exlen = 0
            
            _exlen, id = read_pascal_string(f, 1)
            print(id)
            exlen += _exlen
            
            #print(readUInt(f))
            _exlen, name = read_unicode_string(f)
            #print(name)
            print(name.decode('utf_16_be').encode('big5', 'replace'))
            exlen += _exlen
            
            f.read(8)
            
            datalen = readULongLong(f)
            hasOpenMode = readUByte(f)
            datalen -= 1
            print(datalen)
            print(hasOpenMode)
            f.read(hasOpenMode)
            datalen -= hasOpenMode
            
            #print([f.read(100)])
            #f.seek(datalen, os.SEEK_CUR)
            
            psddata = f.read(datalen)
            self.psds[id] = (name, paddata)
            
            #psd_f = cStringIO.StringIO(psddata)
            
            #psdformat = readpsd(psd_f, 5)
            #f2 = open('inner.psd', 'wb')
            #f2.write(psddata)
            #f2.close()
            
            reminding -= length + 8
            
            
'''
def ReadGAL_lnk2(f, psdformat):
    gal = None
    for _gal in psdformat['Layer']['GlobalAdditionalLayerInfos']:
        if _gal['Key'] == "lnk2":
            gal = _gal
            
    if gal is None:
        return None
        
    data = gal['_getter'](gal, f)
    reminding = len(data)
    import cStringIO
    data_f = cStringIO.StringIO(data)
    
    f = data_f
    
    while(reminding > 0):
        length = readULongLong(f)
        sign = f.read(4)
        if sign != "liFD":
            err_string = "Signature is not 'liFD', is {0}".format(sign)
            logging.error(verbose, err_string)
            raise Exception(err_string)
        
        version = readUInt(f)
        if version != 2:
            raise Exception(version)
        
        exlen = 0
        
        _exlen, id = read_pascal_string(f, 1)
        print(id)
        exlen += _exlen
        
        #print(readUInt(f))
        _exlen, name =read_unicode_string(f)
        #print(name)
        print(name.decode('utf_16_be').encode('big5', 'replace'))
        exlen += _exlen
        
        f.read(8)
        
        datalen = readULongLong(f)
        hasOpenMode = readUByte(f)
        datalen -= 1
        print(datalen)
        print(hasOpenMode)
        #print([f.read(100)])
        #f.seek(datalen, os.SEEK_CUR)
        psddata = f.read(datalen)
        psd_f = cStringIO.StringIO(psddata)
        psdformat = readpsd(psd_f, 5)
        #f2 = open('inner.psd', 'wb')
        #f2.write(psddata)
        #f2.close()
        
        reminding -= length + 8
        
        
        
        #if hasOpenMode == 1:
        #    raise Exception(f.read(1))
        #print([f.read(121095)])
        #search_sign(f, '8BPS')
        #print(f.read(6000))
        #print('??')
'''