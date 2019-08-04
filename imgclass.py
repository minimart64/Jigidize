#!/usr/bin/env python3

import sys, pygame, os, shutil, time, imghdr
pygame.init()

imgFolder = "/home/pi/Downloads/img"
keepFolder = "/home/pi/Downloads/img/good"
tossFolder = "/home/pi/Downloads/img/bad"
imgList = os.listdir(imgFolder)
img = imgList[0]

waiting = True

screenSize = display_width, display_height = 1270, 950
btnWidth = 100
btnHeight = 50
btnTop = display_height - btnHeight - 25
btnLeft = 150
btnSpace = 3
bkgColor = 100, 100, 100
black = 0, 0, 0
dkRed = 150, 50, 50
ltRed = 250, 0, 0
dkGreen = 50, 150, 50
ltGreen = 0, 250, 0
btnFont = pygame.font.Font("freesansbold.ttf",20)

dbi = 0.3 # debounce interval

def nextImg():
    global img # image used everywhere
    imgList = os.listdir(imgFolder)
    for pic in imgList:
        try:
            imghdr.what(imgFolder + "/" + pic)
            img = pic
            picture = pygame.image.load(imgFolder + "/" + img)
            break
        except:
            # print("directory? " + pic)
            pass
        finally:
            pass
    screen.fill(bkgColor)
    # get dimensions of image
    picWidth = picture.get_width()
    picHeight = picture.get_height()
    if picHeight > btnTop:
        h = btnTop
        w = int(btnTop * picWidth / picHeight)
        picture = pygame.transform.scale(picture, (w,h))
    pictRect = picture.get_rect()
    pictRect.center = ( (display_width/2),(btnTop/2) )
    screen.blit(picture, pictRect)
    titleText = btnFont.render(img + ' (' + str(picWidth) + ' x ' + \
            str(picHeight) + ') ('+str(len(imgList))+')', True, black) # renders img in btnFont
    titleTextRect = titleText.get_rect() # Puts the text in a rect
    titleTextRect.center = (display_width/2,15) # centers the rect on the screen
    screen.blit(titleText, titleTextRect)

def button(msg,x,y,w,h,ic,ac,action=None):
    # msg is text to display on button
    # x,y are top left corner, w,h are width, height of button
    # ic,ac are color of button inactive and active
    btnText = btnFont.render(msg, True, black) # renders the msg in btnFont
    btnTextRect = btnText.get_rect() # Puts the text in a rect
    btnTextRect.center = (x+w/2,y+h/2) # centers the rect in the button
    
    mousePos = pygame.mouse.get_pos() # x,y of mouse
    click = pygame.mouse.get_pressed() # detects mouse click
    
    if x < mousePos[0] < x+w and y < mousePos[1] < y+h: # mouse inside the button
        pygame.draw.rect(screen, ac, (x,y,w,h)) # draw button with active color
        if click[0] == 1 and action != None:
            action()
    else:
        pygame.draw.rect(screen, ic, (x,y,w,h)) # draw button with inactive color
    screen.blit(btnText, btnTextRect) # shows the text

def quitApp():
    # Code to run when Quit button is clicked
    sys.exit()
    waiting = False

def keepImg():
    # Code to run when Keep button is clicked
    print("moving " + img + " to good")
    shutil.move(imgFolder + "/" + img, keepFolder)
    time.sleep(dbi)
    nextImg()
    
def tossImg():
    # Code to run when Toss button is clicked
    print("moving " + img + " to bad")
    shutil.move(imgFolder + "/" + img, tossFolder)
    time.sleep(dbi)
    nextImg()

def deleteImg():
    # Code to run when Delete button is clicked
    print("deleting " + img)
    os.remove(imgFolder + "/" + img)
    time.sleep(dbi)
    nextImg()

### Actual code starts here ###
screen = pygame.display.set_mode(screenSize)
pygame.display.set_caption("Rich's Image Classifier")
clock = pygame.time.Clock()

nextImg()

while waiting:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            waiting = False
            
    button("Keep",btnLeft,btnTop,btnWidth,btnHeight,dkGreen,ltGreen,keepImg)
    button("Toss",btnLeft+btnWidth*btnSpace,btnTop,btnWidth,btnHeight,dkRed,ltRed,tossImg)
    button("Delete",btnLeft+btnWidth*btnSpace*2,btnTop,btnWidth,btnHeight,dkRed,ltRed,deleteImg)
    button("Quit",btnLeft+btnWidth*btnSpace*3,btnTop,btnWidth,btnHeight,dkRed,ltRed,quitApp)
            
    pygame.display.update()
    clock.tick(30)
print("done waiting")
pygame.quit()
quit()
sys.exit()
