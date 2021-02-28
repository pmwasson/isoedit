import os
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

OFFSETX = 600
OFFSETY = 5


HEIGHT = 64-8
PREVIEWX = 5
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

   def get_surface(self):
      return self.surface

   def get_rect(self):
      return self.surface.get_rect(top=self.offsety,left=self.offsetx)

   def draw(self):

      for y in range(self.height):
         for x in range(self.width):
            color = self.sarray[x,y]
            self.surface.fill(color, (x*self.scale,y*self.scale,self.scale-1,self.scale-1))

   def checkPoint(self,pos):
      return self.get_rect().collidepoint(pos)

   def flip(self):
      self.sarray = self.sarray[::-1,:]
 
   def get_preview(self):
      return self.sarray.make_surface()

   def coord(self,pos):
      return ( int((pos[0]-self.offsetx) / self.scale),
               int((pos[1]-self.offsety) / self.scale) )

   def paint(self,pos,color):
      (x,y) = self.coord(pos)
      self.sarray[x,y] = color

   def set_image(self,surface):
      self.sarray = pygame.PixelArray(surface)


class TileList:

   def __init__(self,path):
      self.path = path
      self.list = None

   def read(self):
      self.list = [f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path,f)) and (f.find('.png') != -1)] 

   def name_list(self):
      return([f.split('.')[0] for f in self.list])

   def load_surface(self,name):
      index = self.name_list().index(name)
      return pygame.image.load(os.path.join(self.path,self.list[index]))

class Map:

   def __init__(self,tiles,width,height,scale,offsetx=0,offsety=0):
      self.tiles = tiles
      self.width = width
      self.height = height
      self.scale = scale
      self.offsetx = offsetx
      self.offsety = offsety

      defaultTile = tiles.name_list()[0]
      self.data = [[defaultTile] * height] * width
      self.surface = pygame.Surface((self.width*self.scale*ISOWIDTH,((self.height*self.scale)>>1)*ISOHEIGHT+HEIGHT*self.scale))
 
   def isoPos(pos):
      (x,y) = pos
      ix = x*ISOWIDTH+(y%2)*(ISOWIDTH>>1)
      iy = (y*ISOHEIGHT)>>1
      return(ix,iy)

   def draw(self):
      self.surface.fill(BACKGROUND)
      for y in range(self.height):
         for x in range(self.width-y%2):
            tile =  pygame.transform.scale(self.tiles.load_surface(self.data[x][y]),(WIDTH*self.scale,HEIGHT*self.scale))
            (ix,iy) = Map.isoPos((x,y))
            self.surface.blit(tile,(self.scale*ix,self.scale*iy))
      return self.surface

   def get_surface(self):
      return self.surface

   def get_rect(self):
      return self.surface.get_rect(top=self.offsety,left=self.offsetx)

def getFiles(path):
   files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
   return(files)


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

   tileSelect = pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(options_list=tiles.name_list(),
                                                                     starting_option=tiles.name_list()[0],
                                                                     relative_rect=pygame.Rect((0,0),(200,22)),
                                                                     manager=manager)


   shape = tiles.load_surface(tiles.name_list()[0])
   canvas = PixelCanvas(pygame.PixelArray(shape),SCALE,OFFSETX,OFFSETY)

   map = Map(tiles,7,16,MAPSCALE,MAPX,MAPY)
   map.draw()

   (lastX,lastY) = (0,0)

   while True:

      time_delta = clock.tick(60)/1000.0

      for event in pygame.event.get():
         if event.type == QUIT:
            pygame.quit()
            return
         elif event.type == MOUSEBUTTONDOWN:
            if (event.button == 1):
               color = WHITE
            elif (event.button == 3):
               color = BLACK
            elif (event.button == 2):
               color = MASKED
            if (canvas.checkPoint(event.pos)):
               canvas.paint(event.pos,color)
               lastColor = color
         elif event.type == MOUSEMOTION:
            if (canvas.checkPoint(event.pos) and
               (event.buttons[0] or event.buttons[1] or event.buttons[2])):
               canvas.paint(event.pos,color)
               (lastX,lastY) = canvas.coord(event.pos)

         elif event.type == TEXTINPUT:
            if event.text == 'h':
               # flip horizontal
               canvas.flip()
               #shapeArray = shapeArray[::-1,:]
            elif event.text == 's':
               # save
               print("Saved to iso.png")
               pygame.image.save(canvas.get_preview(),"iso.png")
            elif event.text == 'l':
               # load
               print("Load from iso.png")
               canvas.set_image(pygame.image.load("iso.png"))
         if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
               canvas.set_image(tiles.load_surface(event.text))

         manager.process_events(event)

      manager.update(time_delta)


      screen.fill(BACKGROUND)
      canvas.draw()
      screen.blit(canvas.get_surface(),canvas.get_rect())

      preview = canvas.get_preview()
      previewScaled = pygame.transform.scale(preview,(PREVIEWWIDTH,PREVIEWHEIGHT))
      #previewScaled.fill((200,200,0,128),None,BLEND_RGBA_MULT)

      screen.blit(preview,(PREVIEWX,PREVIEWY))
      screen.blit(previewScaled,(PREVIEWX+WIDTH+5,PREVIEWY))

      screen.blit(map.get_surface(),map.get_rect())

      screen.blit(font.render("x={:02}, y={:02}".format(lastX-19,HEIGHT-1-lastY-14),True,WHITE,BLACK),(5,600))

      manager.draw_ui(screen)

      pygame.display.flip()

# Execute game:
main()


