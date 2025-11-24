# @author runhey
# github https://github.com/runhey
from typing import Any

import numpy as np

from module.atom.image import RuleImage


class RuleGif:
    # 大部分实现同RuleImage 的接口

    @property
    def name(self) -> str:
        return self.appear_target.name

    def __init__(self, targets: list[RuleImage]):
        self.targets = targets
        self.roi_front = [0, 0, 0, 0]
        self.appear_target = targets[0]

    def pre_process(self, image: Any) -> Any:
        return image

    def search(
        self, image: Any, roi: list[int] | None = None, threshold: float | None = None
    ) -> tuple[bool, RuleImage | None]:
        """

        :param image:
        :param roi:
        :param threshold:
        :return: bool
        第一项是否为出现, 第二项为匹配的RuleImage
        """
        image = self.pre_process(image)
        #
        threshold = self.targets[0].threshold if threshold is None else threshold
        roi = self.targets[0].roi_back if roi is None else roi
        for target in self.targets:
            target.roi_back = list(roi) if roi is not None else list(self.targets[0].roi_back)
            if target.match(image, threshold):
                self.roi_front = list(target.roi_front)
                self.appear_target = target
                return True, target
        return False, None

    def match(self, image: Any, threshold: float | None = None) -> bool:
        return self.search(image, threshold=threshold)[0]

    def coord(self) -> tuple[int, int]:
        x, y, w, h = self.roi_front
        return x + np.random.randint(0, w), y + np.random.randint(0, h)

    def front_center(self) -> tuple[int, int]:
        x, y, w, h = self.roi_front
        return int(x + w // 2), int(y + h // 2)
