import json


class QProcesser:
    def __init__(self, prc_hid_classes, w, h):
        self.questions = {"where": 0, "add": 1, "added": 1, "edit": 1, "new": 1,
                          "remove": 2, "take": 2, "took": 2, "removed": 2,
                          "taken": 2, "see": 3, "seen": 3, "seem": 3,
                          "change": 4, "changed": 4, "changes": 4,
                          "predict": 5}
        self.frames = None
        self.prc_classes = prc_hid_classes
        self.removed_objects = {}
        self.w = w
        self.h = h

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
            except Exception as e:
                return self.getData()

    def updateFrames(self, frames):
        self.frames = frames

    def extract_centroids(self, centroids):
        centroids = centroids[1:len(centroids) - 1]
        centroids = centroids.split()
        x = int(float(centroids[0]))  # string to float then to int
        y = int(float(centroids[1]))
        return x, y

    def extractDepth(self, coordinates, class_names):
        for name in class_names:
            x, y = self.extract_centroids(coordinates[name])
            depth = self.frames.get_depth_frame()
            dist = depth.get_distance(round(x), round(y))
            print("Depth of " + name + " is " + str(dist))

    def analyzeWhere(self, question):
        data = self.getData()
        availableClasses = data["class_names_upd"]
        directions = data["directions_upd"]
        classesToName = []
        for w in question:
            if w in availableClasses:
                classesToName.append(w)
            elif w[:-1] in availableClasses:  # case of multiple objects like chairS
                classesToName.append(w[:-1])
        retString = ""
        if classesToName == []:
            retString += "I do not know"
        for c_name in classesToName:
            retString += c_name + " is on the " + directions[c_name]
        return retString

    def answerQuestion(self, q_code, question):
        data = self.getData()
        try:
            class_names = data["class_names"]
            directions = data["directions"]
        except:
            return
        retString = ""
        if q_code == 0:
            retString = self.analyzeWhere(question)
        elif q_code == 1 or q_code == 2:
            self.compareImages(data, isQuesion=True, c_code=q_code)
            self.updateJson(data["class_names_upd"], data["directions_upd"])
        elif q_code == 3:
            countedObjects = self.countObjects(class_names)
            retString += "I see " + self.firstNameClasses(countedObjects, directions)
            self.updateJson(data["class_names_upd"], data["directions_upd"])
            return retString
        elif q_code == 4:
            self.compareImages(data, isQuesion=True, c_code=0)
            self.updateJson(data["class_names_upd"], data["directions_upd"])
        elif q_code == 5:
            name = None
            for w in question:
                if w in data["class_names_upd"]:
                    name = w
                    break
            self.make_prediction(data['centroids'], data['centroids_upd'], name)
        return retString

    def nameClasses(self, name, count, direction, dirP):
        retString = ""
        retString += str(count) + " "
        word = name if count == 1 else name + "s"
        retString += word + " " + dirP + direction + " "
        return retString

    def firstNameClasses(self, countedObjects, directions):
        retString = ""
        for name in countedObjects.keys():
            count = countedObjects[name]
            direction = directions[name]
            retString += self.nameClasses(name, count, direction, "on the ")
        return retString

    # process classes which are put into box or behind it
    def process_hid_classes(self):
        # if the object was somewhere in the middle of the frame when it's last seen
        # it was probably hidden into a box, otherwise it's just gone
        # TODO: count num of frames in which the object was missing if > 10 then check if hidden
        # also add if there is a box?
        x_border = (self.w / 100) * 10  # 10% of width
        y_up_border = (self.h / 100) * 10
        y_down_border = (self.h / 100) * 30
        for name in self.removed_objects:
            #name = name[0:len(name) - 1]
            x, y = self.extract_centroids(self.removed_objects[name][1])
            if x > x_border or x < (self.w - x_border) or \
                    y > y_up_border or y < (self.h - y_down_border) and \
                    self.removed_objects[name][1] > 10:
                print(name + " is probably hidden into a box")

    def updateJson(self, class_names, directions, centroids):
        newData = self.getData()
        data = {'init': 'false', 'class_names': class_names, 'directions': directions,
                'class_names_upd': newData["class_names_upd"],
                'directions_upd': newData["directions_upd"],
                'centroids': centroids, 'centroids_upd': newData['centroids_upd']}
        self.dumpData(data)

    # check on how many frames the object is hidden
    def check_hid_per_frame(self, class_names):
        for r in self.removed_objects:
            if r in class_names:
                self.removed_objects.pop(r)
            else:
                self.removed_objects[r][0] += 1

    def getChanges(self, oldClasses, newClasses):
        return list(set(newClasses) - set(oldClasses)), \
               list(set(oldClasses) - set(newClasses))

    def announce(self, changedClasses, countFirstStrings,
                 countSecondStrings, directions, dirP, phrase):
        phraseFlag = 0
        retString = ""
        for c in changedClasses:
            firstPair = countFirstStrings[c]
            flag = 0
            for secondPair in countSecondStrings.values():
                if secondPair[0] == firstPair[0]:
                    flag = 1
                    count = firstPair[1] - secondPair[1]
                    if count > 0:
                        if phraseFlag == 0:
                            phraseFlag = 1
                            retString = phrase + " "
                        name = firstPair[0]
                        retString += self.nameClasses(name, count, directions[name], dirP) + " "
            if flag == 0:
                if phraseFlag == 0:
                    phraseFlag = 1
                    retString += phrase
                name = firstPair[0]
                count = firstPair[1]
                retString += self.nameClasses(name, count, directions[name], dirP)
        return retString

    def upd_removed_obj(self, deleted_classes, centroids):
        for d in deleted_classes:
            d = d[0: len(d)-1]
            self.removed_objects[d] = [1, centroids[d]]
        print(self.removed_objects)

    def announceChanges(self, countNewStrings, countOldStrings,
                        addedClasses, deletedClasses, oldDirections,
                        newDirections, centroids):
        retString = ""
        if not len(addedClasses) == 0:
            retString += self.announce(addedClasses, countNewStrings, countOldStrings,
                                       newDirections, "on the ", "You have added ") + " "

        if not len(deletedClasses) == 0:
            retString += self.announce(deletedClasses, countOldStrings, countNewStrings,
                                       oldDirections, "from the ", "You have removed ")
            #if self.prc_classes:
                #self.upd_removed_obj(deletedClasses, centroids)

        return retString

    def compareImages(self, data, isQuesion, c_code):
        oldClasses = data["class_names"]
        newClasses = data["class_names_upd"]
        countedOld = self.countObjects(oldClasses)
        countedNew = self.countObjects(newClasses)
        countOldStrings = {i + str(countedOld[i]): (i, countedOld[i]) for i in countedOld.keys()}
        countNewStrings = {i + str(countedNew[i]): (i, countedNew[i]) for i in countedNew.keys()}
        addedClasses, deletedClasses = self.getChanges(countOldStrings.keys(), countNewStrings.keys())
        if c_code == 1:
            deletedClasses = []
        elif c_code == 2:
            addedClasses = []
        if isQuesion and (len(addedClasses) == len(deletedClasses) == 0):
            retString = "I see no changes"
            return retString
        return self.announceChanges(countNewStrings, countOldStrings, addedClasses,
                                    deletedClasses, data["directions"], data["directions_upd"], data['centroids'])

    def countObjects(self, class_names):
        return {i: class_names.count(i) for i in class_names}

    def make_prediction(self, coordinates, coordinates_upd, name):
        x1, y1 = self.extract_centroids(coordinates[name])
        x2, y2 = self.extract_centroids(coordinates_upd[name])
        x = (x1 + x2) / 2
        y = (y1 + y2) / 2
        print(name + " should be at " + str(x) + " " + str(y))

    def processClasses(self):
        retString = ""
        data = self.getData()
        try:  # we need this if working on server
            class_names = data["class_names"]
            directions = data["directions"]
            coordinates = data['centroids']
            self.extractDepth(coordinates, class_names)
            #if self.prc_classes:
                #self.check_hid_per_frame(class_names)
        except:
            return
        countedObjects = self.countObjects(class_names)
        if data["init"] == "true":
            if len(countedObjects) == 0:
                return
            data["init"] = "false"
            self.dumpData(data)
            retString += "Let's start! I see " + \
                         self.firstNameClasses(countedObjects, directions)
        else:
            retString += self.compareImages(data, isQuesion=False, c_code=0)
            self.updateJson(data["class_names_upd"], data["directions_upd"], data["centroids_upd"])
            #if self.prc_classes:
                #self.process_hid_classes()
        return retString

    def clean(self):
        data = {"init": "true"}
        self.dumpData(data)
