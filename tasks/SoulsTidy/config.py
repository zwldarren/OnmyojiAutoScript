# @author runhey
# github https://github.com/runhey
from pydantic import BaseModel, Field

from tasks.Component.config_base import ConfigBase
from tasks.Component.config_scheduler import Scheduler


class SimpleTidy(BaseModel):
    # 贪吃鬼和招财猫
    enable_greed: bool = Field(default=True, description="是否启用贪吃鬼")
    enable_maneki: bool = Field(default=True, description="是否启用奉纳")


class SoulsTidy(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    simple_tidy: SimpleTidy = Field(default_factory=SimpleTidy)
