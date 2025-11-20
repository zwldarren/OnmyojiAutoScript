# @author runhey
# github https://github.com/runhey
from pydantic import Field

from tasks.Component.config_base import Time
from tasks.Component.config_scheduler import Scheduler


class RestartScheduler(Scheduler):
    enable: bool = Field(default=True, description="enable_help")
    priority: int = Field(default=0, description="priority_help")
    server_update: Time = Field(
        default=Time(hour=9, minute=5, second=0), description="server_update_help"
    )
