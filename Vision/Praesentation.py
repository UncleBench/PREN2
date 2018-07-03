import cv2
import numpy as np
import imutils
import time
from Target import Target

# constants for output
BLUE     = (255, 0, 0)
GREEN   = (0, 255, 0)
RED    = (0, 0, 255)
YELLOW  = (0, 255, 255)
ORANGE  = (0, 165, 255)
PURPLE  = (255, 0, 255)


def show_webcam(mirror=False):
    cam = cv2.VideoCapture(0)
    # cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    # cam.set(cv2.CAP_PROP_FPS, 30)
    target = Target()

    while True:
        # if self.debug:
        #     print(time.time())
        _, img = cam.read()
        if mirror==True:
            img = cv2.flip(img, 1)

        resized = img[:, 392:904]
        thresh = get_thresholded_image(resized)

        # # display threshold image
        cv2.imshow('Thresholded image', thresh)
        #
        edge = cv2.Canny(thresh, 50, 200, 3)
        cv2.imshow('Edge image', edge)

        # find contours
        _, cnts, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,
                                              cv2.CHAIN_APPROX_SIMPLE)

        # flatten hierarchy array
        hierarchy = hierarchy[0]

        # get the hierarchy level of every contour and
        # map the two together
        hierarchy_levels = get_contour_levels(hierarchy)

        # initialize target contours
        target_cnts = []

        max_level = max(hierarchy_levels)
        # is there a single contour with the highest hierarchy?
        if hierarchy_levels.count(max_level) == 1:
            # if there is and it's got a high area and solidity, then
            # it's most likely the contour in the center of the target
            i = hierarchy_levels.index(max_level)
            if are_solidity_and_area_high(cnts[i]):
                if is_reasonably_square(cnts[i]):
                    target_cnts.append(cnts[i])
        else:
            # if there's more than one, we need to filter further
            if hierarchy_levels.count(max_level) > 1:
                i = -1
                for hierarchy_level in hierarchy_levels:
                    i += 1
                    if hierarchy_level == max_level:
                        # filter out contours that don't have 4 corners
                        epsilon = cv2.arcLength(cnts[i], True)
                        approx = cv2.approxPolyDP(cnts[i], 0.01 * epsilon,
                                                  True)
                        if len(approx) == 4:
                            if are_solidity_and_area_high(cnts[i]):
                                if is_reasonably_square(cnts[i]):
                                    target_cnts.append(cnts[i])

        # draw the contour
        cv2.drawContours(resized, target_cnts, -1, GREEN, 2)

        x, y = -1, -1
        # did we find any potential target contours?
        if target_cnts:
            target_contour = find_biggest_contour(target_cnts)
            x, y = determine_center(target_contour)

            image_height, _, _ = resized.shape
            if y != -1:
                target.y_ratio = y / float(image_height)
                if not target.found:
                    target.found = True
                else:
                    if 0.485 < target.y_ratio < 0.525:
                        pass
            cv2.circle(resized, (x, y), 5, YELLOW, -1)
            draw_text(resized, 'Target: {:4f} : {:4f}'.format(x, y), RED)

        # output target coordinates

        # show solidity and area
        #self.draw_solidity_and_area_on_contours(resized, target_cnts)

        # display original image with recognized contours
        cv2.imshow('Contours on original image', resized)

        # esc to quit
        if cv2.waitKey(1) == 27:
            break
        # A to go frame by frame
        # while cv2.waitKey(1) != 65:
        #     k = 0

    cv2.destroyAllWindows()


def get_thresholded_image(resized):
    """Transforms the input image to grayscale, blur it, normalize it,
    runs a combination of adaptive Gaussian threshold and Otsu threshold
    on it, then returns the result as a base for the contour recognition

    Args:
        resized (image): The image to create a threshold image from

    Returns:
        Threshold image
    """
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    norm_image = blurred
    cv2.normalize(norm_image, norm_image, 0, 255, cv2.NORM_MINMAX)
    # find otsu's threshold value with OpenCV function using
    # adaptive gaussian threshold
    ret, thresh = cv2.threshold(norm_image, 0, 255,
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C +
                                cv2.THRESH_OTSU)
    #ret, thresh = cv2.threshold(norm_image, 10, 250, cv2.THRESH_OTSU)
    return thresh

def is_reasonably_square(contour):
    x,y,w,h = cv2.boundingRect(contour)
    aspect_ratio = float(w)/h
    return 0.75 < aspect_ratio < 1.33

def are_solidity_and_area_high(contour):
    """Checks a contour for high area and solidity values

    Args:
        contour (numpy array): The contour to check

    Returns:
        True or False
    """
    area = cv2.contourArea(contour)
    solidity_and_area_are_high = False
    if area:
        # compute the convex hull of the contour, then
        # use the area of the original contour and the
        # area of the convex hull to compute the solidity
        hull = cv2.convexHull(contour)
        hullArea = cv2.contourArea(hull)
        solidity = area / float(hullArea)

        # filter out small contours with low solidity
        if area > 100 and solidity > 0.95:
            solidity_and_area_are_high = True
    return solidity_and_area_are_high

def draw_solidity_and_area_on_contours(img, contours):
    """Draws solidity (blue) and area (red) values of the input contour
    array onto the input image where they are located

    Args:
        img (image): The image the values should be drawn onto
        contours (array<numpy array>): The contours whose values to draw
    """
    for c in contours:
        area = cv2.contourArea(c)
        if area > 0:
            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            solidity = area / float(hull_area)
            cv2.putText(img, '{:2f}'.format(solidity),
                        tuple(c[c[:, :, 0].argmin()][0]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, BLUE, 2)
            cv2.putText(img, '{:f}'.format(area),
                        tuple(c[c[:, :, 0].argmax()][0]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, RED, 2)

def find_smallest_contour(contours):
    """Finds the smallest contour of given contour array

    Args:
        contours (array<numpy array>): Array of contours to search in

    Returns:
        The smallest contour (numpy array)
    """
    # Find the index of the smallest target contour
    areas = [cv2.contourArea(c) for c in contours]
    if len(areas) > 0:
        return contours[np.argmin(areas)]

def find_biggest_contour(contours):
    """Finds the biggest contour of given contour array

    Args:
        contours (array<numpy array>): Array of contours to search in

    Returns:
        The biggest contour (numpy array)
    """
    # Find the index of the biggest target contour
    areas = [cv2.contourArea(c) for c in contours]
    if len(areas) > 0:
        return contours[np.argmax(areas)]

def get_contour_levels(hierarchy):
    """Traverses the tree hierarchy and returns the level of the contours
    contained therein if the contour is enclosed.

    Args:
        hierarchy: Output of cv2.findContours(thresh, cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE).

    Returns:
        Array with the level of every contour with a hierarchy level !=
        -1, which means the contour is not enclosed
    """
    contour_levels = []
    for element in hierarchy:
        lvl = 0
        next = element[3]
        while next != -1:
            lvl += 1
            next = hierarchy[next][3]
        contour_levels.append(lvl)
    return contour_levels

def draw_text(img, msg, col):
    """Draws text in the desired color at (10, 10) onto the input image

    Args:
        img (image): The image to draw onto
        msg (String): The text to draw
        col ((blue, green, red): Color in BGR format
    """
    h, _, _ = img.shape
    x, y = 10, h - 10
    cv2.putText(img, msg, (x,y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)

def determine_center(contour):
    """Finds the center (x, y) of a given contour

    Args:
        contour (numpy array): The contour to determine the center of

    Returns:
        Tuple with x, y values representing the input contour's center
    """
    cx, cy = -1, -1
    m = cv2.moments(contour)
    m00 = m['m00']
    if m00 > 0:
        cx = int(m['m10']/m00)
        cy = int(m['m01']/m00)
    return cx, cy


if __name__ == '__main__':
    show_webcam(mirror=True)