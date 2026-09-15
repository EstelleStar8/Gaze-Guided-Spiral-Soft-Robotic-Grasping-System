
# Screen tracking using corner harris detection ================================================

def screenTracking(frame):

    rows = frame.shape[0]
    cols = frame.shape[1]

    x, y, w, h = 2,2,2,2

    # Grey scale
    gframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gframe = np.float32(gframe)

    # Maybe mask out the bottom third of the image to prevent the task bar from being flagged?
    # cv2.rectangle(gframe, (int(rows/3),int(cols/3)), (int(rows/3)+200, int(cols/3)+200), (0, 0, 0), 2)
    #...honestly you don't even need to. Maybe just draw a box around the corners with the furthest XY positions

    # cv2.imshow("fwd_process_preview", gframe)

    # Gaussian blur to reduce noise (lowers accuracy of position but reduces interference effects)
    gframe = cv2.GaussianBlur(gframe, (5,5), 0)

    # Use corner harris to find the 4 corners of the monitor
    blockSize = 5
    sobelSize = 5
    k = 0.05
    harris = cv2.cornerHarris(gframe, blockSize, sobelSize, k)

    ret, harris = cv2.threshold(harris,0.01*harris.max(),255,0)
    harris = np.uint8(harris)

    # find centroids
    ret, labels, stats, centroids = cv2.connectedComponentsWithStats(harris)
    
    # define the criteria to stop and refine the corners
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001)
    corners = cv2.cornerSubPix(gframe,np.float32(centroids),(5,5),(-1,-1),criteria)

    #sobel = cv2.Sobel(gframe, cv2.CV_64F, 1, 1, 2)
    #cv2.imshow("sobel_preview", sobel)

    # Expands out edges of the image
    # harris = cv2.dilate(gframe, None)

    cv2.imshow("corner_preview", harris)

    # Show in blue where the corners are on the raw camera feed
    frame[harris>0.01*harris.max()] = [255, 0 , 0]

    # Find and print points
    points = np.unravel_index(harris.argmax(), harris.shape)
    x = points[0]
    y = points[1]

    cv2.line(frame, ((x + int(w/2)), 0), (x+int(w/2), rows), (82, 150, 92), 2)
    cv2.line(frame, (0, (y + int(h/2))), (cols, y+int(h/2)), (82, 150, 92), 2)

    # Calculate the distance/angle from the screen using known screen size

    return

# == Calibration Through Terminal ================================================================

def calibrationProcedure(debug):

    global doneCalibration

    calibration = 0
    boundingBox = []

    # Variable to store the state of calibration:
    # 2 = undetermined, 1 = procede with calibration, 0 = no calibration
    calibration = 2
    while(calibration == 2):

        # Prompt console input
        userInput = input("Begin Calibration? Y/N: \n")
        try:
            if(userInput == 'Y' or userInput == 'y'):
                print("Calibration Starting\n")
                calibration = 1
            elif(userInput == 'N' or userInput == 'n'):
                print("Calibration Skipped\n")
                calibration = 0
            else:
                print("Invalid Input\n")

        except ValueError:
            print("Invalid Input\n")

    # Run bound collection function to get the maximum XY gaze values
    if(calibration == 1):
        boundingBox = boundCollection(debug)
        doneCalibration = 1;

    return boundingBox

# Helper function for calibration procedure
def boundCollection(debug):

    #Store coordinates for the eye placement of each screen corner
    topRight = [1,0]
    topLeft = [0,0]
    bottomRight = [1,1]
    bottomLeft = [0,1]

    rval, eyeCamFrame = videoCap.read()
    
    while rval:
        # Display raw camera footage (DOES NOT WORK!!!)
        # Either needs to be run on a thread or some other method of non-blocking input needs to be used
        # rval, eyeCamFrame = videoCap.read()
        # cv2.imshow("raw_preview", eyeCamFrame)

        userInput = input("Look at the top right of your screen.\n Press any key to continue: \n").split()
        try:
            # Debug flag for manual input of bounding box
            if(debug):
                for i in userInput:
                    topRight.append(int(i))
            else:
                topRight = eyeTracking(eyeCamFrame)

        except ValueError:
            print("Invalid Input\n")

        userInput = input("Look at the top left of your screen.\n Press any key to continue: \n").split()
        try:
            if(debug):
                for i in userInput:
                    topLeft.append(int(i))
            else:
                topLeft = eyeTracking(eyeCamFrame)

        except ValueError:
            print("Invalid Input\n")

        userInput = input("Look at the bottom right of your screen.\n Press any key to continue: \n").split()
        try:
            if(debug):
                for i in userInput:
                    bottomRight.append(int(i))
            else:
                bottomRight = eyeTracking(eyeCamFrame)

        except ValueError:
            print("Invalid Input\n")

        userInput = input("Look at the bottom left of your screen.\n Press any key to continue: \n").split()
        try:
            if(debug):
                for i in userInput:
                    bottomLeft.append(int(i))
            else:
                bottomLeft = eyeTracking(eyeCamFrame)

        except ValueError:
            print("Invalid Input\n")

        break

    return topRight, topLeft, bottomRight, bottomLeft

# =================================================================================================