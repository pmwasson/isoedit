import os
import pygame
from pygame.locals import *

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
OFFSETX = 5
OFFSETY = 5
PREVIEWX = OFFSETX*2 + WIDTH*SCALE
PREVIEWY = OFFSETY
PREVIEWSCALE = 2
PREVIEWHEIGHT = HEIGHT*PREVIEWSCALE
PREVIEWWIDTH = WIDTH*PREVIEWSCALE

class pixelCanvas:

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

def getFiles(path):
   files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
   return(files)

def isoPos(pos):
   (x,y) = pos
   ix = x*ISOWIDTH+(y%2)*(ISOWIDTH>>1)
   iy = (y*ISOHEIGHT)>>1
   return(ix,iy)

def main():

   # make a list of tile files
   files = getFiles('tiles')
   print("files=",files)


   pygame.init()
   screen = pygame.display.set_mode((1024, 640),SRCALPHA)
   pygame.display.set_caption('Arduboy isometric tile editor')
   clock = pygame.time.Clock()
   font = pygame.font.Font(None,32)

   shape = pygame.Surface((WIDTH,HEIGHT),SRCALPHA)
   shape.fill(MASKED)
   for x in range(10):
      shape.fill(BLACK,(x*2,HEIGHT-11-ISOOFFSET-x,WIDTH-4*x,(x+1)*2+ISOOFFSET))
      shape.fill(WHITE,(x*2,HEIGHT-11-ISOOFFSET-x,WIDTH-4*x,(x+1)*2))

   canvas = pixelCanvas(pygame.PixelArray(shape),SCALE,OFFSETX,OFFSETY)
   (lastX,lastY) = (0,0)

   while True:
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

      clock.tick(60)

      screen.fill(BACKGROUND)

      canvas.draw()
      screen.blit(canvas.get_surface(),canvas.get_rect())

      preview = canvas.get_preview()
      previewScaled = pygame.transform.scale(preview,(PREVIEWWIDTH,PREVIEWHEIGHT))
      #previewScaled.fill((200,200,0,128),None,BLEND_RGBA_MULT)

      screen.blit(preview,(PREVIEWX,PREVIEWY))
      screen.blit(previewScaled,(PREVIEWX+WIDTH+5,PREVIEWY))

      for y in range(16):
         for x in range(7-y%2):
            (ix,iy) = isoPos((x,y))
            screen.blit(previewScaled,(PREVIEWX+PREVIEWSCALE*ix,PREVIEWY+PREVIEWHEIGHT+5+PREVIEWSCALE*iy))

      screen.blit(font.render("x={:02}, y={:02}".format(lastX-19,HEIGHT-1-lastY-14),True,WHITE,BLACK),(5,600))

      pygame.display.flip()

# Execute game:
main()


