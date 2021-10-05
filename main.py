import argparse
import json
import subprocess
import time
import sys
import pkg_resources

import pyrealsense2 as rs
import cv2
import numpy as np
import pysftp

#import help_module
from testingModule import Tester
import threading


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera', default='Pepper', type=str,
                        help='Possible values are RealSense or Pepper')
    parser.add_argument('--connectToPepper', default='True', type=str,
                        help='True if you want Pepper to answer, False for testing purposes from PC')
    parser.add_argument('--isRemote', default='False', type=str,
                        help='True if you want to run the YOLACT part remotely')
    parser.add_argument('--hostname', type=str, default=None)
    parser.add_argument('--username', type=str, default=None)
    parser.add_argument('--password', type=str, default=None)
    parser.add_argument('--speakConstantly', default='False', type=str,
                        help='If true Pepper will say what he sees each 10 seconds')
    parser.add_argument('--process_hidden', type=str, default=None)
    args = parser.parse_args(argv)
    return args

def cleanFile():
    data = {"init" : "true"}
    with open('classes.json', 'w') as f:
        json.dump(data, f)

class MainModule():
    def __init__(self, args):
        self.isFinished = False
        self.cameraFile = "/home/anastasia/server/camera.jpg"
        self.classesFile = "classes.json"
        self.fileRead = 'imageOut.jpg'
        self.sftp = None
        self.args = args
        w = 720
        h = 1280
        self.tester = Tester(args.process_hidden, w, h)

    def frame2image(self, frames):
        align_to = rs.stream.color
        align = rs.align(align_to)
        aligned_frames = align.process(frames)
        color_frame = aligned_frames.get_color_frame()
        color_image = np.asanyarray(color_frame.get_data())
        return color_image[..., ::-1]

    def writeImage(self, pipe):
        frames = pipe.wait_for_frames()
        self.tester.updateFrame(frames)
        im = self.frame2image(frames)
        cv2.imwrite(self.cameraFile, im)

    def showImage(self):
        while True:
            try:
                self.sftp.get(self.fileRead, self.fileRead)
                self.sftp.remove(self.fileRead)
                img = cv2.imread("imageOut.jpg")
                cv2.imshow('img_yolact', img)
                break
            except Exception:
                pass

    def runRemotelyRS(self, pipe, hostname, username, password):
        with pysftp.Connection(hostname, username=username, password=password) as self.sftp:
            with self.sftp.cd('yolact'):
                while not self.isFinished:
                    self.writeImage(pipe)
                    self.sftp.put(self.cameraFile, 'imageIn.jpg')
                    self.showImage()
                    self.sftp.get(self.classesFile, "classes.json")
                    #self.sftp.remove("classes.json")
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.isFinished = True

    def answerQuestions(self):
        while not self.isFinished:
            self.tester.recogniseQuestion()

    def constantlyCheckObjects(self):
        while not self.isFinished:
            self.tester.checkObjects()
            time.sleep(5)

    # TODO: test this function
    def runLocallyRS(self, pipe):
        import help_module
        helper = help_module.Helper()
        frames = pipe.wait_for_frames()
        while not self.isFinished:
            #self.writeImage(pipe)
            frames = pipe.wait_for_frames()
            self.tester.updateFrame(frames)
            im = self.frame2image(frames)
            im = np.array(im, np.int16)
            yolact_im = helper.applyYolact(im)
            cv2.imshow('img_yolact', yolact_im)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def runPepperModule(self):
        subprocess.run("python2 PepYolact.py --speak_constantly=True --realSense=True", shell=True)

    def runPepperModuleCam(self):
        subprocess.run("python2 PepYolact.py --speak_constantly=True --realSense=False", shell=True)

    def get_frame_size(self, frames):
        im = self.frame2image(frames)
        return im.shape[:2]

    def runOnRealSense(self):
        try:
            pipe = rs.pipeline()
            profile = pipe.start()
            frames = pipe.wait_for_frames()
            #print(self.get_frame_size(frames))
            t = None
            if args.connectToPepper == 'True':
                t = threading.Thread(target=self.runPepperModule)
            else:  # for testing purposes
                if args.speakConstantly == 'True':
                    t = threading.Thread(target=self.constantlyCheckObjects)
                else:
                    t = threading.Thread(target=self.answerQuestions)
            t.daemon = True
            t.start()
            if args.isRemote == "True":
                self.runRemotelyRS(pipe, args.hostname, args.username, args.password)
                print("finita la commedia")
                self.tester.clean()
            else:
                self.runLocallyRS(pipe)
                self.tester.clean()
        finally:
            pipe.stop()

if __name__ == '__main__':
    try:
        args = parse_args()
        mainModule = MainModule(args)
        #helper = help_module.Helper()
        if args.camera == "Pepper":
            mainModule.runPepperModule()
        if args.camera == "RealSense":
            mainModule.runOnRealSense()
    except KeyboardInterrupt:
        cleanFile()
        exit()