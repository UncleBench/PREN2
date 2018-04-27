from Vision import Vision


if __name__ == '__main__':
    vision = Vision(usePiCamera=True)
    vision.capture(mirror=True)