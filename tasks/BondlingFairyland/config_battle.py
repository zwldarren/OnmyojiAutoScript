# @author runhey
# github https://github.com/runhey

from tasks.Component.config_base import dynamic_hide
from tasks.Component.GeneralBattle.config_general_battle import GeneralBattleConfig


class BattleConfig(GeneralBattleConfig):
    hide_fields = dynamic_hide("lock_team_enable", "preset_enable", "preset_group", "preset_team")
