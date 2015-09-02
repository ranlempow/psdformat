import comtypes.client

psApp = None
def launchPhotoshop():
    global psApp
    if psApp is None:
        psApp = comtypes.client.CreateObject('Photoshop.Application')
    return psApp
    
def tid(chars):
    assert len(chars) == 4
    return psApp.charIDToTypeID(chars)

def sid(string):
    return psApp.stringIDToTypeID(string)

C = tid
S = sid

class Object(object):
    def __init__(self, n1, o1):
        self.classID = n1
        self.actionDescriptor = o1
    
"""
putClass(desiredClass:Number):void    
putEnumerated(desiredClass:Number, enumType:Number, value:Number):void    
putIdentifier(desiredClass:Number, value:Number):void    
putIndex(desiredClass:Number, value:Number):void
putName(desiredClass:Number, value:String):void
putOffset(desiredClass:Number, value:Number):void
putProperty(desiredClass:Number, value:Number):void
"""

class Class(object):
    def __init__(self, n1):
        self.desiredClass = n1
        
class Enumerated(object):
    def __init__(self, n1, n2, n3):
        self.desiredClass = n1
        self.enumType = n2
        self.value = n3
        
class Identifier(object):
    def __init__(self, n1, n2):
        self.desiredClass = n1
        self.value = n2
        
class Index(object):
    def __init__(self, n1, n2):
        self.desiredClass = n1
        self.value = n2

class Name(object):
    def __init__(self, n1, s1):
        self.desiredClass = n1
        self.value = s1
        
class Offset(object):
    def __init__(self, n1, n2):
        self.desiredClass = n1
        self.value = n2
        
class Property(object):
    def __init__(self, n1, n2):
        self.desiredClass = n1
        self.value = n2
        
class UnitDouble(object):
    def __init__(self, n1, f1):
        self.unitID = n1
        self.value = f1
        
class Path(object):
    def __init__(self, n1):
        self.value = n1
        
def _do_put_actionlist(obj, value):
    if isinstance(value, bool):
        obj.putBoolean( value )
    elif isinstance(value, Class):
        obj.putClass( value.desiredClass)
    elif isinstance(value, bytes):        # 注意, 這裡可能是不對的!!!
        obj.putData( value )
    elif isinstance(value, float):
        obj.putDouble( value )
    elif isinstance(value, Enumerated):
        obj.putEnumerated( value.enumType, value.value)
    elif isinstance(value, int):
        obj.putInteger( value)
    elif isinstance(value, Object):
        obj.putObject( value.classID, value.actionDescriptor)
    elif str(type(value)) == "<class 'comtypes.POINTER(_ActionReference)'>":
        obj.putReference( value )
    elif isinstance(value, str):
        obj.putString( value )
    elif isinstance(value, UnitDouble):
        obj.putUnitDouble( value.unitID, value.value)
    elif isinstance(value, Path):
        obj.putPath(value.value)
    elif isinstance(value, List):
        obj.putList(value.list)
    else:
        raise value
        
class List(object):
    def __init__(self, *args):
        self.list = comtypes.client.CreateObject( "Photoshop.ActionList" )
        for arg in args:
            _do_put_actionlist(self.list, arg)

        
"""
void putBoolean (key: number, value: bool)
void putClass (key: number, value: number)
void putData (key: number, value: string)
void putDouble (key: number, value: number)
void putEnumerated (key: number, enumType: number, value: number)
void putInteger (key: number, value: number)
void putList (key: number, value: ActionList)
void putObject (key: number, classID: number, value: ActionDescriptor)
void putPath (key: number, value: File)
void putReference (key: number, value: ActionReference)
void putString (key: number, value: string)
void putUnitDouble (key: number, unitID: number, value: number)
"""

def _do_put_actiondesc(obj, key, value):
    if isinstance(value, bool):
        obj.putBoolean( key, value )
    elif isinstance(value, Class):
        obj.putClass( key, value.desiredClass)
    elif isinstance(value, bytes):        # 注意, 這裡可能是不對的!!!
        obj.putData( key, value )
    elif isinstance(value, float):
        obj.putDouble( key, value )
    elif isinstance(value, Enumerated):
        obj.putEnumerated( key, value.enumType, value.value)
    elif isinstance(value, int):
        obj.putInteger( key, value)
    elif isinstance(value, Object):
        obj.putObject(key, value.classID, value.actionDescriptor)
    elif str(type(value)) == "<class 'comtypes.POINTER(_ActionReference)'>":
        obj.putReference( key, value )
    elif isinstance(value, str):
        obj.putString( key, value )
    elif isinstance(value, UnitDouble):
        obj.putUnitDouble( key, value.unitID, value.value)
    elif isinstance(value, Path):
        obj.putPath(key, value.value)
    elif isinstance(value, List):
        obj.putList(key, value.list)
    else:
        raise value

class ActionDescriptor(object):
    def __init__(self, keyvalue=None):
        self.desc = comtypes.client.CreateObject( "Photoshop.ActionDescriptor" )
        if keyvalue:
            for key in keyvalue:
                self[key] = keyvalue[key]
        
    def __getitem__(self, key):
        pass
    def __setitem__(self, key, value):
        if isinstance(key, str) and len(key) == 4:
            key = C(key)
        elif isinstance(key, str):
            key = S(key)
        
        _do_put_actiondesc(self.desc, key, value)

"""
putClass(desiredClass:Number):void    
putEnumerated(desiredClass:Number, enumType:Number, value:Number):void    
putIdentifier(desiredClass:Number, value:Number):void    
putIndex(desiredClass:Number, value:Number):void
putName(desiredClass:Number, value:String):void
putOffset(desiredClass:Number, value:Number):void
putProperty(desiredClass:Number, value:Number):void
"""
def _do_put_actionref(obj, value):
    if isinstance(value, Class):
        obj.putClass(value.desiredClass)
    elif isinstance(value, Enumerated):
        obj.putEnumerated( value.desiredClass, value.enumType, value.value)
    elif isinstance(value, Identifier):
        obj.putIdentifier( value.desiredClass, value.value )
    elif isinstance(value, Index):
        obj.putIndex( value.desiredClass, value.value )
    elif isinstance(value, Offset):
        obj.putOffset( value.desiredClass, value.value )
    elif isinstance(value, Property):
        obj.putProperty( value.desiredClass, value.value )
    elif isinstance(value, Name):
        obj.putName( value.desiredClass, value.value )
    else:
        raise
    
def ActionReference(*args):
    ref = comtypes.client.CreateObject( "Photoshop.ActionReference" )
    for value in args:
        _do_put_actionref(ref, value)
    return ref


    
def ps_err_handle(f):
    #import codecs
    import pywintypes
    import _ctypes

    def do(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except pywintypes.com_error as e:
            except_string = (e.args[2][2]).encode('big5', 'ignore')
            #raise Exception(except_string)
            print(except_string)
            raise
        except _ctypes.COMError as e:
            print(e.args[1])
            except_string = (e.args[2][0]).encode('big5', 'ignore')
            #raise Exception(except_string)
            print(except_string)
            raise
    return do
