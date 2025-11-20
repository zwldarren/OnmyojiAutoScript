# @author runhey
# github https://github.com/runhey

from tasks.Exploration.solo import ScriptTask as SoloScriptTask


class ScriptTask(SoloScriptTask):
    pass


if __name__ == "__main__":
    from module.config.config import Config
    from module.device.device import Device

    config = Config("oas1")
    device = Device(config)
    t = ScriptTask(config, device)
    t.config.exploration.exploration_config.exploration_level = "第二十八章"
    t.run()
