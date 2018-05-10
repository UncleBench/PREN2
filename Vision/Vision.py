import cv2
import numpy as np
import time
from imutils.video import FPS
from MessageQueue.MessageQueue import Message
from VideoStream import VideoStream
from Target import Target
from multiprocessing import Process


# constants for display output
BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
YELLOW = (0, 255, 255)
ORANGE = (0, 165, 255)
PURPLE = (255, 0, 255)


class Vision(object):
    def __init__(self, callback, usePiCamera=False, debug=False):
        self.stop = False
        self.usePiCamera = usePiCamera
        self.stream = None
        self.debug = debug

        # output
        self.target = None

        self.worker = Process(target=self.capture, name='VisionProcess',
                              args=(callback,))
        self.worker.start()

    def stop_capture(self):
        self.stop = True

    def capture(self, callback):
        # if we're on the Pi, name the process 'Vision'
        if self.usePiCamera:
            from setproctitle import setproctitle
            setproctitle('Vision')

        # FPS counter for debug mode
        if self.debug:
            self.fps = FPS().start()
        self.target = Target()
        self.stream = VideoStream(usePiCamera=self.usePiCamera).start()
        # wait for the camera to initialize
        time.sleep(2.0)
        while True:
            # if self.debug:
            #     print(time.time())

            img = self.stream.read()

            if self.usePiCamera:
                img = cv2.flip(img, 1)

            resized = img[:, 392:904]
            thresh = self.get_thresholded_image(resized)

            # # display threshold image
            # cv2.imshow('Thresholded image', thresh)
            #
            # edge = cv2.Canny(thresh, 50, 200, 3)
            # cv2.imshow('Edge image', edge)

            # find contours
            _, cnts, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE,
                                                  cv2.CHAIN_APPROX_SIMPLE)

            # flatten hierarchy array
            hierarchy = hierarchy[0]

            # get the hierarchy level of every contour and
            # map the two together
            hierarchy_levels = self.get_contour_levels(hierarchy)

            # initialize target contours
            target_cnts = []

            max_level = max(hierarchy_levels)
            # is there a single contour with the highest hierarchy?
            # If there is and it's got a high area and solidity, then
            # it's very likely the contour in the center of the target
            if hierarchy_levels.count(max_level) == 1:
                i = hierarchy_levels.index(max_level)
                if self.are_solidity_and_area_high(cnts[i]):
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
                                if self.are_solidity_and_area_high(cnts[i]):
                                    target_cnts.append(cnts[i])

            # draw the contour
            cv2.drawContours(resized, target_cnts, -1, GREEN, 2)

            x, y = -1, -1
            if target_cnts:
                target_contour = self.find_biggest_contour(target_cnts)
                x, y = self.determine_center(target_contour)

                image_height, _, _ = resized.shape
                if y != -1:
                    self.target.y_ratio = y / float(image_height)
                    if not self.target.found:
                        self.target.found = True
                        callback(Message('target_found', self.target))
                    else:
                        if 0.45 < self.target.y_ratio < 0.55:
                            callback(Message('target_centered', self.target))
                cv2.circle(resized, (x, y), 5, YELLOW, -1)

            # output target coordinates
            self.draw_text(resized, 'Y/target Y: {:4f}'
                           .format(self.target.y_ratio), RED)
            # show solidity and area
            self.draw_solidity_and_area_on_contours(resized, target_cnts)

            # display original image with recognized contours
            cv2.imshow('Contours on original image', resized)

            # esc to quit
            if cv2.waitKey(1) == 27 or self.stop:
                break
            # A to go frame by frame
            # while cv2.waitKey(1) != 65:
            #     k = 0

            if self.debug:
                # update the fps counter
                self.fps.update()
        cv2.destroyAllWindows()
        self.stream.stop()

        if self.debug:
            # stop the timer and display FPS information
            self.fps.stop()
            print("[INFO] elasped time: {:.2f}".format(self.fps.elapsed()))
            print("[INFO] approx. FPS: {:.2f}".format(self.fps.fps()))

    def get_thresholded_image(self, resized):
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

    def are_solidity_and_area_high(self, c):
        area = cv2.contourArea(c)
        solidity_and_area_are_high = False
        if area:
            # compute the convex hull of the contour, then
            # use the area of the original contour and the
            # area of the convex hull to compute the solidity
            hull = cv2.convexHull(c)
            hullArea = cv2.contourArea(hull)
            solidity = area / float(hullArea)

            # filter out small contours with low solidity
            if area > 100 and solidity > 0.95:
                solidity_and_area_are_high = True
        return solidity_and_area_are_high

    def draw_solidity_and_area_on_contours(self, img, contours):
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

    def find_smallest_contour(self, contours):
        # Find the index of the smallest target contour
        areas = [cv2.contourArea(c) for c in contours]
        if len(areas) > 0:
            return contours[np.argmin(areas)]

    def find_biggest_contour(self, contours):
        # Find the index of the biggest target contour
        areas = [cv2.contourArea(c) for c in contours]
        if len(areas) > 0:
            return contours[np.argmax(areas)]

    def get_contour_levels(self, hierarchy):
        contour_levels = []
        for element in hierarchy:
            lvl = 0
            next = element[3]
            while next != -1:
                lvl += 1
                next = hierarchy[next][3]
            contour_levels.append(lvl)
        return contour_levels

    def draw_text(self, img, msg, col):
        h, _, _ = img.shape
        x, y = 10, h - 10
        cv2.putText(img, msg, (x,y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)

    def determine_center(self, contour):
        cx, cy = -1, -1
        m = cv2.moments(contour)
        m00 = m['m00']
        if m00 > 0:
            cx = int(m['m10']/m00)
            cy = int(m['m01']/m00)
        return cx, cy


if __name__ == '__main__':
    vision = Vision()
    vision.capture(mirror=True)