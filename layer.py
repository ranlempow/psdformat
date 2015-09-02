import os
from PIL import Image
from ImageData import *


CHANNEL_ALPHA_1 = -1
CHANNEL_ALPHA_2 = -2
CHANNEL_ALPHA_3 = -3
CHANNEL_RED = 0
CHANNEL_GREEN = 1
CHANNEL_BLUE = 2

# TODO: move to descriptor
FOLDER_OPEN = 1
FOLDER_CLOSE = 2
FOLDER_DIVIDE = 3

# TODO: TreeHandler

        
class SaveLayerHandler:
    def __call__(self, f, layer, parents):
        left = layer['Left']
        top = layer['Top']
        width = layer['Right'] - layer['Left']
        height = layer['Bottom'] - layer['Top']
        name = layer['Name']
        
        name = '$'.join(parents + [name])
        name += '@' + '@'.join(map(str, [layer['Left'], layer['Top'], width, height]))
        
        image = read_channels_as_image(f, layer['Channels'], width, height)
        
        saved_name = name.replace('/', '_')
        image.save('output/' + saved_name + '.png')

def read_layer(handler, f, psdformat):
    layers = psdformat['Layer']['Layers'][:]
    layers.reverse()
    
    parents_stack = []
    for layer in layers:
        
        name = layer['Name']
        folder = None
        for info in layer['AddtionInfos']:
            if info.type == b'lsct':
                folder = int(info.data[3])
        
        if folder == FOLDER_OPEN or folder == FOLDER_CLOSE:
            parents_stack.append(name)
        elif folder == FOLDER_DIVIDE:
            parents_stack.pop()
        elif folder is None:
            handler(f, layer, parents_stack)
                
    
def read_channels_as_image(f, channels, width, height):
    oripos = f.tell()
    imgs = {}
    #for k in range(len(channels)):
    for channel in channels:
        #  沒影像的圖層, 可能是圖層資料夾
        #if 'Compression' not in layer['Channels'][k]:
        #    continue
        
        id = channel['Id']
        compression = channel['Compression']
        ptr = channel['PosInFile']
        datalen = channel['Length']
        
        f.seek(ptr, os.SEEK_SET)
        data = f.read(datalen)
        cdata = DecodeChannelImageData(data, compression, width, height)
        img = Image.frombuffer("L", (width, height), cdata, 'raw', "L", 0, 1)
        imgs[id] = img
    
    result = None
    if imgs:
        alpha = None
        if CHANNEL_ALPHA_1 in imgs:
            alpha = imgs[CHANNEL_ALPHA_1]
            
        if CHANNEL_ALPHA_2 in imgs: 
            if alpha is None:
                alpha = imgs[CHANNEL_ALPHA_2]
            else:
                alpha.paste(255, None, imgs[CHANNEL_ALPHA_2])
            
        if CHANNEL_ALPHA_3 in imgs: 
            if alpha is None:
                alpha = imgs[CHANNEL_ALPHA_3]
            else:
                alpha.paste(255, None, imgs[CHANNEL_ALPHA_3])
            
            
        if CHANNEL_RED in imgs and CHANNEL_GREEN in imgs and CHANNEL_BLUE in imgs:
            rgb = (imgs[CHANNEL_RED], imgs[CHANNEL_GREEN], imgs[CHANNEL_BLUE])
            if alpha:
                result = Image.merge("RGBA", rgb + (alpha,))
            else:
                result = Image.merge("RGB", rgb)
                
        elif CHANNEL_RED in imgs:
            # 還沒考慮多重色版的狀況
            if alpha:
                result = Image.merge("LA", (imgs[CHANNEL_RED], alpha)) 
            else:
                result = Image.merge("L", (imgs[CHANNEL_RED]))
        else:
            logging.error(imgs.keys())
            raise

    f.seek(oripos, os.SEEK_SET)
    return result

def read_final_as_image(f, psdformat):
    width = psdformat["Basic"]['Width']
    height = psdformat["Basic"]['Height']
    channelcounts = psdformat["Basic"]['ChannelCounts']
    compression = psdformat["Image"]['Compression']
    ori = f.tell()
    f.seek(psdformat["Image"]['PosInFile'], os.SEEK_SET)
    
    # 貪婪讀取可能會讀取過多的資料(雖然結尾所剩資料不多)
    # 但是效率較好
    cdata = DecodeFinalImageData(f.read(), compression, channelcounts, width, height)
    cdatas = []
    for ch in range(channelcounts):
        cdatas.append(cdata[ch*width*height:(ch+1)*width*height])
    
    #elif compression == 0:
    #    for ch in range(channelcounts):
    #        cdatas.append(f.read(widht * height))
            
    from PIL import Image
    icr = Image.frombuffer("L", (width, height), cdatas[0], 'raw', "L", 0, 1)
    icg = Image.frombuffer("L", (width, height), cdatas[1], 'raw', "L", 0, 1)
    icb = Image.frombuffer("L", (width, height), cdatas[2], 'raw', "L", 0, 1)
    result = Image.merge("RGB", (icr, icg, icb)) 
    #result.save('irgb.bmp')
    
    f.seek(ori, os.SEEK_SET)
    
    return result
