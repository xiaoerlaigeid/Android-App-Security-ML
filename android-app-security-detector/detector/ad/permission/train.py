# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'wtq'

import os
from datetime import datetime
from androguard.core import androconf
from androguard.core.bytecodes import apk
import numpy
from sklearn.externals import joblib
from base import BasePermission
from detector.config import TRAIN_APK_PATH
from detector.config import TRAIN_PERMISSION
from detector.config import CLASSIFIER_PATH
from detector.config import TRAIN_DESCRIPTION
from detector.config import TRAIN_NAIVEBAYES
from detector.logger import AdDetectorLogger

logger = AdDetectorLogger()


class AdClassifierTrain(BasePermission):

    def get_train_permission(self):
        """
        get train permission and classvec then write to mongo
        :return:
        """

        classvec = []
        permission_list = []
        train_permission = []
        for root, dirs, files in os.walk(TRAIN_APK_PATH, followlinks=True):
            if files:
                for f in files:
                    real_filename = root
                    if real_filename[-1] != "/":
                        real_filename += "/"
                    real_filename += f
                    ret_type = androconf.is_android(real_filename)
                    if ret_type == "APK":

                        try:
                            a = apk.APK(real_filename)
                            if a.is_valid_APK():
                                logger.info(os.path.basename(real_filename))
                                if "notContentAds" in root:
                                    classvec.append(0)
                                else:
                                    classvec.append(1)
                                permission_list.append(self.get_permission_from_apk(a))
                            else:
                                logger.info("it not a real apk")

                        except Exception, e:
                            logger.info(e)
            else:
                logger.info("directory not exists!!!")
        train_permission.append(permission_list)
        train_permission.append(classvec)
        save_train = {
            "train-permission": train_permission,
            "description": "is the train apk permission",
            "create": datetime.now()
        }
        self.session.insert_one(TRAIN_PERMISSION, save_train)

    def train_classifier(self, classifier_algorithm, classifier_name):
        """
        :param clf: the classifier in scikit-learn then write the classifier to disk
        :param session: object of mongo
        :return: the classifier after trained
        """

        clf = classifier_algorithm
        train_permission = self.session.query_sort(TRAIN_PERMISSION, 'create')[0]
        train_permission_list = train_permission[TRAIN_PERMISSION][0]

        class_vector = train_permission[TRAIN_PERMISSION][1]

        stand_permissions = self.get_standard_permission_from_mongodb()
        train_matrix = []

        for permission in train_permission_list:
            train_matrix.append(self.create_permission_vector(stand_permissions, permission))
        # if classifier_name != 'SVM':
        train_matrix = numpy.array(train_matrix)
        class_vector = numpy.array(class_vector)

        clf.fit(train_matrix, class_vector)
        joblib.dump(clf, CLASSIFIER_PATH + classifier_name + ".m")
        save_classifier = {
            'description': TRAIN_DESCRIPTION,
            'algorithm_tag': classifier_name,
            'created_time': datetime.now()
        }
        self.session.insert_one(TRAIN_NAIVEBAYES, save_classifier)
        read_train = self.session.query_sort(TRAIN_NAIVEBAYES, 'created_time')[0]
        train_id = read_train['_id']
        return clf, train_id

    def get_classifier(self, classifier_name):
        """

        :param classifier_name:the classifier that you want get from classifer-model
        :return: the classifier that you trained
        """
        clf = joblib.load(CLASSIFIER_PATH + classifier_name + ".m")
        return clf
