import cv2
import os.path
import json
from copy import copy

from utils.functions import SavePath
from inference_tool import InfTool

fileOut = "imageOut.jpg"
isFinished = False


def writeFile(img_numpy):
    while True:
        if not os.path.isfile("imageOut.jpg"):
            cv2.imwrite("imageOut.jpg", img_numpy)
            print("done")
            break


def assignDirections(class_names, centroids):
    if not centroids:
        return {}
    xCentroids = [row[0] for row in centroids]
    center = max(xCentroids) - min(xCentroids)
    directions = {}
    for i in range(0, len(centroids)):
        if xCentroids[i] < center:
            directions[class_names[i]] = "left"
        else:
            directions[class_names[i]] = "right"
    return directions


def dumpData(data):
    with open('classes.json', 'w') as f:
        try:
            json.dump(data, f)
        except:
            dumpData(data)


def getData():
    with open("classes.json") as f:
        try:
            return json.load(f)
        except:
            return getData()


def assignAndDumpData(init, class_names, class_names_upd,
                      directions, directions_upd):
    data = {'init': init, 'class_names': class_names, 'directions': directions,
            'class_names_upd': class_names_upd,
            'directions_upd': directions_upd}
    dumpData(data)


def firstJsonUpdate(class_names, directions):
    assignAndDumpData("true", class_names,
                      class_names, directions, directions)


def normalJsonUpdate(class_names, directions):
    oldData = getData()
    assignAndDumpData("false", copy(oldData['class_names']), class_names,
                      copy(oldData['directions']), directions)


def updateInfo(class_names, directions):
    data = getData()
    if data["init"] == "true":
        firstJsonUpdate(class_names, directions)
    else:
        normalJsonUpdate(class_names, directions)

'''
def streamPepperCamera():
    subprocess.run(["python2", fileName, '--speak_constantly=True'])
    global isFinished
    isFinished = True
'''

def clean(image):
    os.remove(image)
    data = {"init": "true"}
    dumpData(data)

if __name__ == "__main__":
    weights = "weights/yolact_base_54_800000.pth"
    model_path = SavePath.from_str(weights)
    config = model_path.model_name + '_config'

    cnn = InfTool(weights=weights, config=config, score_threshold=0.35)

    for i in range (0, 1000):
        img = cv2.imread("imageIn.jpg")
        if img is None:
            continue
        else:
            preds, frame = cnn.process_batch(img)
            classes, class_names, scores, boxes, masks, centroids = cnn.raw_inference(img, preds=preds,frame=frame)
            updateInfo(class_names, assignDirections(class_names, centroids))
            img_numpy = cnn.label_image(img, preds=preds)

            writeFile(img_numpy)