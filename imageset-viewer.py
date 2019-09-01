#!/usr/bin/env python
# coding:utf-8
# Author: Ashwin Nair
# Date: 2019.9.1 16:30
# Description:
# Annotation visualiser for the Pascal VOC style datasets. This is a modified version
# of Zhuo Zhang's original code which can be found here -> https://github.com/zchrissirhcz/imageset-viewer
# Packages Used：
#     Python, Tkinter(GUI), opencv(image processing), lxml(annotation parsing)
#
# Package requirements:
#     cv2.so/cv2.dll
#     pip install --upgrade image pillow lxml numpy

from __future__ import print_function

try:
    import Tkinter as tk
except:
    import tkinter as tk
from PIL import Image, ImageTk #pillow模块
import os
try:
    from tkFileDialog import askdirectory
except:
    from tkinter.filedialog import askdirectory
import cv2
from lxml import etree
import numpy as np

class PascalVOC2007XML:
    def __init__(self, xml_full_name):
        # todo:校验xml_full_name这个文件的合法性
        self.tree = etree.parse(xml_full_name)
        self.boxes = []

    def get_boxes(self):
        if len(self.boxes) == 0:
            for bbox in self.tree.xpath('//bndbox'):
                pts = bbox.getchildren()
                box = [int(float(_.text)) for _ in pts]
                self.boxes.append(box)
        return self.boxes


class App:
    def __init__(self, master, im_dir=None, show_x=None, show_y=None, box_thick=1):
        # 加载图像：tk不支持直接使用jpg图片。需要Pillow模块进行中转
        """
        @param im_dir: 包含图片的路径，也就是"images". 要求它的同级目录中包含annotations目录，里面包含各种xml文件。
        @param show_x: 图片显示时候的宽度
        @param show_y: 图片显示时的高度
        @param box_thick: 画框的宽度
        """
        self.master = master
        self.show_x = show_x
        self.show_y = show_y
        self.box_thick = box_thick

        self.im_dir = tk.StringVar()
        self.path_entry = tk.Entry(master, text=self.im_dir, width=60, state='readonly')
        self.path_entry.grid(row=0, column=0)

        self.choose_path_btn = tk.Button(master, text='Choose image directory', command=self.selectPath)
        self.choose_path_btn.grid(row=0, column=1)

        ## 设定封面
        self.tkim = self.get_surface_tkim()
        ## 也可以自己搞张图，替代默认的很丑的封面
        #im_name = '/home/chris/Pictures/im/girl2.jpg'
        #self.tkim = ImageTk.PhotoImage(Image.open(im_name))

        self.label1 = tk.Label(master, justify='left',
                          image=self.tkim, compound='center',
                          fg='white', bg='white',
                          width = 1000, height = 1000)
        self.label1.grid(row=1, column=0)

        self.scrollbar = tk.Scrollbar(master, orient=tk.VERTICAL)

        self.listbox = tk.Listbox(master, yscrollcommand=self.scrollbar.set)
        self.listbox.grid(row=1, column=2, sticky=tk.N+tk.S)

        self.im_names = []
        if im_dir is not None:
            self.im_dir.set(im_dir)
            #获取自然顺序的文件列表
            self.im_names = [_ for _ in os.listdir(self.im_dir.get())]
            self.im_names.sort()
            for im_name in self.im_names:
                self.listbox.insert(tk.END, im_name)
        self.listbox.bind('<<ListboxSelect>>', self.callback)
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.grid(row=1, column=3, sticky=tk.N+tk.S)

    def callback(self, event=None):
        im_id = self.listbox.curselection()

        if im_id:
            im_name = self.listbox.get(im_id)
            if (im_name.endswith('.jpg') or im_name.endswith('.png')):
                im_name_full = os.path.join(self.im_dir.get(), im_name).replace('\\', '/')
                self.tkim = self.get_tkim(im_name_full)
                self.label1.configure(image=self.tkim)

    def serial2point(self,box):
        # Input - box = [x1,y1,x2,y2,....]
        # Output - box = [[x1,y1],[x2,y2]....]
        point_list = list(zip(box[::2],box[1::2]))
        return point_list

    def get_tkim(self, im_name_full):
        """
        读取图像并转化为tkim。必要时做resize
        """
        im = cv2.imread(im_name_full)
        print('reading image:', im_name_full)
        im_ht, im_wt, im_dt = im.shape
        show_x = self.show_x
        show_y = self.show_y
        if show_x is None:
            show_x = im_wt
        if show_y is None:
            show_y = im_ht
        if show_x!=im_wt or show_y!=im_ht:
            im = cv2.resize(im, (show_x, show_y))
            print('doing resize!')
            print('show_x={:d}, im_wt={:d}, show_y={:d}, im_ht={:d}'.format(show_x, im_wt, show_y, im_ht))
        scale_x = im_wt*1.0 / show_x
        scale_y = im_ht*1.0 / show_y
        name = os.path.basename(im_name_full)[:-4] # image_name
        anno_name_full = os.path.join(os.path.dirname(os.path.dirname(im_name_full)),'annotations', name + ".xml") #im_name_full.replace('images', 'annotations').replace('.jpg', '.xml').replace('.png', '.xml')
        print('anno_name_full is:', anno_name_full)
        if os.path.exists(anno_name_full):
            print('Xml file exists!')
            boxes = self.get_boxes_from_voc_xml(anno_name_full)
            
            for box in boxes:
                if len(box) !=4:
                    # box represented by set of points [x0,y0,x1,y1,x2,y2,.....]
                    box = self.serial2point(box)
                    box = np.int0(box)
                    cv2.drawContours(im,
                              [box],
                              0,
                              color=(0, 255, 0),
                              thickness=self.box_thick
                              )
                else:
                    # box represented by [x, y, w, h]
                    cv2.rectangle(im,
                        pt1=(int(box[0]/scale_x), int(box[1]/scale_y)),
                        pt2=(int(box[2]/scale_x), int(box[3]/scale_y)),
                        color=(0, 255, 0),
                        thickness=self.box_thick
                        )


        im = im[:, :, ::-1]  #bgr => rgb   necessary
        tkim = ImageTk.PhotoImage(Image.fromarray(im))
        return tkim

    def get_surface_tkim(self):
        """封面图片"""
        im = np.ndarray((500, 700, 3), dtype=np.uint8)

        cv2.putText(im, 'Please choose image set folder',
                    (30, 200),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    color=(255,255,255)
                    )
        im = im[:, :, ::-1]

        tkim = ImageTk.PhotoImage(image=Image.fromarray(im))
        return tkim

    def get_boxes_from_voc_xml(self, anno_name_full):
        # 解析xml文件，获取bbox
        anno = PascalVOC2007XML(anno_name_full)
        boxes = anno.get_boxes()
        return boxes

    def selectPath(self):
        pth = askdirectory()

        #清空listbox中的元素
        self.listbox.delete(0, len(self.im_names)-1)

        self.fill_im_names(pth)

    def fill_im_names(self, im_dir):
        if im_dir is not None:
            self.im_dir.set(im_dir)
            # 获取自然顺序的文件列表
            self.im_names = [_ for _ in os.listdir(im_dir)]
            self.im_names.sort()
            for im_name in self.im_names:
                self.listbox.insert(tk.END, im_name)

# example usage:
if __name__ == '__main__':
    root = tk.Tk()  #创建窗口对象的背景色
    root.title('imageset viewer')
    root.geometry('1400x1400') #设置窗口大小

    ## 最简单的方式：不预设im_dir，打开GUI后自行选择图片路径
    app = App(root, im_dir=None, box_thick=2)

    """
    ## 也可以在代码中指定
    ## eg1: 指定图片路径
    im_dir = '/opt/data/PASCAL_VOC/VOCdevkit2007/TT100/images'
    app = App(root, im_dir)

    ## eg2: 还可以指定显示的图片的长度和宽度，也就是要做图像缩放了。
    app = App(root, im_dir, show_x=1000, show_y=1000)

    ## eg3: 指定画框的宽度
    app = App(root, im_dir, box_thick=2)
    # 或者更多的指定：
    app = App(root, im_dir, show_x=1000, show_y=1000, box_thick=2)
    """

    #进入消息循环
    root.mainloop()
