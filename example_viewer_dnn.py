#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import cv2
from chainer.functions import Convolution2D
from logging import getLogger, DEBUG, INFO, WARNING
import multiprocessing
import numpy as np
import six
import time

import sys
sys.path.append('../image_servers')

import log_initializer

import imgviewer
import dnn

# logging
log_initializer.setFmt()
log_initializer.setRootLevel(WARNING)
logger = getLogger(__name__)
logger.setLevel(DEBUG)
imgviewer.logger.setLevel(INFO)
dnn.logger.setLevel(INFO)


if __name__ == '__main__':
    logger.info('Start')

    # start server
    viewer_queue = multiprocessing.Queue()
    imgviewer.start(viewer_queue, stop_page=True, port=5000)

    dnn.init()

    layer_names = dnn.model.layers
    layer_names.sort()
    for layer_name, _, _ in layer_names:
        if layer_name not in dir(dnn.model):
            continue
        layer = dnn.model[layer_name]
        if isinstance(layer, Convolution2D):
            data = layer.W.data
            assert(data.ndim == 4)

            if data.shape[2] < 3:
                continue

            for i in six.moves.range(data.shape[0]):
                accum = np.zeros_like(data[i, 0])
                for ch in six.moves.range(data.shape[1]):
                    accum += data[i][ch]
                img = np.empty_like(accum)
                cv2.normalize(accum, img, 0, 255, cv2.NORM_MINMAX)

                name = layer_name + str(i)
                width = 50 * img.shape[0] / 3
                viewer_queue.put((layer_name, name,
                                  {'img': img, 'width': width}))

    while True:
        time.sleep(1)