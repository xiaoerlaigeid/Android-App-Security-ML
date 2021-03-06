# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'wtq'

import time
import threading
from threading import Lock
import json
import os
import requests
from detector.ad.ad_detector_web.task_queue import detector_task, running_detector_task
from detector.ad.core import check_adware_from_config
from detector.ad.permission.predict import AdGaussianPredict
from detector.ad.permission.predict import AdRandomForestPredict
from detector.config import DOWNLOAD_PATH, WEB_PORT, REQUEST_URL, AGENT_ID
from detector.logger import AdDetectorLogger

logger = AdDetectorLogger()


def ad_detector(apkpath):
    """
    调用特征库与分类算法对apk中是否包含广告进行判断
    :param apkpath:
    :return:该apk中包含广告返回yes,反之返回no
    """
    result = check_adware_from_config(apkpath)
    if result:
        return result
    else:
        gauss_predictor = AdGaussianPredict()
        if int(gauss_predictor.predict(apkpath)[0]) == 0:
            return False
        else:
            random_predictor = AdRandomForestPredict()
            if int(random_predictor.predict(apkpath)[0]) == 0:
                return False
            else:
                return True


def detector_server():

    print(threading.current_thread().name + ":" + "server....")

    while True:

        # 扫描任务队列，查找是否有需要处理的任务
        if detector_task.getsize():
            logger.info(threading.current_thread().name + ": " + "the number of task_queue" + str(detector_task.getsize()))

            # ensure getting element from queue is a atom operator
            lock = Lock()
            lock.acquire()
            task_id = detector_task.task_id.get()
            app_name = detector_task.app_name.get()
            web_ip = detector_task.wed_ip.get()
            sign = detector_task.sign.get()
            if not sign:
                port = detector_task.port.get()
                path = detector_task.path.get()
            # 正在运行的任务数量减1
            running_detector_task.pop(task_id)
            lock.release()

            apk_path = os.path.join(DOWNLOAD_PATH, app_name)
            detector_report = {}
            detector_report['apk_name'] = app_name
            # start detecting apk ad
            try:
                detector_report['contain_ad'] = ad_detector(apk_path)
                logger.info(detector_report)
                # 检测完后删除apk
                os.remove(apk_path)
                if sign:
                    r = requests.put("http://" + web_ip + ":" + str(WEB_PORT) + REQUEST_URL
                                 + task_id, data=json.dumps({"agent_id": AGENT_ID, "status": 4,
                                                             "detector_report": detector_report}))
                else:
                    r = requests.put("http://" + web_ip + ":" + str(port) + path
                                     + task_id, data=json.dumps({"agent_id": AGENT_ID, "status": 4,
                                                                 "detector_report": detector_report}))
            # return data to client
            except Exception as e:
                logger.info(e)
                if sign:
                    r = requests.put("http://" + web_ip + ":" + str(WEB_PORT) + REQUEST_URL
                            + task_id, data=json.dumps({"agent_id": AGENT_ID, "status": 0, "detector_report": ""}))
                else:
                     r = requests.put("http://" + web_ip + ":" + str(port) + path
                            + task_id, data=json.dumps({"agent_id": AGENT_ID, "status": 0, "detector_report": ""}))
                os.remove(apk_path)
        else:
            print(threading.current_thread().name + ":" + "没有新任务  " + str(len(running_detector_task))+
                  "正在运行" + "  有" + str(detector_task.getsize()) + "正在等待, 暂停5秒")
        time.sleep(3)

if __name__ == "__main__":
    result1 = {}
    result = ad_detector("/home/wtq/Downloads/jishitianqi.apk")
    print result
    data = json.dumps({"content_ad": result})
    print json.loads(data)["content_ad"]
