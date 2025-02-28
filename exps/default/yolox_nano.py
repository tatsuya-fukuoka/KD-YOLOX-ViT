#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Copyright (c) Megvii, Inc. and its affiliates.

import os

import torch.nn as nn

from yolox.exp import Exp as MyExp


class Exp(MyExp):
    def __init__(self):
        super(Exp, self).__init__()
        self.depth = 0.33
        self.width = 0.25
        self.input_size = (416, 416)
        self.mosaic_scale = (0.5, 1.5)
        self.random_size = (10, 20)
        self.test_size = (416, 416)
        self.exp_name = os.path.split(os.path.realpath(__file__))[1].split(".")[0]
        self.enable_mixup = False

        # ---------------- YOLOX with ViT Layer ---------------- #
        
        self.vit = False
        
        # ---------------- Knowledge Distillation config ---------------- #
        
        #KD set to True activate add the KD loss to the ground truth loss
        self.KD = True #False
        
        #Teacher model for the Knowledge Distillation
        self.teacher = "yolox_l"
        
        #Path of the weights of the teacher for the Knowledge Distillation
        self.teacher_weights = "./YOLOX_outputs/yolox_l/best_ckpt.pth" #yolox-lで学習した重みを指定
        
        #KD_Online set to False recquires the teacher FPN logits saved to the "folder_KD_directory" folder
        #Then the student training will use the teacher FPN logits
        #Otherwise, if KD_Online set to True the student use the online data augmentation and does not recquire saved teacher FPN logits
        self.KD_online = True #False
        
        #KD_Teacher_Inference set to True save the FPN logits before using offline KD
        
        #folder_KD_directory is the folder where the teacher FPN logits are saved
        self.folder_KD_directory = "KD-FPN-Images/"
        
        if self.KD and not self.KD_online:
             # ---------------- dataloader config ---------------- #

            # To disable multiscale training, set the value to 0.
            self.multiscale_range = 0
               # --------------- transform config ----------------- #
            # prob of applying mosaic aug
            self.mosaic_prob = 0
            # prob of applying mixup aug
            self.mixup_prob = 0
            # prob of applying hsv aug
            self.hsv_prob = 0
            # prob of applying flip aug
            self.flip_prob = 0.0
            # rotation angle range, for example, if set to 2, the true range is (-2, 2)
            self.degrees = 0.0
            # translate range, for example, if set to 0.1, the true range is (-0.1, 0.1)
            self.translate = 0
            self.random_size = (1, 1)
            self.mosaic_scale = (1, 1)
            # apply mixup aug or not
            self.enable_mixup = False
            self.mixup_scale = (1, 1)
            # shear angle range, for example, if set to 2, the true range is (-2, 2)
            self.shear = 0
            
        # Define yourself dataset path
        self.data_dir = "/mnt/datasets/face_yolox_coco/" # 修正

        self.train_ann = "instances_train2017.json"
        self.val_ann = "instances_val2017.json"
        
        self.num_classes = 1 # 修正
        self.max_epoch = 100
        self.eval_interval = 1
        self.save_history_ckpt = False
        
    def get_model(self, sublinear=False):

        def init_yolo(M):
            for m in M.modules():
                if isinstance(m, nn.BatchNorm2d):
                    m.eps = 1e-3
                    m.momentum = 0.03
        if "model" not in self.__dict__:
            from yolox.models import YOLOX, YOLOPAFPN, YOLOXHead
            in_channels = [256, 512, 1024]
            # NANO model use depthwise = True, which is main difference.
            backbone = YOLOPAFPN(self.depth, self.width, in_channels=in_channels, depthwise=True, vit=self.vit)
            head = YOLOXHead(self.num_classes, self.width, in_channels=in_channels, act=self.act, depthwise=True, KD=self.KD, KD_Online=self.KD_online, 
                             folder_KD_directory=self.folder_KD_directory, exp_name=self.exp_name, teacher=self.teacher, teacher_weights=self.teacher_weights)
            self.model = YOLOX(backbone, head)

        self.model.apply(init_yolo)
        self.model.head.initialize_biases(1e-2)
        return self.model
