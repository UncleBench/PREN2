from Vision import Vision
from imutils.video import FPS


if __name__ == '__main__':
    vision = Vision(usePiCamera=True, debug=True)
    vision.capture()