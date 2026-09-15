import cv2
import numpy as np
import glob
import pickle

# Camera Calibration methodology and code
# https://www.youtube.com/watch?v=3h7wgR5fYik

# Pickle Storage methodology and code
# https://stackoverflow.com/questions/6568007/how-do-i-save-and-restore-multiple-variables-in-python

# Calibration Documentation
# https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html

# Change for whatever chessboard dimensions we use ((x, y) tiles minus 1)
chessboardSize = (7,7)

# Change for whatever resolution the camera captures in
frameSize = (4628, 3468)

criteria = (cv2.TermCriteria_EPS + cv2.TermCriteria_MAX_ITER, 30, 0.001)

# Object points represent the chess board in real life space
# Whlie image points represent the chess board in a 2D
# The calibration will come from the relationship between these two sets of points

# Setup object point array
objp = np.zeros((chessboardSize[0] * chessboardSize[1], 3), np.float32)
# Confused on this line
objp[:,:2] = np.mgrid[0:chessboardSize[0], 0:chessboardSize[1]].T.reshape(-1, 2)

objPoints = []
imgPoints = []

images = glob.glob('*.png')

for image in images:

    # Convert to greyscale
    img = cv2.imread(image)
    imgGrey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find the corners of the chessboard
    ret, corners = cv2.findChessboardCorners(imgGrey, chessboardSize, None)

    # If chessboard corners are successfully detected
    if ret == True:
        objPoints.append(objp)
        # Refine the image points for accuracy (break the corners into further subpixels)
        corners2 = cv2.cornerSubPix(imgGrey, corners, (11, 11), (-1, -1), criteria)
        imgPoints.append(corners)

        # Image preview of calibrated chess boards
        cv2.drawChessboardCorners(img, chessboardSize, corners2, ret)
        cv2.namedWindow("Corner_Preview", cv2.WINDOW_NORMAL)
        cv2.imshow("Corner_Preview", img)
        cv2.waitKey(1000)

cv2.destroyAllWindows()

# Obtain calibration matrix from gathered data
ret, cameraMatrix, dist, rvecs, tvecs = cv2.calibrateCamera(objPoints, imgPoints, frameSize, None, None)

# dist = Distortion Parameters
# rvecs = Rotation Vectors
# tvecs = Translation Vectors
# cameraMatrix = Camera Matrix

# Note that remapping is faster but less accurate for undistorting images,
# could be a consideration if we have data transfer problems with the pi

# Undistortion ============================================================================

img = cv2.imread('calibration1.png')
h, w = img.shape[:2]
newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, dist, (w,h), 1, (w,h))

# Store parameters for later use (this script only ever needs to run once)
with open('calibration.pkl', 'wb') as f:
    pickle.dump([cameraMatrix, newCameraMatrix, dist, roi], f)

# # Call this in any other script to grab the calibration data
# with open('calibration.pkl', 'rb') as f:
#     cameraMatrix, newCameraMatrix, dist, roi = pickle.load(f)

# Built in undistortion method ==================

dst = cv2.undistort(img, cameraMatrix, dist, None, newCameraMatrix)

# Crop borders out (severe warping not fit for processing)
x, y, w, h = roi
dst = dst[y:y+h, x:x+w]

cv2.imwrite('UndistortedResult1.png', dst)

# Remapping Method  ==============================

mapX, mapY = cv2.initUndistortRectifyMap(cameraMatrix, dist, None, newCameraMatrix, (w,h), 5)
dst = cv2.remap(img, mapX, mapY, cv2.INTER_LINEAR)

# Crop image
x, y, w, h = roi
dst = dst[y:y+h, x:x+w]

cv2.imwrite('UndistortedResult2.png', dst)

# Calculate Calibration Error ====================

mean_error = 0

for i in range(len(objPoints)):
    imgPoints2, __ = cv2.projectPoints(objPoints[i], rvecs[i], tvecs[i], cameraMatrix, dist)
    error = cv2.norm(imgPoints[i], imgPoints2, cv2.NORM_L2)/len(imgPoints2)
    mean_error += error

print("Total error =", mean_error/len(objPoints))


# ==================================================

# I'll be honest this entire function might be useless :(
# It just runs too damn slow for realtime