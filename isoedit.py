from collections import defaultdict 
import os
import re
import pygame
from pygame.locals import *
import pygame_gui

SCREENSIZE = (1024,640)

WHITE  = pygame.Color(255,255,255,255)
BLACK  = pygame.Color(0,0,0,255)
BACKGROUND = pygame.Color(96,96,128,255)
MASKED = pygame.Color(0,128,0,0)

SCALE = 10

ISOWIDTH = 40
ISOHEIGHT = ISOWIDTH>>1
ISOOFFSET = 4

WIDTH = ISOWIDTH-2
HEIGHT = 64-8

CENTERX = (WIDTH>>1)-1
CENTERY = (HEIGHT-ISOOFFSET-(ISOHEIGHT>>1))-1

OFFSETX = 600
OFFSETY = 5

PREVIEWX = 400
PREVIEWY = OFFSETY
PREVIEWSCALE = 2
PREVIEWHEIGHT = HEIGHT*PREVIEWSCALE
PREVIEWWIDTH = WIDTH*PREVIEWSCALE

MAPSCALE = 2
MAPX = 5
MAPY = 140


class PixelCanvas:

   def __init__(self,sarray,scale,offsetx=0,offsety=0):
      self.sarray = sarray
      self.scale = scale
      self.width = len(sarray)
      self.height = len(sarray[0])
      self.surface = pygame.Surface((self.width*self.scale,self.height*self.scale))
      self.offsetx = offsetx
      self.offsety = offsety
      self.lastColor = MASKED

   def get_surface(self):
      return self.surface

   def get_rect(self):
      return self.surface.get_rect(top=self.offsety,left=self.offsetx)

   def draw(self):
      self.surface.fill(BACKGROUND)
      for y in range(self.height):
         for x in range(self.width):
            color = self.sarray[x,y]
            self.surface.fill(color, (x*self.scale,y*self.scale,self.scale-1,self.scale-1))

   def checkPoint(self,pos):
      return self.get_rect().collidepoint(pos)

   def flip(self):
      self.sarray = self.sarray[::-1,:]
 
   def left(self):
      temp = self.sarray[0,:]
      self.sarray[:-1,:] = self.sarray[1:,:]
      self.sarray[-1,:] = temp

   def right(self):
      temp = self.sarray[-1,:]
      self.sarray[1:,:] = self.sarray[:-1,:]
      self.sarray[0,:] = temp

   def up(self):
      temp = self.sarray[:,0]
      self.sarray[:,:-1] = self.sarray[:,1:]
      self.sarray[:,-1] = temp

   def down(self):
      temp = self.sarray[:,-1]
      self.sarray[:,1:] = self.sarray[:,:-1]
      self.sarray[:,0] = temp


   def get_preview(self):
      return self.sarray.make_surface()

   def coord(self,pos):
      return ( int((pos[0]-self.offsetx) / self.scale),
               int((pos[1]-self.offsety) / self.scale) )

   def button_color(self, button):
      if button is None:
         return self.lastColor
      elif (button == 1):
         return WHITE
      elif (button == 3):
         return BLACK 
      return MASKED

   def paint(self,pos,button):
      (x,y) = self.coord(pos)
      color = self.button_color(button)
      self.sarray[x,y] = color
      self.lastColor = color

   def set_image(self,surface):
      self.sarray = pygame.PixelArray(surface)


class Tile:
   def __init__(self,path,name,framecount=0,animation=None):
      self.path = path
      self.name = name
      self.animation = animation

      if (framecount > 0):
         self.surface = [ self.read(f) for f in range(framecount)]
      else:
         self.surface = [ self.read() ]

   def read(self,frame=None):
      if frame is None:
         return pygame.image.load(os.path.join(self.path,self.name + ".png"))
      else:
         return pygame.image.load(os.path.join(self.path,self.name + "_" + self.animation + str(frame) + ".png"))

   def animationFrame(self,framecount,x):
      if (self.animation is None):
         return 0
      elif (self.animation == 'w'):
         # Wave
         frame = (((framecount) >> 4)+x) & 0x7
         if frame > 3:
            frame = 7 - frame
         return frame
      elif (self.animation == 'l'):
         # Linear
         frame = ((framecount) >> 5) % len(self.surface)
         return frame
      # must be blink
      elif ((((framecount>>3)^x)&0x3f) == 0):
         return 1
      return 0

   def get_animated_surface(self,frameCount,x):
      index = self.animationFrame(frameCount,x)
      return self.surface[index]

   def get_surface(self,frame):
      return self.surface[frame]

   def get_frame_count(self):
      return len(self.surface)

class TileList:

   def __init__(self,path):
      self.path = path
      self.tiles = {}

   def read(self):
      # get a list of all .png fles in the directory
      filelist = [f.split('.')[0] for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path,f)) and (f.find('.png') != -1)]

      # group into frames
      framelist = defaultdict(int)
      animation = {}
      for f in filelist:
         m = re.search('(.*)_([lbw])([0-7])',f)
         if m is None:
            framelist[f] = 0
            animation[f] = None
         else:
            name = m.group(1)
            anitype = m.group(2)
            frame = m.group(3)
            framelist[name] = max(int(frame)+1,framelist[name])
            animation[name] = anitype
      # create a tile per set
      for n in framelist.keys():
         self.tiles[n] = Tile(self.path,n,framelist[n],animation[n])

   def name_list(self):
      return(list(self.tiles.keys()))

   def get_frame_count(self,name):
      return(self.tiles[name].get_frame_count())

   def get_animated_surface(self,name,frameCount=0,x=0):
      surface = None
      for t in name.split(','):
         tile = self.tiles[t]
         if surface is None:
            surface = tile.get_animated_surface(frameCount,x)
         else:
            surface = surface.copy()
            surface.blit(tile.get_animated_surface(frameCount,x).copy(),(0,0))
      return surface

   def get_surface(self,name,frame=0):
      return(self.tiles[name].get_surface(frame))

class Map:

   def __init__(self,tiles,width,height,scale,offsetx=0,offsety=0):
      self.tiles = tiles
      self.width = width      # display width
      self.height = height    # display height
      self.scale = scale
      self.offsetx = offsetx
      self.offsety = offsety

      self.sizew = 64
      self.sizeh = 32
      self.posx = 0
      self.posy = 0

      defaultTile = 'groundGrass0'
      self.data = [[defaultTile for i in range(self.sizeh)] for j in range(self.sizew)]
      self.surface = pygame.Surface((self.width*self.scale*ISOWIDTH,((self.height*self.scale)>>1)*ISOHEIGHT+HEIGHT*self.scale))

      self.previewTile = None
      self.previewX = 0
      self.previewY = 0

   def isoPos(self,pos):
      (x,y) = pos
      ix = x*ISOWIDTH+(y%2)*(ISOWIDTH>>1)
      iy = (y*ISOHEIGHT)>>1
      return(ix,iy)

   def closestTile(self,pos):
      minDist = None
      closeX = 0
      closeY = 0

      for y in range(self.height):
         for x in range(self.width-y%2):
            (ix,iy) = self.isoPos((x,y))
            delx =  pos[0] - (self.offsetx + (self.scale*(ix+CENTERX)))
            dely =  pos[1] - (self.offsety + (self.scale*(iy+CENTERY)))
            dist = delx**2 + dely**2
            if ((minDist is None) or (dist < minDist)):
               minDist = dist
               closeX = x
               closeY = y

      return(closeX,closeY,self.data[self.posx + closeX][self.posy + closeY])

   def preview(self,tile,pos):
      (self.previewX,self.previewY,name) = self.closestTile(pos)
      self.previewTile = tile

   def paint(self,tile,pos,append=False):
      (self.previewX,self.previewY,name) = self.closestTile(pos)
      if append:
         self.previewTile = self.data[self.posx + self.previewX][self.posy + self.previewY] + ',' + tile
      else:
         self.previewTile = tile

      self.data[self.posx + self.previewX][self.posy + self.previewY]=self.previewTile

   def clear_preview(self):
      self.previewTile = None

   def draw(self,framecount):
      self.surface.fill(BACKGROUND)


      for y in range(self.height):
         for x in range(self.width-y%2):
            tile =  pygame.transform.scale(self.tiles.get_animated_surface(self.data[self.posx+x][self.posy+y],framecount,x),(WIDTH*self.scale,HEIGHT*self.scale))
            (ix,iy) = self.isoPos((x,y))
            self.surface.blit(tile,(self.scale*ix,self.scale*iy))


      if self.previewTile is not None:
         tile =  pygame.transform.scale(self.tiles.get_animated_surface(self.previewTile,0),(WIDTH*self.scale,HEIGHT*self.scale))
         tile.fill((200,200,0,128),None,BLEND_RGBA_MULT)
         (ix,iy) = self.isoPos((self.previewX,self.previewY))
         self.surface.blit(tile,(self.scale*ix,self.scale*iy))
      return self.surface

   def get_surface(self):
      return self.surface

   def get_rect(self):
      return self.surface.get_rect(top=self.offsety,left=self.offsetx)

   def checkPoint(self,pos):
      return self.get_rect().collidepoint(pos)

   def up(self,step):
      self.posy = self.posy - step
      if (self.posy < 0):
         self.posy = 0

   def down(self,step):
      self.posy = self.posy + step
      if (self.posy + self.height > self.sizeh):
         self.posy = self.sizeh - self.height

   def left(self,step):
      self.posx = self.posx - step
      if (self.posx < 0):
         self.posx = 0

   def right(self,step):
      self.posx = self.posx + step
      if (self.posx + self.width > self.sizew):
         self.posx = self.sizew - self.width

   def tileType(self,data):
      t = data.split(',')
      if len(t) == 1:
         if (t[0].startswith('block') or
             t[0].startswith('deco') or
             t[0].startswith('wall') or
             t[0].startswith('ramp')):
            return('blocked')
         elif t[0].startswith('ground'):
            return('free')
         else:
            return('unknown')
      else:
         if t[1].startswith('obj'):
            return('common_'+t[1])
         if t[1].startswith('character'):
            return('unique')
         else:
            return('unknown')

   def output(self,frameMap):
      out = []
      info = []
      prop = {}
      propCount = 0

      info.append("#define MAP_WIDTH     {}".format(self.sizew))
      info.append("#define MAP_HEIGHT    {}".format(self.sizeh))
      info.append("#define MAP_TILE_SIZE {}".format(3))
      
      for y in range(self.sizeh):
         for x in range(self.sizew):

            t = self.data[x][y].split(',')
            # bg frame
            out.append(frameMap[t[0]])
            # fg frame
            if (len(t) > 1):
               out.append(frameMap[t[1]])
            else:
               out.append(0)
            # index
            tile = self.tileType(self.data[x][y])
            assert tile != 'unknown', 'Unknown tile type {} at {},{}'.format(self.data[x][y],x,y)
            index = 0
            if tile == 'unique':
               index = propCount
               propCount += 1
               info.append('// prop {} = {} // {}'.format(tile,index,self.data[x][y]))
            elif tile in prop:
               index = prop[tile]
            else:
               index = propCount
               prop[tile] = index
               propCount += 1
               info.append('// prop {} = {} // {}'.format(tile,index,self.data[x][y]))

            out.append(index)

      return(out,info)

   def save(self,mapFilename='map.txt'):
      output = []
      defines = {}

      for y in range(self.sizeh):
         outline = []
         for x in range(self.sizew):
            cell = self.data[x][y]
            if cell not in defines:
               defines[cell] = '{:02x}'.format(len(defines))
            outline.append(defines[cell])
         output.append(';'.join(outline))

      with open(mapFilename, "w") as text_file:
         byteCount = 0
         for d in defines:
            byteCount += text_file.write('{}={}\n'.format(defines[d],d))
         byteCount += text_file.write('\n'.join(output))
         print("Wrote {} bytes to {}".format(byteCount,mapFilename))

   def load(self,mapFilename='map.txt'):
      defines = {}
      y = 0

      with open(mapFilename, "r") as text_file:

         for l in text_file.readlines():
            line = l.strip()
            if '=' in line:
               (name,value) = line.split('=')
               defines[name] = value
            else:
               x = 0
               for cell in line.split(';'):
                  self.data[x][y] = defines[cell]
                  x += 1
               y+=1

         print("Read {} rows from {}".format(y,mapFilename))

# return 1-bit color and mask
def colorTo1Bit(color):
   brightness = (0.21 * color[0]) + (0.72 * color[1]) + (0.07 * color[2])
   return(brightness > 128, color[3] > 200)

def outputBytes(tiles,isomap,filename='data'):

   binFilename = filename+".bin"
   infoFilename = filename+".h"

   frameMap= {}

   outputInfo = []
   outputBytes = bytearray();

   tileNumber = 0

   outputInfo.append('#define {:25} 0x{:06x}'.format('TILE_START',len(outputBytes)))

   outputBytes.append(0);  # upper byte
   outputBytes.append(WIDTH);
   outputBytes.append(0);  # upper byte
   outputBytes.append(HEIGHT);

   for t in tiles.name_list():
      framecount = tiles.get_frame_count(t)
      outputInfo.append('#define {:30} 0x{:02x} // 0x{:06x} frames {:2}'.format('TILE_'+t,tileNumber,len(outputBytes),framecount))

      # remember frame mapping
      frameMap[t] = tileNumber 

      # calc next tile
      tileNumber = tileNumber + framecount

      for f in range(framecount):
         surface = tiles.get_surface(t,f)
         size = surface.get_rect()
         for y in range(size.h // 8):
            for x in range(size.w):
               colorByte = 0
               maskByte = 0
               for bitPos in range(8):
                  (color,mask) = colorTo1Bit(surface.get_at((x,y*8+bitPos)))
                  colorByte = colorByte | (color<<bitPos)
                  maskByte =  maskByte  | (mask <<bitPos)
               outputBytes.append(colorByte)
               outputBytes.append(maskByte)

   outputInfo.append('#define {:25} 0x{:06x}'.format('MAP_START',len(outputBytes)))

   (mapBytes,mapInfo) =  isomap.output(frameMap)

   for b in mapBytes:
      outputBytes.append(b)

   outputInfo += mapInfo

   outputInfo.append('// Total bytes = {} (0x{:06x})'.format(len(outputBytes),len(outputBytes)))

   with open(binFilename, "wb") as binary_file:
      byteCount = binary_file.write(outputBytes)
      print("Wrote {} bytes to {}".format(byteCount,binFilename))

   with open(infoFilename, "w") as text_file:
      byteCount = text_file.write('\n'.join(outputInfo))
      print("Wrote {} bytes to {}".format(byteCount,infoFilename))

def main():

   # make a list of tile files
   tiles = TileList('tiles')
   tiles.read()

   pygame.init()
   screen = pygame.display.set_mode(SCREENSIZE,SRCALPHA)
   pygame.display.set_caption('Arduboy isometric tile editor')
   clock = pygame.time.Clock()
   font = pygame.font.Font(None,32)

   manager = pygame_gui.UIManager(SCREENSIZE)

   currentTile = tiles.name_list()[0]
   tileSelect = pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(options_list=tiles.name_list(),
                                                                     starting_option=currentTile,
                                                                     relative_rect=pygame.Rect((100,0),(200,22)),
                                                                     manager=manager,
                                                                     expansion_height_limit=125)

   filterText = pygame_gui.elements.ui_text_entry_line.UITextEntryLine( relative_rect=pygame.Rect((0,0),(100,22)),
                                                                        manager=manager)

   shape = tiles.get_surface(tiles.name_list()[0])
   canvas = PixelCanvas(pygame.PixelArray(shape),SCALE,OFFSETX,OFFSETY)

   isomap = Map(tiles,7,16,MAPSCALE,MAPX,MAPY)
   framecount = 0
   info = None

   active = None

   while True:

      time_delta = clock.tick(60)/1000.0

      # keep a 16 bit counter
      framecount = (framecount + 1) & 0xffff


      for event in pygame.event.get():
         if event.type == QUIT:
            pygame.quit()
            return

         elif event.type == MOUSEBUTTONDOWN:
            if canvas.checkPoint(event.pos):
               active = "canvas"
               canvas.paint(event.pos,event.button)
            elif (isomap.checkPoint(event.pos)):
               active = "map"
               isomap.paint(currentTile,event.pos,event.button==3)

         elif event.type == MOUSEMOTION:
            if (canvas.checkPoint(event.pos)):
               active = "canvas"
               if (event.buttons[0] or event.buttons[1] or event.buttons[2]):
                  canvas.paint(event.pos,None)
               (x,y) = canvas.coord(event.pos)
               info = font.render("{}: x={:02}, y={:02}".format(active,x,HEIGHT-1-y),True,WHITE,BLACK)

            elif (isomap.checkPoint(event.pos)):
               active = "map"
               if (event.buttons[0]):
                  isomap.paint(currentTile,event.pos)
               else:
                  isomap.preview(currentTile,event.pos)
               (x,y,name)=isomap.closestTile(event.pos)
               info = font.render("{}: x={:02}, y={:02}: {}".format(active,isomap.posx+x,isomap.posy+y,name),True,WHITE,BLACK)

            else:
               active = None
               isomap.clear_preview()

         elif event.type == KEYDOWN:
            shift = event.mod & pygame.KMOD_SHIFT
            if (active == "canvas"):
               if event.key == K_h:
                  # flip horizontal
                  canvas.flip()
                  #shapeArray = shapeArray[::-1,:]
               elif event.key == K_LEFT:
                  canvas.left()
               elif event.key == K_RIGHT:
                  canvas.right()
               elif event.key == K_UP:
                  canvas.up()
               elif event.key == K_DOWN:
                  canvas.down()
               elif event.key == K_o:
                  # Output
                  print("Output to iso.png")
                  pygame.image.save(canvas.get_preview(),"iso.png")
               elif event.key == K_i:
                  # load
                  print("Input from iso.png")
                  canvas.set_image(pygame.image.load("iso.png"))

            if (active == "map"):
               if event.key == K_x:
                  # export
                  print("Export tile data")
                  outputBytes(tiles,isomap)
               # MAP movement
               elif event.key == K_w:
                  isomap.up(14 if shift else 2)
                  info = None
               elif event.key == K_a:
                  isomap.left(6 if shift else 1)
                  info = None
               elif event.key == K_s:
                  isomap.down(14 if shift else 2)
                  info = None
               elif event.key == K_d:
                  isomap.right(6 if shift else 1)
                  info = None
               elif event.key == K_o:
                  # Output
                  isomap.save()
               elif event.key == K_i:
                  # Input
                  isomap.load()

         if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
               currentTile = event.text
               canvas.set_image(tiles.get_surface(currentTile,0))
            elif event.user_type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
               # should probably change to a RE
               filter_list =  list(filter(lambda x: event.text.lower() in x.lower(), tiles.name_list()))
               if len(filter_list) > 0:
                  currentTile = filter_list[0]
                  tileSelect.kill()
                  tileSelect = pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(options_list=filter_list,
                                                                     starting_option=currentTile,
                                                                     relative_rect=pygame.Rect((100,0),(200,22)),
                                                                     manager=manager,
                                                                     expansion_height_limit=125)
                  canvas.set_image(tiles.get_surface(currentTile,0))


         manager.process_events(event)

      manager.update(time_delta)


      screen.fill(BACKGROUND)

      canvas.draw()
      screen.blit(canvas.get_surface(),canvas.get_rect())

      isomap.draw(framecount)
      screen.blit(isomap.get_surface(),isomap.get_rect())

      preview = canvas.get_preview()
      previewScaled = pygame.transform.scale(preview,(PREVIEWWIDTH,PREVIEWHEIGHT))

      screen.blit(preview,(PREVIEWX,PREVIEWY))
      screen.blit(previewScaled,(PREVIEWX+WIDTH+5,PREVIEWY))

      if (info is not None):
         screen.blit(info,(5,600))

      
      manager.draw_ui(screen)

      pygame.display.flip()

# Execute game:
main()


