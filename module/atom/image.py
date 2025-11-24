# @author runhey
# github https://github.com/runhey
from pathlib import Path

import cv2
import numpy as np
from numpy import fromfile, uint8

from module.base.decorator import cached_property
from module.base.utils import is_approx_rectangle
from module.logger import logger


class RuleImage:
    debug_mode: bool = False

    def __init__(
        self, roi_front: tuple, roi_back: tuple, method: str, threshold: float, file: str
    ) -> None:
        """
        初始化
        :param roi_front: 前置roi
        :param roi_back: 后置roi 用于匹配的区域
        :param method: 匹配方法 "Template matching"
        :param threshold: 阈值  0.8
        :param file: 相对路径, 带后缀
        """
        self._match_init = False  # 这个是给后面的 等待图片稳定
        self._image = None  # 这个是匹配的目标
        self._kp = None  #
        self._des = None
        self.method = method

        self.roi_front: list = list(roi_front)
        self.roi_back: list = list(roi_back)
        self.threshold = threshold
        self.file = file

    @cached_property
    def name(self) -> str:
        """

        :return:
        """
        return Path(self.file).stem.upper()

    def __str__(self):
        return self.name

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    def __bool__(self):
        return True

    def load_image(self) -> None:
        """
        加载图片
        :return:
        """
        if self._image is not None:
            return
        img = cv2.imdecode(fromfile(self.file, dtype=uint8), -1)
        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self._image = img

        if self._image is not None:
            height, width, channels = self._image.shape
            if height != self.roi_front[3] or width != self.roi_front[2]:
                self.roi_front[2] = width
                self.roi_front[3] = height
                logger.debug(f"{self.name} roi_front size changed to {width}x{height}")

    def load_kp_des(self) -> None:
        if self._kp is not None and self._des is not None:
            return
        if self.sift is None:
            self._kp = []
            self._des = np.array([])
            return
        self._kp, self._des = self.sift.detectAndCompute(self.image, None)

    @property
    def image(self):
        """
        获取图片
        :return:
        """
        if self._image is None:
            self.load_image()
        return self._image

    @cached_property
    def is_template_match(self) -> bool:
        """
        是否是模板匹配
        :return:
        """
        return self.method == "Template matching"

    @cached_property
    def is_sift_flann(self) -> bool:
        return self.method == "Sift Flann"

    @cached_property
    def sift(self):
        # Try different ways to get SIFT based on OpenCV version
        sift = None
        if hasattr(cv2, "SIFT_create"):
            sift = cv2.SIFT_create()
        # Only try xfeatures2d if SIFT is not available in main cv2
        elif hasattr(cv2, "xfeatures2d") and hasattr(cv2.xfeatures2d, "SIFT_create"):
            sift = cv2.xfeatures2d.SIFT_create()

        return sift

    @cached_property
    def kp(self):
        if self._kp is None:
            self.load_kp_des()
        return self._kp if self._kp is not None else []

    @cached_property
    def des(self):
        if self._des is None:
            self.load_kp_des()
        return self._des if self._des is not None else []

    def corp(self, image: np.ndarray, roi: list[int] | None = None) -> np.ndarray:
        """
        截取图片
        :param image:
        :param roi
        :return:
        """
        if roi is None:
            x, y, w, h = self.roi_back
        else:
            x, y, w, h = roi
        x, y, w, h = int(x), int(y), int(w), int(h)
        return image[y : y + h, x : x + w]

    def match(self, image: np.ndarray, threshold: float | None = None) -> bool:
        """
        :param threshold:
        :param image:
        :return:
        """
        if threshold is None:
            threshold = self.threshold

        if not self.is_template_match:
            return self.sift_match(image)
            # raise Exception(f"unknown method {self.method}")

        source = self.corp(image)
        mat = self.image

        if mat is None:
            return False

        if hasattr(mat, "shape") and (mat.shape[0] == 0 or mat.shape[1] == 0):
            logger.error(f"Template image is invalid: {mat.shape}")
            return True

        if hasattr(source, "shape") and (source.shape[0] == 0 or source.shape[1] == 0):
            return False

        res = cv2.matchTemplate(source, mat, cv2.TM_CCOEFF_NORMED)  # type: ignore[arg-type]
        if res is None:
            return False
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        if self.debug_mode:
            logger.attr(self.name, f"matching score {max_val:.5f}")

        if max_val > threshold:
            self.roi_front[0] = max_loc[0] + self.roi_back[0]
            self.roi_front[1] = max_loc[1] + self.roi_back[1]
            return True
        else:
            return False

    def match_all(
        self, image: np.ndarray, threshold: float | None = None, roi: list[int] | None = None
    ) -> list[tuple]:
        """
        区别于match，这个是返回所有的匹配结果
        :param roi:
        :param image:
        :param threshold:
        :return:
        """
        if roi is not None:
            self.roi_back = roi
        if threshold is None:
            threshold = self.threshold
        if not self.is_template_match:
            raise Exception(f"unknown method {self.method}")
        source = self.corp(image)
        mat = self.image

        if mat is None:
            return []

        results = cv2.matchTemplate(source, mat, cv2.TM_CCOEFF_NORMED)  # type: ignore[arg-type]
        locations = np.where(results >= threshold)
        matches = []
        for pt in zip(*locations[::-1], strict=False):  # (x, y) coordinates
            score = results[pt[1], pt[0]]
            # 得分, x, y, w, h
            x = self.roi_back[0] + pt[0]
            y = self.roi_back[1] + pt[1]
            if mat is not None:
                matches.append((score, x, y, mat.shape[1], mat.shape[0]))
        return matches

    def match_all_any(
        self,
        image: np.ndarray,
        threshold: float | None = None,
        roi: list[int] | None = None,
        nms_threshold: float = 0.3,
    ) -> list[tuple]:
        """
        区别于match，这个是返回所有的匹配结果，去除冗余匹配项（例如：多个框选区域重叠的情况）时使用。
        :param roi:
        :param image:
        :param threshold:
        :return:
        """
        if roi is not None:
            self.roi_back = roi
        if threshold is None:
            threshold = self.threshold
        if not self.is_template_match:
            raise Exception(f"unknown method {self.method}")
        source = self.corp(image)
        mat = self.image

        if mat is None:
            return []

        results = cv2.matchTemplate(source, mat, cv2.TM_CCOEFF_NORMED)  # type: ignore[arg-type]
        locations = np.where(results >= threshold)
        matches = []
        for pt in zip(*locations[::-1], strict=False):  # (x, y) coordinates
            score = results[pt[1], pt[0]]
            # 得分, x, y, w, h
            x = self.roi_back[0] + pt[0]
            y = self.roi_back[1] + pt[1]
            if mat is not None:
                matches.append((score, x, y, mat.shape[1], mat.shape[0]))
        if len(matches) > 0:
            scores = np.array([m[0] for m in matches])
            boxes = np.array([[m[1], m[2], m[3], m[4]] for m in matches])
            # 使用OpenCV的NMSBoxes
            try:
                indices = cv2.dnn.NMSBoxes(
                    boxes.tolist(),
                    scores.tolist(),
                    threshold,
                    nms_threshold,
                )
            except Exception:
                # Fallback for older OpenCV versions
                indices = np.array([])
                for i in range(len(matches)):
                    keep = True
                    for j in range(i):
                        if self._iou_overlap(boxes[i], boxes[j]) > nms_threshold:
                            keep = False
                            break
                    if keep:
                        indices = np.append(indices, i)
            filtered_matches = [matches[i] for i in indices]
            return filtered_matches
        return matches

    @staticmethod
    def _iou_overlap(box1, box2):
        """计算两个框的IoU重叠率"""
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2

        # 计算交集的坐标
        xi_min = max(x1_min, x2_min)
        yi_min = max(y1_min, y2_min)
        xi_max = min(x1_max, x2_max)
        yi_max = min(y1_max, y2_max)

        # 计算交集面积
        inter_area = max(0, xi_max - xi_min) * max(0, yi_max - yi_min)

        # 计算两个框的面积
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)

        # 计算IoU
        iou = (
            inter_area / (box1_area + box2_area - inter_area)
            if (box1_area + box2_area - inter_area) > 0
            else 0
        )
        return iou

    def coord(self) -> tuple:
        """
        获取roi_front的随机的点击的坐标
        :return:
        """
        x, y, w, h = self.roi_front
        return x + np.random.randint(0, w), y + np.random.randint(0, h)

    def coord_more(self) -> tuple:
        """
         获取roi_back的随机的点击的坐标
        :return:
        """
        x, y, w, h = self.roi_back
        return x + np.random.randint(0, w), y + np.random.randint(0, h)

    def front_center(self) -> tuple:
        """
        获取roi_front的中心坐标
        :return:
        """
        x, y, w, h = self.roi_front
        return int(x + w // 2), int(y + h // 2)

    def test_match(self, image: np.ndarray):
        self.debug_mode = True
        if self.is_template_match:
            return self.match(image)
        if self.is_sift_flann:
            return self.sift_match(image, show=True)

    def sift_match(self, image: np.ndarray, show: bool = False) -> bool:
        """
        特征匹配，同样会修改 roi_front
        :param image: 是游戏的截图，就是转通道后的截图
        :param show: 测试用的
        :return:
        """
        source = self.corp(image)

        # Check if SIFT is available
        if self.sift is None:
            return False

        kp, des = self.sift.detectAndCompute(source, None)

        # Check if we have valid keypoints and descriptors
        if kp is None or des is None or len(kp) == 0 or len(des) == 0:
            return False

        # 参数1：index_params
        #    对于SIFT和SURF，可以传入参数index_params=dict(algorithm=FLANN_INDEX_KDTREE, trees=5)。
        #    对于ORB，可以传入参数index_params=dict(algorithm=FLANN_INDEX_LSH, table_number=6, key_size=12）。
        index_params = {"algorithm": 1, "trees": 5}
        # 参数2：search_params 指定递归遍历的次数，值越高结果越准确，但是消耗的时间也越多。
        search_params = {"checks": 50}
        # 根据设置的参数创建特征匹配器 指定匹配的算法和kd树的层数,指定返回的个数
        flann = cv2.FlannBasedMatcher(index_params, search_params)  # type: ignore[abstract]
        # 利用创建好的特征匹配器利用k近邻算法来用模板的特征描述符去匹配图像的特征描述符，k指的是返回前k个最匹配的特征区域
        # 返回的是最匹配的两个特征点的信息，返回的类型是一个列表，列表元素的类型是Dmatch数据类型，具体是什么我也不知道
        # 第一个参数是小图的des, 第二个参数是大图的des
        matches = flann.knnMatch(self.des, des, k=2)

        good = []
        result = True
        for _i, (m, n) in enumerate(matches):
            # 设定阈值, 距离小于对方的距离的0.7倍我们认为是好的匹配点.
            if m.distance < 0.6 * n.distance:
                good.append(m)
        if len(good) >= 10:
            src_pts = np.array([self.kp[m.queryIdx].pt for m in good], dtype=np.float32).reshape(
                -1, 1, 2
            )
            dst_pts = np.array([kp[m.trainIdx].pt for m in good], dtype=np.float32).reshape(
                -1, 1, 2
            )

            # 计算透视变换矩阵m， 要求点的数量>=4
            m, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            # 创建一个包含模板图像四个角坐标的数组
            w, h = self.roi_front[2], self.roi_front[3]
            pts = np.array(
                [[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]], dtype=np.float32
            ).reshape(-1, 1, 2)
            if m is None:
                result = False
            else:
                dst = cv2.perspectiveTransform(pts, m)  # type: ignore[arg-type]
                self.roi_front[0] = int(dst[0, 0, 0]) + self.roi_back[0]
                self.roi_front[1] = int(dst[0, 0, 1]) + self.roi_back[1]
                if show:
                    # Convert dst to list of points for polylines
                    pts_list = dst.astype(np.int32).reshape(-1, 1, 2)
                    cv2.polylines(source, [pts_list], isClosed=True, color=(0, 0, 255), thickness=2)  # type: ignore[arg-type]
                if not is_approx_rectangle(np.array([pos[0] for pos in dst.reshape(-1, 2)])):
                    result = False
        else:
            result = False

        # https://blog.csdn.net/cungudafa/article/details/105399278
        # https://blog.csdn.net/qq_45832961/article/details/122776322
        if show:
            # 准备一个空的掩膜来绘制好的匹配
            mask_matches = [[0, 0] for _ in range(len(matches))]
            # 向掩膜中添加数据
            for i, (m, n) in enumerate(matches):
                if m.distance < 0.6 * n.distance:  # 理论上0.7最好
                    mask_matches[i] = [1, 0]

            # Get non-None versions of image and kp for drawing
            img_to_draw = self.image if self.image is not None else np.array([])
            kp_to_draw = self.kp if self.kp else []
            source_kp = kp if kp else []

            img_matches = cv2.drawMatchesKnn(
                img_to_draw,
                kp_to_draw,
                source,
                source_kp,
                matches,
                outImg=np.array([]),
                matchColor=(0, 255, 0),
                singlePointColor=(255, 0, 0),
                matchesMask=mask_matches,
                flags=0,
            )
            cv2.imshow(f"Sift Flann: {self.name}", img_matches)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return result

    def match_mean_color(self, image, color: tuple, bias=10) -> bool:
        """

        :param image:
        :param color:  rgb
        :param bias:
        :return:
        """
        image = self.corp(image)
        average_color = cv2.mean(image)
        # logger.info(f'{self.name} average_color: {average_color}')
        return all(abs(average_color[i] - color[i]) <= bias for i in range(3))


if __name__ == "__main__":
    from dev_tools.assets_test import detect_image

    IMAGE_FILE = "./log/test/QQ截图20240223151924.png"
    from tasks.Restart.assets import RestartAssets

    jade = RestartAssets.I_HARVEST_JADE
    jade.method = "Sift Flann"
    sign = RestartAssets.I_HARVEST_SIGN
    sign.method = "Sift Flann"
    print(jade.roi_front)

    detect_image(IMAGE_FILE, jade)
    detect_image(IMAGE_FILE, sign)
    print(jade.roi_front)
