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


def isoPos(pos):
   (x,y) = pos
   ix = x*ISOWIDTH+(y%2)*(ISOWIDTH>>1)
   iy = (y*ISOHEIGHT)>>1
   return(ix,iy)

def scalePos(pos):
   x = int((pos[0] - OFFSETX)/SCALE)
   y = int((pos[1] - OFFSETY)/SCALE)
   return(x,y)

def checkPos(pos):
   (x,y)=pos
   if (x>=0) and (x < WIDTH) and (y>=0) and (y < HEIGHT):
      return True
   return False

def paint(shapeArray,pos,color):
   if checkPos(pos):
      (x,y)=pos
      shapeArray[x,y] = color
   return(color,shapeArray.make_surface())

def getFiles(path):
   files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
   return(files)

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

   preview = shape.copy()

   shapeArray = pygame.PixelArray(shape)
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
               (lastColor,preview) = paint(shapeArray,scalePos(event.pos),color)
            elif event.type == MOUSEMOTION:
               pos = scalePos(event.pos)
               if checkPos(pos):
                  (lastX,lastY) = pos
               if (event.buttons[0] or event.buttons[1] or event.buttons[2]):
                  (lastColor,preview) = paint(shapeArray,scalePos(event.pos),lastColor)
            elif event.type == TEXTINPUT:
               if event.text == 'h':
                  # flip horizontal
                  shapeArray = shapeArray[::-1,:]
               elif event.text == 'v':
                  # flip vertical
                  shapeArray = shapeArray[:,::-1]
               elif event.text == 's':
                  # save
                  print("Saved to iso.png")
                  pygame.image.save(preview,"iso.png")
               elif event.text == 'l':
                  # load
                  print("Load from iso.png")
                  shape = pygame.image.load("iso.png")
                  shapeArray = pygame.PixelArray(shape)

               preview = shapeArray.make_surface();

      clock.tick(60)

      screen.fill(BACKGROUND)


      for y in range(HEIGHT):
         for x in range(WIDTH):
            color = shapeArray[x,y]
            screen.fill(color, (OFFSETX+x*SCALE,OFFSETY+y*SCALE,SCALE-1,SCALE-1))

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


