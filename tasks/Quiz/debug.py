# @author runhey
# github https://github.com/runhey
import re
from pathlib import Path


def remove_symbols(text):
    return re.sub(r"[^\w\s]", "", text)


class Debugger:
    def __init__(self):
        self._file_path = None

    @property
    def fn(self):
        if self._file_path is None:
            # 以添加方式打开一个文件
            file: Path = Path("./log/quiz/supplement.txt")
            if not file.parent.exists():
                file.parent.mkdir(parents=True)
            if not file.exists():
                file.touch()
            self._file_path = file
        return self._file_path

    def append_one(self, question: str, options: list[str]):
        question = remove_symbols(question)
        options = [remove_symbols(option) for option in options]
        with open(self.fn, "a", encoding="utf-8") as f:
            f.write(f"{question},{options[0]},{options[1]},{options[2]},{options[3]}\n")

    def close_fn(self):
        # File is automatically closed when using context manager
        pass


if __name__ == "__main__":
    a = Debugger()
    a.append_one("1", ["1", "2", "3", "4"])
    a.append_one("5", ["1", "2939/;.", "3", "4"])
    a.append_one("1", ["1", "2", "3", "4"])
    a.close_fn()
