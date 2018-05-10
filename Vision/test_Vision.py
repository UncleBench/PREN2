from Vision import Vision
from imutils.video import FPS


def foo(bar):
    print bar['cmd']

if __name__ == '__main__':
    vision = Vision(callback=foo, usePiCamera=True, debug=False)