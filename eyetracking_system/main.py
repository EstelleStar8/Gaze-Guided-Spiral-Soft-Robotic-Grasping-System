import cv2
import numpy as np
import pickle
import pyautogui as pyGui
import pygame
import numpy

# Open Video camera 
# https://stackoverflow.com/questions/604749/how-do-i-access-my-webcam-in-python

# Lowkey most of the basic code for thresholding/contours
# https://www.youtube.com/watch?v=kbdbZFT9NQI

# Harris Corner Detection
# https://www.youtube.com/watch?v=1LzJlVUSL5k

# Camera Calibration for getting pixels to real world distance (mostly needed for the forward camera)
# https://stackoverflow.com/questions/14038002/opencv-how-to-calculate-distance-between-camera-and-object-using-image

# Getting openCV to display within pyGame
# https://stackoverflow.com/questions/19240422/display-cv2-videocapture-image-inside-pygame-surface

# screenTracking Function source
# https://stackoverflow.com/questions/60667001/how-to-find-corner-x-y-coordinate-points-on-image-python-opencv

# Window Text display helper function
# https://www.youtube.com/watch?v=ndtFoWWBAoE

# ================ OpenCV Initializers ================================================

cv2.namedWindow("raw_preview")
cv2.namedWindow("process_preview")
cv2.namedWindow("binary_preview")
cv2.namedWindow("image")

# These would be replaced with the camera feed input
videoCap = cv2.VideoCapture(2, cv2.CAP_DSHOW)
#videoCap = cv2.VideoCapture("CapstoneDemo2.mp4")
fwdVideoCap = cv2.VideoCapture("libraryscreenlong.mp4")
#fwdVideoCap = cv2.VideoCapture(2, cv2.CAP_DSHOW)

# ============== PyAutoGUI Initializers ===============================================

# Setting pyGUI parameters
pyGui.FAILSAFE = False
pyGui.PAUSE = 0

# Higher number = less responsive but more stable mouse movement
mouseSmoothing = 10

# ==================== Pygame Initializers ============================================

pyGameWindowSizeX = 1080
pyGameWindowSizeY = 1080

pygame.init()
screen = pygame.display.set_mode((pyGameWindowSizeX, pyGameWindowSizeY))
clock = pygame.time.Clock()
delta_time = 0.1

# Setting the window font
textFont = pygame.font.SysFont("lucidasans", 38, bold = False, italic = False)

# Image class for easier image manipulation
class pyGameImage(pygame.Surface):
    def __init__(self, image, xpos=0, ypos=0, xScale=1, yScale=1):
        self.image = image
        self.xpos = xpos
        self.ypos = ypos
        self.xScale = xScale
        self.yScale = yScale
        self.selected = False
        self.rect = pygame.Rect(xpos, ypos, image.get_width() * xScale, image.get_height() * yScale)

# ====================== Calibration Global Variables =================================

# Flag to mark that calibration is complete
doneCalibration = 0

# Increments for each calibration data point collected
cornerCount = 0

# Send over PI
# ****************************************
# Tracks if head has shifted too drastically from initial position
outOfBounds = 0

# Last valid eye coordinates (Uses to keep mouse position through blinks and when the camera loses the eye)
lastValidPupilCoords = [1,1]
lastValidGlintCoords = [1,1]
# ****************************************


# Variable for incrementing through the circular array (keeps track of the last X mouse positions for stability)
posQueue = 0

# Tracks blinks [Currently unused]
isBlinking = 0

# Tracks if user has been staring at one spot
isFocused = 0
lastGazeVector = [0,0]

# Screen size in cm
screenSizeX = 62
screenSizeY = 35

# Function definition ==============================================================

def eyeTracking(frame, glint):

    rows = frame.shape[0]
    cols = frame.shape[1]

    x, y, w, h = 1,1,1,1

    global lastValidPupilCoords
    global lastValidGlintCoords
    global isBlinking

    # Grey scale
    gframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #cv2.imshow("process_preview", gframe)

    # Cut size of frame
    # gframe = gframe[300: 900, 100: 900]
    
    # Gaussian blur to reduce noise (lowers accuracy of position but reduces interference effects)
    gframe = cv2.GaussianBlur(gframe, (7,7), 0)

    if(not glint):
        # Binary classification of pixels according to brightness values threshold
        # Finding the darkest spot on the image
        __, thresholds = cv2.threshold(gframe, 50, 255, cv2.THRESH_BINARY_INV)
    else:
        # Finding the brightest spot on the image
        __, thresholds = cv2.threshold(gframe, 235, 255, cv2.THRESH_BINARY)

    # Draw and find the contours of the image (edges of B/W)
    contours, __ = cv2.findContours(thresholds, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Sort contours from biggest to smallest
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)

    # Different colours for light and dark sections (mostly for debugging purposes)
    if(not glint):
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # y = y+300
            cv2.drawContours(frame, [cnt], -1, (107, 224, 72), 3)
            cv2.rectangle(frame, (x,y), (x + w, y + h), (240, 100, 72), 2)
            cv2.line(frame, ((x + int(w/2)), 0), (x+int(w/2), rows), (232, 23, 86), 2)
            cv2.line(frame, (0, (y + int(h/2))), (cols, y+int(h/2)), (232, 23, 86), 2)

            break # Only draw the biggest contour
    else:    
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # y = y+300
            cv2.drawContours(frame, [cnt], -1, (235, 42, 212), 3)
            cv2.rectangle(frame, (x,y), (x + w, y + h), (10, 10, 170), 2)
            cv2.line(frame, ((x + int(w/2)), 0), (x+int(w/2), rows), (103, 125, 235), 2)
            cv2.line(frame, (0, (y + int(h/2))), (cols, y+int(h/2)), (103, 125, 235), 2)

            break # Only draw the biggest contour

    # Keep track of the last valid coordinates so the mouse maintains position through blinks and losing track of eye
    if((x+int(w/2) and y+int(h/2)) != 1):
        # Mark if the frame is a blink or not. Used for clicking function.
        isBlinking = 0
        coordinates = [x+int(w/2), y+int(h/2)]

        if(not glint):
            lastValidPupilCoords = coordinates
        else:
            lastValidGlintCoords = coordinates

    else:
        if(not glint):
            # Only check if the pupil is missing (generally this is harder to accidently loose so its a bit more accurate on blinks)
            isBlinking = 1
            coordinates = lastValidPupilCoords
        else:
            coordinates = lastValidGlintCoords

    # Draw a line between the glint and pupil
    cv2.line(frame, lastValidGlintCoords, lastValidPupilCoords, (0, 200, 255), 4)

    # if(not glint):
    #     print("\nPupil position: ", "X:", coordinates[0], "Y:", coordinates[1], end = "\r")
    # else: 
    #     print("\nGlint position: ", "X:", coordinates[0], "Y:", coordinates[1], end = "\r")
    
    cv2.imshow("binary_preview", thresholds)

    return coordinates

def glintPupilVectorPos(vectorQueue):

    # Function that takes the glint vector minus the pupil vector to get the eye position relative to the camera

    global lastValidPupilCoords
    global lastValidGlintCoords
    global posQueue

    avgPositionX = 0
    avgPositionY = 0

    gazeVector = [0,0]

    gazeVector[0] = lastValidPupilCoords[0] - lastValidGlintCoords[0]  
    gazeVector[1] = lastValidPupilCoords[1] - lastValidGlintCoords[1]

    # Update the list of recent mouse positions
    vectorQueue[posQueue] = gazeVector
    posQueue = (posQueue + 1) % len(vectorQueue)

    # Average out the values in the position queue (for stablization)
    for i in range(len(vectorQueue)):
        avgPositionX += vectorQueue[i][0]
        avgPositionY += vectorQueue[i][1]
    
    avgPositionX = avgPositionX/len(vectorQueue)
    avgPositionY = avgPositionY/len(vectorQueue)

    gazeVector = [avgPositionX, avgPositionY]

    # print("Gaze Vector: ", vectorQueue)
    print("Gaze Avg: ", gazeVector, end='\r')

    return gazeVector, vectorQueue

def focusTracking(gazeVector):

    global lastGazeVector
    global isFocused

    isFocused = 0

    if(( abs(gazeVector[0]) - abs(lastGazeVector[0]) < 10) and (abs(gazeVector[1]) - abs(lastGazeVector[1]) < 10)):
        isFocused = 1

    # Update the previous vector for next time the function is called
    lastGazeVector = gazeVector

    return isFocused

def screenTracking(frame, lastScreenArea):

    global cornerCount
    global outOfBounds

    x, y, w, h = 1,1,1,1

    # Grey scale
    gframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gframe = np.float32(gframe)

    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Find distorted bounding rect
    cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    cnts = sorted(cnts, key=lambda x: cv2.contourArea(x), reverse=True)

    for c in cnts:
        # Find distorted bounding rect
        rect = cv2.minAreaRect(c)
        corners = cv2.boxPoints(rect)
        corners = np.int32(corners)
        cv2.fillPoly(mask, [corners], (255,255,255))
        
        # Draw corner points
        corners = corners.tolist()
        # print(corners)
        for corner in corners:
            x, y = corner
            cv2.circle(frame, (x, y), 5, (36,255,12), -1)
        break

    # Front camera warning ==========================================================

    # Corner format: (Top left, Top right, Bottom right, Bottom left)
    # Keep updating until calibration is started
    if(cornerCount == 0):
        topLeft, topRight, botRight, botLeft = corners
        lastScreenArea = (topRight[0] - topLeft[0]) * (botRight[1] - topRight[1])

    # Update current screen area
    screenArea = (corners[1][0] - corners[0][0]) * (corners[2][1] - corners[1][1])
    if(abs(screenArea) - abs(lastScreenArea) > 30):
        outOfBounds = 1
        print("Moved too much")
    else:
        outOfBounds = 0

    # cv2.imshow('thresh', thresh)
    cv2.imshow('image', frame)
    cv2.imshow('mask', mask)

    return corners, lastScreenArea

# For an elementary tracking without angles, maybe map the screen corners to the bounding box
# then move the mouse according to the precentage of the bounding box

def undistortFrame(frame):

    # Get calibration data from pickle file
    with open('calibration.pkl', 'rb') as f:
        cameraMatrix, newCameraMatrix, dist, roi = pickle.load(f)

    print(cameraMatrix)

    x, y, w, h = roi

    # Using remapping for better realtime processing
    mapX, mapY = cv2.initUndistortRectifyMap(cameraMatrix, dist, None, newCameraMatrix, (w,h), 5)
    dst = cv2.remap(frame, mapX, mapY, cv2.INTER_LINEAR)

    # Crop image
    dst = dst[y:y+h, x:x+w]

    return dst

def checkVideoStatus(videoSource):
    
     # Try to get the first frame
    if videoCap.isOpened():
        status, frame = videoSource.read()
    else:
        print("Could not open video source")
        frame = None
        status = False
    
    return status, frame

def printBoundingBox(boundingBox):
    # Print bounding box coordinates
    print("\nBounding box: \nTop right: " + str(boundingBox[0][0]) + " " + str(boundingBox[0][1]) + "\nTop Left: " + 
          str(boundingBox[1][0]) + " " + str(boundingBox[1][1]) + "\n Bottom Right: " + 
          str(boundingBox[2][0]) + " " + str(boundingBox[2][1]) + "\nBottom Left: " + 
          str(boundingBox[3][0]) + " " + str(boundingBox[3][1]) + "\n")
    return

def draw_text(text, font, colour, x, y):

    # The boolean is for smoother edges
    image = font.render(text, True, colour)
    screen.blit(image, (x,y))

    return 0

def draw_calibration_text(coordinates, colour):

    if(cornerCount == 0):
        draw_text("Please look at the top right corner of your screen", textFont, colour, coordinates[0], coordinates[1])
    elif(cornerCount == 1):
        draw_text("Please look at the top left corner of your screen", textFont, colour, coordinates[0], coordinates[1])
    elif(cornerCount == 2):
        draw_text("Please look at the bottom right corner of your screen", textFont, colour, coordinates[0], coordinates[1])
    elif(cornerCount == 3):
        draw_text("Please look at the bottom left corner of your screen", textFont, colour, coordinates[0], coordinates[1])
    else:
        draw_text("Calibration Complete!", textFont, colour, coordinates[0], coordinates[1])  

    return 0

def draw_warning_text(coordinates, colour):

    if(outOfBounds):
                draw_text("Warning: Head is too far from original position\nPlease re-center or recalibrate!",
                        textFont, colour, coordinates[0], coordinates[1])

    return 0

def getCamFrame(frame, screen, coordinates):

    # Colour correction 
    # frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    # if not color:
    #     frame=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    #     frame=cv2.cvtColor(frame,cv2.COLOR_GRAY2RGB)

    # pyGameFrame = cv2.resize(frame, (pyGameWindowSizeX, pyGameWindowSizeY), 0.1, 0.1)

    pyGameFrame = cv2.resize(frame, None, fx = 2, fy = 2, interpolation=cv2.INTER_LINEAR)

    # Rotate the image 90 degrees (k indicates how many rotations)
    pyGameFrame = numpy.rot90(pyGameFrame, k=1)
    pyGameFrame = pygame.surfarray.make_surface(pyGameFrame)

    # Flip the screen along the Y-axis
    pyGameFrame = pygame.transform.flip(pyGameFrame, True, False)

    # Draw camera view onto window
    screen = blitCamFrame(pyGameFrame, screen, coordinates)

    return screen

def blitCamFrame(frame, screen, coordinates):
    screen.blit(frame,(coordinates[0],coordinates[1]))
    return screen

def pyGameCalibration(glintCoords, boundingBox):

    global doneCalibration
    global cornerCount

    keyPressed = 0

    # Checks for all events (button presses and the like)
    events = pygame.event.get()
    
    for event in events:
        # On key press
        if event.type == pygame.KEYDOWN:

            # Press space to register a corner coordinate for the bounding box calibration
            if event.key == pygame.K_SPACE:

                # Collect coordinate data every time space is pressed
                if(cornerCount == 0):
                    # Top right
                    boundingBox[0] = glintCoords
                if(cornerCount == 1):
                    # Top left
                    boundingBox[1] = glintCoords
                if(cornerCount == 2):
                    # Bottom Right
                    boundingBox[2] = glintCoords
                if(cornerCount == 3):
                    # Bottom Left
                    boundingBox[3] = glintCoords

                    # Set calibration to done
                    doneCalibration = 1;
                
                # Flash screen colour when calibration point taken
                if(doneCalibration == 0):
                    screen.fill((0,255,255))
                    keyPressed = 1
                cornerCount += 1
                #print(glintCoords)
        
    # Basically clears the screen every frame so you don't get bleeding images
    if(cornerCount > 3):
        screen.fill((0,0,255))
    elif(keyPressed == 0):
        screen.fill((255,0,255))

    #printBoundingBox(boundingBox)

    # Return event so that event polling is not repeated throughout the pyGame functions
    return boundingBox, events

def pyGameClickLoop(isClick, startTicks):

    global isBlinking
    global isFocused

    # Get time since the start of the blink
    seconds = (pygame.time.get_ticks() - startTicks)/1000

    # While the blink is ongoing (so that the click doesn't register before user opens eyes)
    if(isFocused == 1 and isClick == 0):
        startTicks = pygame.time.get_ticks()
        seconds = 0
        # print("We be blinking\n")
        isClick = 1;
        
    # Closed eye state
    if(isClick == 1):
        # Do nothing if open eyes too soon
        if(isFocused == 0):
            isClick = 0
            # print("Opened eyes too soon\n")

        # Single click if closed for 1 second
        if(isFocused == 1 and seconds > 1):
            isClick = 2
            print("Left click toggle\n")
        
    if(isClick == 2):
        # Double click if closed for 2 seconds
        if(isFocused == 1 and seconds > 2):
            isClick = 3
            print("Double Click Toggle\n")
 
    # On eye open
    if(isFocused == 0 and isClick == 2):
        print("Left click\n")
        pyGui.leftClick()
        isClick = 0

    if(isFocused == 0 and isClick == 3):
        print("Left double click\n")
        #pyGui.doubleleftClick()
        isClick = 0

    return isClick, startTicks

def draw_window_buttons(event, imageList, quit):

    global cornerCount
    global doneCalibration

    cButtonImage = imageList[0]
    qButtonImage = imageList[2]
    
    screen.blit(imageList[1], (cButtonImage.xpos, cButtonImage.ypos))
    screen.blit(imageList[3], (qButtonImage.xpos, qButtonImage.ypos))

    for events in event:
        # On event click
        if events.type == pygame.MOUSEBUTTONDOWN:

            # If the mouse is hovering calibration button (this is a placeholder check idk how to do it)
            if(mouse_hover(cButtonImage)):
                cornerCount = 0
                doneCalibration = 0

            # If the mouse is hovering quit button (this is a placeholder check idk how to do it)
            if(mouse_hover(qButtonImage)):
                quit = 1

    return quit

def mouse_hover(object):

    mousePos = pygame.mouse.get_pos()

    if(object.rect.collidepoint(mousePos)):
        object.selected = True 
        return 1
    else:
        object.selected = False
        return 0
    
def drawBG(imageList):

    # Draw white background
    whiteBG = imageList[4]
    screen.blit(imageList[5], (whiteBG.xpos, whiteBG.ypos))

    return 0

def pyGameRender(frame, event, imageList, quit):

    global delta_time

    # Normalize time to not be dependant on framerate
    delta_time = clock.tick(30)
    delta_time = max(0.001, min(0.1, delta_time))

    # Draw background elements
    drawBG(imageList)

    # Draws camera view onto pyGame, coordinates of view can be input here
    getCamFrame(frame, screen, (0,0))

    # Handles the text that shows up for each stage of calibration ((X,Y), (R,G,B))
    draw_calibration_text((50,650), (0,0,80))

    # Handles text for when head is not in proper position
    draw_warning_text((50,900), (0,0,80))

    # Handles the button drawing and function for clicking the button
    quit = draw_window_buttons(event, imageList, quit)

    # Actually draws the frame update for pyGame
    pygame.display.flip()

    return quit


def getScreenSize():

    # Does what you think it does
    width, height = pyGui.size()

    return width, height

def gazeToPixels(eyeCoords, boundingBox):

    # I believe you'll need a mid point as well for the calibration (but that's for later)
    mouseCoords = [70,100]
    xMoveRatio = 0
    yMoveRatio = 0

    # Check if bounding box has values in it
    if(boundingBox):

        # printBoundingBox(boundingBox)

        # Take the average x distance of the top edges
        xRange = ((boundingBox[0][0] - boundingBox[1][0]) + (boundingBox[2][0] - boundingBox[3][0]))/2.0
        yRange = ((boundingBox[2][1]- boundingBox[0][1]) + (boundingBox[3][1]- boundingBox[1][1]))/2.0

        sWidth, sHeight = getScreenSize()

        xMoveRatio = (sWidth)/xRange
        yMoveRatio = (sHeight)/yRange

        # Shift the eyeCoords by the lower bound
        eyeCoords = [eyeCoords[0] - ((boundingBox[1][0] + boundingBox[3][0])/2), 
                    eyeCoords[1] - ((boundingBox[0][1] + boundingBox[1][1])/2)]
        
        # Multiply by the ratio between the bounding box and screen size
        mouseCoords = [eyeCoords[0]*xMoveRatio, eyeCoords[1]*yMoveRatio]

        # Do focus check here
        focusTracking(mouseCoords)

        # print("\nMouse position: ", "X:", int(mouseCoords[0]), "Y:", int(mouseCoords[1]), end = "\r")

    return mouseCoords

def imageInit(image, x, y, scaleX, scaleY):
    
    # Initialize Calibration button class
    objectImage = pyGameImage(image, x, y, 
                               scaleX, scaleY)
    
    # Adjust button size
    scaledObjectImage = pygame.transform.scale(objectImage.image, 
                                            (objectImage.image.get_width() * objectImage.xScale,
                                            objectImage.image.get_height() * objectImage.yScale))

    return objectImage, scaledObjectImage

def pyGameInit():

    imageList = []

    # Load in pyGame assets
    calibrateButton = pygame.image.load('CalibrationButton.png').convert()
    quitButton = pygame.image.load('QuitButton.png').convert()
    whiteBg = pygame.image.load('WhiteSquare.png').convert()

    # Parameters: Image, Xpos, Ypos, Xscale, Yscale
    cButtonImage, scaledcalibrateButton = imageInit(calibrateButton, 150, 750, 0.16, 0.16)
    qButtonImage, scaledquitButton = imageInit(quitButton, 550, 750, 0.16, 0.16)
    whiteBgImage, scaledWhite = imageInit(whiteBg, 0, 600, 1, 1)

    # Append all to image list
    imageList.append(cButtonImage)
    imageList.append(scaledcalibrateButton)

    imageList.append(qButtonImage)
    imageList.append(scaledquitButton)

    imageList.append(whiteBgImage)
    imageList.append(scaledWhite)

    return imageList

# Main processing loop ========================================================

def main ():

    # Debug is calibrationProcedure(1) [Manually inputting coords]
    # boundingBox = calibrationProcedure(1)

    boundingBox = [[10,10], [10,10], [10,10], [10,10]]

    # Defualt positions 
    mouseCoords = [40, 40]
    screenCoords = [[1,1], [1,1], [1,1], [1,1]]
    lastScreenArea = 0

    # Queue for storing previous mouse positions
    mouseQueue = [[10,10], [10,10], [10,10], [10,10]]
    mouseQueue = np.zeros((mouseSmoothing, 2))

    # Variables to handle clicking function
    clickFlag = 0
    timer = 0

    # Camera feed
    rval, eyeCamFrame = checkVideoStatus(videoCap)
    rval2, fwdCamFrame = checkVideoStatus(fwdVideoCap)

    # Intialization of UI sprites
    imageList = pyGameInit()

    quit = 0

    global screen

    # printBoundingBox(boundingBox)

    while rval and rval2:

        # Display raw camera footage
        cv2.imshow("raw_preview", eyeCamFrame)
        rval, eyeCamFrame = videoCap.read()
        
        #cv2.imshow("alt preview", fwdCamFrame)
        rval2, fwdCamFrame = fwdVideoCap.read()

        # Slow but these are functions to remove camera distortion
        #undistortFrame(eyeCamFrame)
        #undistortFrame(fwdCamFrame)

        # Shrink frames for less processing load
        eyeCamFrame = cv2.resize(eyeCamFrame, (320, 240))

        # The second parameter indicates whether to track lights or darks, 0 for dark 1 for light.
        eyeDarkCoords = eyeTracking(eyeCamFrame, 1)

        # Call eye tracking function
        eyeLightCoords = eyeTracking(eyeCamFrame, 0)

        # Call to find vector between glint and pupil
        eyeVectorCoords, mouseQueue = glintPupilVectorPos(mouseQueue)

    # Send to laptop ========================================================
        # Move mouse to location
        if(doneCalibration == 1):

            # Hard coding bounding box for debugging
            #boundingBox = [[95, -260], [-245, -325], [105, -115], [-155, -230]]
            mouseCoords = gazeToPixels(eyeVectorCoords, boundingBox)
            pyGui.moveTo(mouseCoords[0], mouseCoords[1])
            clickFlag, timer = pyGameClickLoop(clickFlag, timer)
    # ========================================================================

        # Call screen tracking function
        screenCoords, lastScreenArea = screenTracking(fwdCamFrame, lastScreenArea)

    # Send to laptop ============================================================
        # Handles the calibration system for the game loop
        # Also fills background for pygame
        boundingBox, event = pyGameCalibration(eyeVectorCoords, boundingBox)
    # ===========================================================================

        # Renders the UI depending on system state
        quit = pyGameRender(eyeCamFrame, event, imageList, quit)

        key = cv2.waitKey(20)
        if key == 27 or quit: # exit on ESC
            break

    return

# Call Main =============
main()

# Cleanup ======================================================================

# Destroy all created windows
videoCap.release()
cv2.destroyWindow("raw_preview")
cv2.destroyWindow("process_preview")
cv2.destroyWindow("binary_preview")
cv2.destroyWindow("image")

# Current Issues =========================================================
'''
~~~~~~~~~ Corner detection picks up taskbar icons ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By using the corner tracking algorithm to pickup the screen, you run into the issue
of picking up any image with corners on the monitor. Which will happen a lot. 

The most obvious exmaple of this are the square taskbar icons on the bottom of your 
screen at all times.

~~~~~~~~~ Otsu threshold monitor detection requires white outline ~~~~~~~~~

If the screen is displaying a dark image/program, the monitor detection fails.

I think the most graceful fix is requiring white stickers along the edge of the monitor


~~~~~~~~ Program crash on losing all contours (Potentially fixed?) ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When no contours are detected the program exits the check that sets the eye coordinates,
particularly setting the x,y,h,w values to null, which crashes the program.

These values should actually save inbetween loops, this will save their position in the case
of a blink (which one has to imagine happens alot) or just losing the tracking for a breif 
moment.

'''
# Current gameplan =======================================================
'''

# Staring detection. Has user moved in X amount of time from the mouse spot?
# Use for calibration. Use for clicking because blink detection is so messy.


Implement the screen detector movement thingy.... yeah
- Warn the user when they have moved their head too far from the original calibration position
- Probably compare the value of corners to the value of them when calibration was completed
- What is the calibration value....... that can be a lot of things
- Average during the process?
- Maybe the moment you take the first corner you take the values then give x amount of wiggle room
- I like this.

Make a UI that isn't a MS paint doodle
- Recalibrate button
- Exit button

'''