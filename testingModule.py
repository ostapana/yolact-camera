import argparse
from questionsProcesser import QProcesser
import time


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--speak_constantly', default='False', type=str,
                        help='If true Pepper will say what he sees each 10 seconds')
    args = parser.parse_args(argv)
    return args


class Tester:
    def __init__(self, process_hidden, w, h):
        process_hidden = True if process_hidden == 'True' else False
        self.qProcesser = QProcesser(process_hidden, w, h)

    def recogniseQuestion(self):
        questions = self.qProcesser.questions
        words = input()  # reading question from the terminal
        words = words.lower()
        words = words.split(" ")
        for q in questions:
            if q in words:
                print(self.qProcesser.answerQuestion(questions[q], words))
                break

    def checkObjects(self):
        ret = self.qProcesser.processClasses()
        if not ret is None:
            print(ret)

    def updateFrame(self, frames):
        self.qProcesser.updateFrames(frames)

    def clean(self):
        self.qProcesser.clean()
