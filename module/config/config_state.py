# @author runhey
# github https://github.com/runhey

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module.config.config import Function


class ConfigState:
    """
    这个类用于 先定义运行过程中所需要的变量
    """

    def __init__(self, config_name: str) -> None:
        self.config_name = config_name
        self.pending_task: list[Function] = []
        self.waiting_task: list[Function] = []
        self.task: Function | None = None  # 任务对象
