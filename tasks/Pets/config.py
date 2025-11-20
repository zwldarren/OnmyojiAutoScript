# @author runhey
# github https://github.com/runhey
from pydantic import Field

from tasks.Component.config_base import ConfigBase
from tasks.Component.config_scheduler import Scheduler


class PetsConfig(ConfigBase):
    # 其乐融融
    pets_happy: bool = Field(default=True)
    # 大餐
    pets_feast: bool = Field(default=True)


class Pets(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    pets_config: PetsConfig = Field(default_factory=PetsConfig)
