from Vision import Vision
from imutils.video import FPS


def foo(message):
    print message.command

if __name__ == '__main__':
    vision = Vision(callback=foo, usePiCamera=False, debug=False)