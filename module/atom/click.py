# @author runhey
# github https://github.com/runhey

import numpy as np


class RuleClick:
    def __init__(self, roi_front: tuple, roi_back: tuple, name: str | None = None) -> None:
        """
        初始化
        :param roi_front:
        :param roi_back:
        """
        self.roi_front = roi_front
        self.roi_back = roi_back
        if name:
            self.name = name
        else:
            self.name = "click"

    def coord(self) -> tuple[int, int]:
        """
        获取坐标, 从roi_front随机获取坐标
        :return:
        """
        x, y, w, h = self.roi_front
        x = np.random.randint(x, x + w)
        y = np.random.randint(y, y + h)
        return x, y

    def coord_more(self) -> tuple[int, int]:
        """
        从roi_back随机获取坐标
        :return:
        """
        x, y, w, h = self.roi_back
        x = np.random.randint(x, x + w)
        y = np.random.randint(y, y + h)
        return x, y

    @property
    def center(self) -> tuple[int, int]:
        """
        返回roi_front的中心坐标
        :return:
        """
        x, y, w, h = self.roi_front
        return x + w // 2, y + h // 2

    def move(self, x: int, y: int) -> None:
        """
        移动roi_front, 需要限幅x是0-1280, y是0-720
        :param x:
        :param y:
        :return:
        """
        x_cur, y_cur, w, h = self.roi_front
        x_new = x_cur + x
        y_new = y_cur + y
        if x_new <= 0:
            x_new = 0
        elif x_new >= 1280:
            x_new = 1280

        if y_new <= 0:
            y_new = 0
        elif y_new >= 720:
            y_new = 720

        self.roi_front = x_new, y_new, w, h
