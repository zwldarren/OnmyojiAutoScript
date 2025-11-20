# @author runhey
# github https://github.com/runhey

from module.exception import TaskEnd
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_main


class ScriptTask(GameUi):
    def run(self) -> None:
        self.ui_get_current_page()
        self.ui_goto(page_main)
        raise TaskEnd("Goto main end")
