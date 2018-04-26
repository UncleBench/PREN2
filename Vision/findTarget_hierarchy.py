import cv2
import numpy as np
import imutils

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

    while True:
        ret_val, img = cam.read()
        if mirror:
            img = cv2.flip(img, 1)

        resized = img[:, 384:896]
        thresh = get_thresholded_image(resized)

        # display threshold image
        cv2.imshow('Thresholded image', thresh)

        edge = cv2.Canny(thresh, 50, 200, 3)
        cv2.imshow('Edge image', edge)

        # find contours
        _, cnts, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # flatten hierarchy array
        hierarchy = hierarchy[0]

        # get the hierarchy level of every contour and map the two together
        hierarchy_levels = get_contour_levels(hierarchy)

        target_cnts = []

        if hierarchy_levels.count(max(hierarchy_levels)) == 1:
            i = hierarchy_levels.index(max(hierarchy_levels))
            add_contour_if_solidity_and_area_are_high(cnts[i], target_cnts)
        else:
            i = -1
            for hierarchy_level in hierarchy_levels:
                i += 1
                if hierarchy_level > 0:
                    add_contour_if_search_pattern_matches(cnts[i], target_cnts)

        cv2.drawContours(resized, target_cnts, -1, GREEN, 2)

        x, y = 0, 0
        if target_cnts:
            smallest_contour = find_smallest_contour(target_cnts)
            x, y = determine_center(smallest_contour)
            cv2.circle(resized, (x, y), 5, YELLOW, -1)

        # output target coordinates
        draw_text(resized, 'Target: {:4d}, {:4d}'.format(x, y), RED)

        draw_solidity_and_area_on_contours(resized, target_cnts)

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
    # Crop image to 720:720, resize to 512:512
    # resized = cv2.resize(img[:, 280:1000], (512, 512))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    norm_image = blurred
    cv2.normalize(norm_image, norm_image, 0, 255, cv2.NORM_MINMAX)
    # find otsu's threshold value with OpenCV function using adaptive gaussian threshold
    ret, thresh = cv2.threshold(norm_image, 0, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C + cv2.THRESH_OTSU)
    #ret, thresh = cv2.threshold(norm_image, 10, 250, cv2.THRESH_OTSU)
    return thresh


def add_contour_if_search_pattern_matches(c, target_cnts):
        epsilon = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * epsilon, True)

        # filter out contours that don't have 4 corners
        if len(approx) == 4:
            add_contour_if_solidity_and_area_are_high(c, target_cnts)


def add_contour_if_solidity_and_area_are_high(c, target_cnts):
    area = cv2.contourArea(c)
    if area:
        # (x, y, w, h) = cv2.boundingRect(c)
        #
        # # compute the aspect ratio of the contour, which is simply the width divided by the height of the bounding box
        # aspectRatio = w / float(h)
        #
        # # use the area of the contour and the bounding box area to compute the extent
        # extent = area / float(w * h)

        # compute the convex hull of the contour, then use the area of the original contour and the area of the convex hull to compute the solidity
        hull = cv2.convexHull(c)
        hullArea = cv2.contourArea(hull)
        solidity = area / float(hullArea)

        # filter out contours that don't have the propper shape
        if area > 100 and solidity > 0.95:
            target_cnts.append(c)


def draw_solidity_and_area_on_contours(img, contours):
    for c in contours:
        area = cv2.contourArea(c)
        if area > 0:
            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            solidity = area / float(hull_area)
            cv2.putText(img, '{:2f}'.format(solidity), tuple(c[c[:, :, 0].argmin()][0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        BLUE, 2)
            cv2.putText(img, '{:f}'.format(area), tuple(c[c[:, :, 0].argmax()][0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        RED, 2)


def find_smallest_contour(contours):
    # Find the index of the smallest target contour
    areas = [cv2.contourArea(c) for c in contours]
    if len(areas) > 0:
        min_index = np.argmin(areas)
        return contours[min_index]


def get_contour_levels(hierarchy):
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
    h, _, _ = img.shape
    x, y = 10, h - 10
    cv2.putText(img, msg, (x,y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)


def determine_center(contour):
    cx, cy = -1, -1
    m = cv2.moments(contour)
    m00 = m['m00']
    if m00 > 0:
        cx = int(m['m10']/m00)
        cy = int(m['m01']/m00)
    return cx, cy


if __name__ == '__main__':
    show_webcam(mirror=True)