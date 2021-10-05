import cv2
import os.path
import json
from copy import copy

from yolact.utils.functions import SavePath
from yolact.inference_tool import InfTool

class Helper:
    def __init__(self):
        self.name = "camera.jpg"
        weights = "yolact/weights/yolact_base_54_800000.pth"
        model_path = SavePath.from_str(weights)
        config = model_path.model_name + '_config'

        self.cnn = InfTool(weights=weights, config=config, score_threshold=0.35)

    def assignDirections(self, class_names, centroids):
        if not centroids:
            return {}
        xCentroids = [row[0] for row in centroids]
        try:
            center = max(xCentroids) - min(xCentroids)
        except:
            print("error")
            print(xCentroids)
            center = 600
        directions = {}
        for i in range(0, len(centroids)):
            if xCentroids[i] < center:
                directions[class_names[i]] = "left"
            else:
                directions[class_names[i]] = "right"
        return directions

    def assignCentroids(self, class_names, centroids):
        if not centroids:
            return {}
        assignedCentroids = {}
        for i in range(0, len(centroids)):
            assignedCentroids[class_names[i]] = str(centroids[i])
        return assignedCentroids



    def dumpData(self, data):
        with open('classes.json', 'w') as f:
            try:
                json.dump(data, f)
            except:
                self.dumpData(data)

    def getData(self):
        with open("classes.json") as f:
            try:
                return json.load(f)
            except:
                return self.getData()

    def assignAndDumpData(self, init, class_names, class_names_upd,
                          directions, directions_upd, centroids, centroids_upd):
        data = {'init': init, 'class_names': class_names, 'directions': directions,
                'class_names_upd': class_names_upd,
                'directions_upd': directions_upd,
                'centroids': centroids,
                'centroids_upd': centroids_upd}
        self.dumpData(data)

    def firstJsonUpdate(self, class_names, directions, assigned_centroids):
        self.assignAndDumpData("true", class_names,
                      class_names, directions, directions, assigned_centroids, assigned_centroids)

    def normalJsonUpdate(self, class_names, directions, assigned_centroids):
        oldData = self.getData()
        self.assignAndDumpData("false", copy(oldData['class_names']), class_names,
                          copy(oldData['directions']), directions, copy(oldData['centroids']), assigned_centroids)

    def updateInfo(self, class_names, directions, assigned_centroids):
        data = self.getData()
        if data is None:
            return
        if data["init"] == "true":
            self.firstJsonUpdate(class_names, directions, assigned_centroids)
        else:
            self.normalJsonUpdate(class_names, directions, assigned_centroids)

    def applyYolact(self, img):
        preds, frame = self.cnn.process_batch(img)
        classes, class_names, scores, boxes, masks, centroids = self.cnn.raw_inference(img, preds=preds, frame=frame)
        c = self.assignCentroids(class_names, centroids)
        self.updateInfo(class_names, self.assignDirections(class_names, centroids), self.assignCentroids(class_names, centroids))
        img_numpy = self.cnn.label_image(img, preds=preds)

        #writeFile(img_numpy)
        return img_numpy
