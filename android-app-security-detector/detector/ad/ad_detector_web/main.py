# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'wtq'

import threading
import tornado.ioloop
from detector.ad.ad_detector_web.ad_detector_service import AppWebService
from detector.ad.ad_detector_web.ad_detector import detector_server
from detector.logger import AdDetectorLogger

logger = AdDetectorLogger()


def main():
    """
    将监听客户端请求的handler函数与对广告进行检测的函数分开作为两个独立的线程
    启动，增强了处理性能
    :return:
    """
    logger.info(threading.current_thread().name + ":" + "main running")
    app_web = AppWebService()

    web_service = threading.Thread(target = app_web.start,)

    # heart_beat = threading.Thread(target = app_web.heart_beat, )

    server_thread = threading.Thread(target = detector_server, )

    print ("start...")
    web_service.start()
    # heart_beat.start()
    server_thread.start()


if __name__ == '__main__':
    main()
