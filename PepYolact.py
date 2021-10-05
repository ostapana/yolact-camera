import argparse
import time
import cv2

from pepper_controller.pepper.robot import Pepper
from questionsProcesser import QProcesser

class PepYolact:
    def __init__(self, ip):
        self.robot = Pepper(ip)
        #self.robot.set_english_language()
        #self.robot.autonomous_life_off()
        #self.robot.move_head_default()
        self.qProcesser = QProcesser()
        self.isFinished = False

    def recogniseQuestion(self):
        questions = self.qProcesser.questions
        while not self.isFinished:
            #self.robot.set_english_language()
            try:
                self.robot.blink_eyes([255, 255, 0])
                words = self.robot.recordSound()
                self.robot.blink_eyes([0, 0, 0])
            except:
                continue
            if words is None:
                # robot.say("I don't understand you, human")
                continue
            print("Pepper has recognised " + words)
            words = words.lower()
            words = words.split(" ")
            for q in questions:
                if q in words:
                    answer = self.qProcesser.answerQuestion(questions[q], words)
                    self.robot.say(answer, bodylanguage='disabled')
                    break
            time.sleep(2)

    def constantlyCheckObjects(self):
        while not self.isFinished:
            result = self.qProcesser.processClasses()
            if not result is None:
                self.robot.say(result, bodylanguage='disabled')
            time.sleep(4)

    def camera_stream(self):
        self.robot.subscribe_camera("camera_top", 2, 30)
        while True:
            image = self.robot.get_camera_frame(show=False)
            cv2.imshow("frame", image)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            im = Image.fromarray(image)
            im.save("camera.jpg")
        self.robot.unsubscribe_camera()
        cv2.destroyAllWindows()
        self.isFinished = True


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--speak_constantly', default='False', type=str,
                        help='If true Pepper will say what he sees each 10 seconds')
    parser.add_argument('--realSense', default='False', type=str)
    args = parser.parse_args(argv)
    return args

if __name__ == "__main__":
    pepYolact = PepYolact("192.168.0.102")
    args = parse_args()
    if args.speak_constantly == 'True':
        pepYolact.constantlyCheckObjects()
    else:
        pepYolact.recogniseQuestion()

    if args.realSense == 'True':
        t = threading.Thread(target=pepYolact.camera_stream())
        t.start()
