#!/usr/bin/env python3

import sys, pygame, os, shutil, time, imghdr
pygame.init()

# TODO make everything dynamic so it can resize
# buttons based on folders in the imgFolder
# button size and spacing based on number of buttons
# window size based on screen size (or resizable) - Done - UAT

# TODO remove debounce interval and make it work correctly
# review multiple pics at a time???

imgFolder = "/home/pi/Downloads/img"
keepFolder = "/home/pi/Downloads/img/good"
tossFolder = "/home/pi/Downloads/img/bad"

foderCount = 0
badCount = 0
waiting = True

# get some environment info
imgList = os.listdir(imgFolder)
img = imgList[0]

# get folder list
dirList = [] # list of directories in the img folder - used for buttons

for thing in imgList:
    if os.path.isdir(imgFolder + '/' + thing):
        dirList.append(thing)
folderCount = len(dirList)
print("list of folders:")
print(dirList)

dirList = [] # list of directories in the img folder - used for buttons
# make button list as a list of tuples (label,action)
# btnList = []
# for dir in dirList:
#   btnList.append((dirName,dirPath))

btnList = ["Keep", "Toss", "Delete", "Quit"] # use dirList at some point + Delete and Quit
btnCount = len(btnList)

screen_w = pygame.display.Info().current_w
screen_h = pygame.display.Info().current_h
screenDim = screen_w, screen_h # size of the screen (or virtual display)
# print(screenDim)
display_width = screen_w
display_height = screen_h - 70 # 70 pixels for the menu bar
screenSize = display_width, display_height
btnWidth = 100
btnHeight = 50
btnSpace = 3 # number of button widths between buttons - works with hard-coded sizes
btnBarWidth = btnWidth * btnSpace * (btnCount - 1) + btnWidth
btnTop = display_height - btnHeight - 25 # 25 pixels up from the bottom
# btnLeft = 150 # where to start the left-most button
# TODO do some math to put the buttons in the middle - can I use a rect?
btnLeft = (display_width - btnBarWidth)/2
# print("buttons total width: " + str(btnBarWidth))
ltGrey = 100, 100, 100
black = 0, 0, 0
dkRed = 150, 50, 50
ltRed = 250, 0, 0
dkGreen = 50, 150, 50
ltGreen = 0, 250, 0
bkgColor = ltGrey
btnFont = pygame.font.Font("freesansbold.ttf",20)

dbi = 0.3 # debounce interval

def nextImg():
    global img # image used everywhere
    imgList = os.listdir(imgFolder)
    if len(imgList) == folderCount:
        print("no more pics")
        raise SystemExit
    for pic in imgList:
        # TODO add a check for os.path.isfile(imgFolder + '/' + pic)
        try:
            if not os.path.isdir(imgFolder + '/' + pic):
                imghdr.what(imgFolder + "/" + pic)
                img = pic
                picture = pygame.image.load(imgFolder + "/" + img)
                break
        except:
            print("bad file? " + pic)
            os.remove(imgFolder + "/" + pic)
            pass
        finally:
            pass
    screen.fill(bkgColor)
    # get dimensions of image
    picWidth = picture.get_width()
    picHeight = picture.get_height()
    if picHeight > btnTop: # taller than the window minus the buttons
        h = btnTop
        w = int(btnTop * picWidth / picHeight)
        if w > display_width: # still wider than the window
            w = display_width
            h = int(display_width * picHeight / picWidth)
        picture = pygame.transform.scale(picture, (w,h))
    pictRect = picture.get_rect()
    pictRect.center = ( (display_width/2),(btnTop/2) )
    screen.blit(picture, pictRect)
    imgDesc = img + ' (' + str(picWidth) + ' x ' + \
            str(picHeight) + ') ('+str(len(imgList)-folderCount)+')'
    titleText = btnFont.render(imgDesc, True, black) # renders img in btnFont
    titleTextRect = titleText.get_rect() # Puts the text in a rect
    titleTextRect.center = (display_width/2,15) # centers the rect on the screen
    # screen.blit(titleText, titleTextRect)
    pygame.display.set_caption("Rich's Image classifier: " + imgDesc)

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
    # print("moving " + img + " to good")
    shutil.move(imgFolder + "/" + img, keepFolder)
    time.sleep(dbi)
    nextImg()
    
def tossImg():
    # Code to run when Toss button is clicked
    # print("moving " + img + " to bad")
    shutil.move(imgFolder + "/" + img, tossFolder)
    time.sleep(dbi)
    nextImg()

def deleteImg():
    # Code to run when Delete button is clicked
    # print("deleting " + img)
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
            
    # TODO for btn in btnList: # build a button for each item in the list
    # how to get the action from the label???
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
