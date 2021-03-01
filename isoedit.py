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
HEIGHT = 64-8

CENTERX = (WIDTH>>1)-1
CENTERY = (HEIGHT-ISOOFFSET-(ISOHEIGHT>>1))-1

OFFSETX = 600
OFFSETY = 5

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
      self.lastColor = MASKED

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


class TileList:

   def __init__(self,path):
      self.path = path
      self.list = None
      self.surfaces = None

   def read(self):
      self.list = [f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path,f)) and (f.find('.png') != -1)]
      self.surfaces = [pygame.image.load(os.path.join(self.path,f)) for f in self.list]

   def name_list(self):
      return([f.split('.')[0] for f in self.list])

   def get_surface(self,name):
      index = self.name_list().index(name)
      return self.surfaces[index]

class Map:

   def __init__(self,tiles,width,height,scale,offsetx=0,offsety=0):
      self.tiles = tiles
      self.width = width
      self.height = height
      self.scale = scale
      self.offsetx = offsetx
      self.offsety = offsety

      defaultTile = tiles.name_list()[0]
      self.data = [[defaultTile for i in range(height)] for j in range(width)]
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

      return(closeX,closeY)

   def preview(self,tile,pos):
      (self.previewX,self.previewY) = self.closestTile(pos)
      self.previewTile = tile

   def paint(self,tile,pos):
      (self.previewX,self.previewY) = self.closestTile(pos)
      self.previewTile = tile
      self.data[self.previewX][self.previewY]=tile

   def clear_preview(self):
      self.previewTile = None

   def draw(self):
      self.surface.fill(BACKGROUND)
      for y in range(self.height):
         for x in range(self.width-y%2):
            tile =  pygame.transform.scale(self.tiles.get_surface(self.data[x][y]),(WIDTH*self.scale,HEIGHT*self.scale))
            (ix,iy) = self.isoPos((x,y))
            self.surface.blit(tile,(self.scale*ix,self.scale*iy))

      if self.previewTile is not None:
         tile =  pygame.transform.scale(self.tiles.get_surface(self.previewTile),(WIDTH*self.scale,HEIGHT*self.scale))
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

   currentTile = tiles.name_list()[0]
   tileSelect = pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(options_list=tiles.name_list(),
                                                                     starting_option=currentTile,
                                                                     relative_rect=pygame.Rect((0,0),(200,22)),
                                                                     manager=manager)


   shape = tiles.get_surface(tiles.name_list()[0])
   canvas = PixelCanvas(pygame.PixelArray(shape),SCALE,OFFSETX,OFFSETY)

   isomap = Map(tiles,7,16,MAPSCALE,MAPX,MAPY)
   (lastX,lastY) = (0,0)

   while True:

      time_delta = clock.tick(60)/1000.0

      for event in pygame.event.get():
         if event.type == QUIT:
            pygame.quit()
            return

         elif event.type == MOUSEBUTTONDOWN:
            if canvas.checkPoint(event.pos):
               canvas.paint(event.pos,event.button)
            elif (isomap.checkPoint(event.pos)):
               isomap.paint(currentTile,event.pos)

         elif event.type == MOUSEMOTION:
            if (canvas.checkPoint(event.pos)):
               if (event.buttons[0] or event.buttons[1] or event.buttons[2]):
                  canvas.paint(event.pos,None)
               (lastX,lastY) = canvas.coord(event.pos)

            if (isomap.checkPoint(event.pos)):
               if (event.buttons[0]):
                  isomap.paint(currentTile,event.pos)
               else:
                  isomap.preview(currentTile,event.pos)
            else:
               isomap.clear_preview()

         elif event.type == KEYDOWN:
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
            elif event.key == K_s:
               # save
               print("Saved to iso.png")
               pygame.image.save(canvas.get_preview(),"iso.png")
            elif event.key == K_l:
               # load
               print("Load from iso.png")
               canvas.set_image(pygame.image.load("iso.png"))
         if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
               currentTile = event.text
               canvas.set_image(tiles.get_surface(currentTile))

         manager.process_events(event)

      manager.update(time_delta)


      screen.fill(BACKGROUND)

      canvas.draw()
      screen.blit(canvas.get_surface(),canvas.get_rect())

      isomap.draw()
      screen.blit(isomap.get_surface(),isomap.get_rect())

      preview = canvas.get_preview()
      previewScaled = pygame.transform.scale(preview,(PREVIEWWIDTH,PREVIEWHEIGHT))

      screen.blit(preview,(PREVIEWX,PREVIEWY))
      screen.blit(previewScaled,(PREVIEWX+WIDTH+5,PREVIEWY))


      screen.blit(font.render("x={:02}, y={:02}".format(lastX-19,HEIGHT-1-lastY-14),True,WHITE,BLACK),(5,600))

      manager.draw_ui(screen)

      pygame.display.flip()

# Execute game:
main()


