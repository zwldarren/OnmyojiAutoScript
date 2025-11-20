# @author runhey
# github https://github.com/runhey
import logging
import os
import shutil
import sys
from collections.abc import Callable
from datetime import date, datetime, timedelta
from io import TextIOBase
from pathlib import Path
from typing import Any, Literal, Protocol, TypeVar

from rich.console import Console, ConsoleOptions, ConsoleRenderable, NewLine, RenderResult
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from rich.rule import Rule


def cleanup_logs(log_dir: str = "./log", keep_days: int = 7):
    """删除 log_dir 下所有早于 keep_days 的文件夹和文件"""
    log_path = Path(log_dir)
    if not log_path.exists():
        return  # 目录都没有，直接退出
    keep_days_ago_ts = (datetime.now() - timedelta(days=keep_days)).timestamp()
    for name in os.listdir(log_path):
        full_path = os.path.join(log_path, name)
        # 忽略软链接，仅处理文件和目录
        if not os.path.exists(full_path):
            continue
        if os.path.isfile(full_path):
            # 处理 log 根目录下超过keep_days的文件
            try:
                if os.path.getmtime(full_path) < keep_days_ago_ts:
                    os.remove(full_path)
            except OSError as e:
                logger.error(f"delete file '{full_path}' error: {e}")
        elif os.path.isdir(full_path):
            # 检查是否为 error 目录
            if name != "error":
                continue
            for error_dir_name in os.listdir(full_path):
                error_dir_path = os.path.join(full_path, error_dir_name)
                if not os.path.isdir(error_dir_path):
                    continue
                # 处理 log/error 根目录下超过keep_days的文件夹
                try:
                    if os.path.getmtime(error_dir_path) < keep_days_ago_ts:
                        # 递归删除整个目录及其内容
                        shutil.rmtree(error_dir_path)
                except OSError as e:
                    logger.error(f"delete dir '{error_dir_path}' error: {e}")


def empty_function(*args, **kwargs):
    pass


# Ensure running in Alas root folder
os.chdir(os.path.join(os.path.dirname(__file__), "../"))
# cnocr will set root logger in cnocr.utils
# Delete logging.basicConfig to avoid logging the same message twice.
logging.basicConfig = empty_function
logging.raiseExceptions = True  # Set True if wanna see encode errors on console

# Remove HTTP keywords (GET, POST etc.)
# RichHandler.KEYWORDS = []


# def show_handlers(handlers):
#     # 获取并打印日志记录器中处理器的信息
#     for handler in logger.handlers:
#         # 获取处理器的类名
#         handler_class = handler.__class__.__name__
#         print(f"Handler class: {handler_class}")
#
#         # 获取处理器的级别
#         handler_level = logging.getLevelName(handler.level)
#         print(f"Handler level: {handler_level}")
#
#         # 获取处理器的格式化器
#         formatter = handler.formatter
#         if formatter is not None:
#             formatter_class = formatter.__class__.__name__
#             print(f"Formatter class: {formatter_class}")
#
#         # 其他处理器的属性和方法，根据需要进行获取和打印
#         print()  # 打印空行，用于分隔处理器的信息


# Logger init
logger_debug = False
logger = logging.getLogger("oas")
logger.setLevel(logging.DEBUG if logger_debug else logging.INFO)
file_formatter = logging.Formatter(
    fmt="%(asctime)s.%(msecs)03d | %(filename)20s:%(lineno)04d | %(levelname)8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console_formatter = logging.Formatter(
    fmt="%(asctime)s.%(msecs)03d │ %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
flutter_formatter = logging.Formatter(
    fmt="| %(asctime)s.%(msecs)03d | %(message)08s", datefmt="%H:%M:%S"
)


# ======================================================================================================================
#            Set console logger
# ======================================================================================================================
console_hdlr = RichHandler(
    console=Console(width=120),
    show_path=False,
    show_time=False,
    rich_tracebacks=True,
    tracebacks_show_locals=True,
    tracebacks_extra_lines=3,
    tracebacks_width=160,
)
console_hdlr.setFormatter(console_formatter)
logger.addHandler(console_hdlr)


# ======================================================================================================================
#            Set file
# ======================================================================================================================
class RichFileHandler(RichHandler):
    """File handler that extends RichHandler for file logging."""

    pass


# Add file logger
pyw_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]


def set_file_logger(name: str | None = None, *, do_cleanup: bool = False) -> None:
    """
    Set up file logger with Rich formatting.

    Args:
        name: Base name for the log file (without extension). Defaults to script name.
        do_cleanup: If True, clean up old log files before starting
    """
    if name is None:
        name = pyw_name
    if "_" in name:
        name = name.split("_", 1)[0]
    log_file: str = f"./log/{date.today()}_{name}.txt"
    try:
        file = open(log_file, mode="a", encoding="utf-8")
    except FileNotFoundError:
        os.mkdir("./log")
        file = open(log_file, mode="a", encoding="utf-8")

    file_console = Console(
        file=file,
        no_color=True,
        highlight=False,
        width=160,
    )

    hdlr = RichFileHandler(
        console=file_console,
        show_path=False,
        show_time=False,
        show_level=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        tracebacks_extra_lines=3,
        tracebacks_width=160,
        highlighter=NullHighlighter(),
    )
    hdlr.setFormatter(file_formatter)

    logger.handlers = [
        h for h in logger.handlers if not isinstance(h, (logging.FileHandler, RichFileHandler))
    ]
    logger.addHandler(hdlr)
    logger.log_file = log_file  # type: ignore[attr-defined]

    # ---------- 可选：清理旧文件 ----------
    if do_cleanup:
        cleanup_logs()
        logger.info("Log cleanup finished")


# ======================================================================================================================
#            Set flutter
# ======================================================================================================================
class FlutterHandler(RichHandler):
    """Handler for Flutter logging."""

    pass


class FlutterConsole(Console):
    """
    Force full feature console
    but not working lol :(
    """

    @property
    def options(self) -> ConsoleOptions:
        return ConsoleOptions(
            max_height=self.size.height,
            size=self.size,
            legacy_windows=False,
            min_width=1,
            max_width=self.width,
            encoding="utf-8",
            is_terminal=False,
        )


class FlutterLogStream(TextIOBase):
    """
    Custom stream that writes to a callback function instead of a file.
    """

    def __init__(self, func: Callable[[str], None] | None = None):
        # Initialize underlying TextIOBase without passing any args
        super().__init__()
        self._func: Callable[[str], None] | None = func

    def write(self, s: str) -> int:
        """Write a string to the stream."""
        if isinstance(s, bytes):
            s = s.decode("utf-8")
        if self._func is not None:
            self._func(s)
        return len(s)

    def flush(self) -> None:
        """Flush the stream (no-op for this implementation)."""
        pass

    def readable(self) -> bool:
        """Return whether the stream is readable."""
        return False

    def writable(self) -> bool:
        """Return whether the stream is writable."""
        return True

    def seekable(self) -> bool:
        """Return whether the stream is seekable."""
        return False

    def read(self, size: int = -1) -> str:
        """Read from the stream (not supported)."""
        return ""

    def readline(self, size: int = -1) -> str:
        """Read a line from the stream (not supported)."""
        return ""

    def readlines(self, hint: int = -1) -> list[str]:
        """Read lines from the stream (not supported)."""
        return []


def set_func_logger(func: Callable[[str], None]) -> None:
    """
    Set up a function-based logger that calls a callback for each log message.

    Args:
        func: Callback function that receives log messages as strings
    """
    stream = FlutterLogStream(func=func)
    stream_console = Console(
        file=stream,  # type: ignore[arg-type]
        force_terminal=False,
        force_interactive=False,
        no_color=True,
        highlight=False,
        width=80,
    )
    hdlr = FlutterHandler(
        console=stream_console,
        show_path=False,
        show_time=False,
        show_level=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        tracebacks_extra_lines=3,
        highlighter=NullHighlighter(),
    )
    hdlr.setFormatter(flutter_formatter)
    logger.addHandler(hdlr)


# ======================================================================================================================
#            Set print format
# ======================================================================================================================


def _get_renderables(
    self: Console,
    *objects: ConsoleRenderable,
    sep: str = " ",
    end: str = "\n",
    justify: Literal["default", "left", "center", "right", "full"] | None = None,
    emoji: bool | None = None,
    markup: bool | None = None,
    highlight: bool | None = None,
) -> list[ConsoleRenderable]:
    """
    Refer to rich.console.Console.print()
    """
    if not objects:
        objects = (NewLine(),)

    render_hooks = self._render_hooks[:]
    with self:
        renderables = self._collect_renderables(
            objects,
            sep,
            end,
            justify=justify,
            emoji=emoji,
            markup=markup,
            highlight=highlight,
        )
        for hook in render_hooks:
            renderables = hook.process_renderables(renderables)
    return renderables


def print(*objects: ConsoleRenderable, **kwargs: Any) -> None:
    """
    Custom print function that works with all logger handlers.

    Args:
        objects: Objects to print
        **kwargs: Additional keyword arguments passed to console.print()
    """
    for hdlr in logger.handlers:
        if isinstance(hdlr, FlutterHandler):
            for renderable in _get_renderables(hdlr.console, *objects, **kwargs):
                # Type narrowing: we know _func is set for FlutterHandler
                stream = hdlr.console.file  # type: ignore[attr-defined]
                if isinstance(stream, FlutterLogStream) and stream._func is not None:
                    stream._func(str(renderable))
        elif isinstance(hdlr, RichHandler):
            hdlr.console.print(*objects, **kwargs)


class GuiRule(Rule):
    """Custom Rule for GUI display with fixed width."""

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        options.max_width = 80
        return super().__rich_console__(console, options)

    def __str__(self) -> str:
        total_width = 80
        cell_len = len(self.title) + 2
        aside_len = (total_width - cell_len) // 2
        left = self.characters * aside_len
        right = self.characters * (total_width - cell_len - aside_len)
        if self.title:
            space = " "
        else:
            space = self.characters
        return f"{left}{space}{self.title}{space}{right}\n"

    def __repr__(self) -> str:
        return self.__str__()


def rule(
    title: str = "",
    *,
    characters: str = "─",
    style: str = "rule.line",
    end: str = "\n",
    align: str = "center",
) -> None:
    """
    Print a rule with optional title.

    Args:
        title: Title text to display in the rule
        characters: Character to use for the rule line
        style: Rich text style
        end: Line ending character
        align: Alignment of the title
    """
    rule_obj = GuiRule(title=title, characters=characters, style=style, end=end)
    print(rule_obj)


def hr(title: str, level: int = 3) -> None:
    """
    Print a horizontal rule with title at different levels.

    Args:
        title: Title text
        level: Rule level (0-3)
            0: Triple line rule with title in middle line
            1: Double line rule
            2: Single line rule
            3: Bold text with markers
    """
    title_upper = str(title).upper()
    if level == 1:
        logger.rule(title_upper, characters="═")  # type: ignore[attr-defined]
        logger.info(title_upper)
    elif level == 2:
        logger.rule(title_upper, characters="─")  # type: ignore[attr-defined]
        logger.info(title_upper)
    elif level == 3:
        logger.info(f"[bold]<<< {title_upper} >>>[/bold]", extra={"markup": True})
    elif level == 0:
        logger.rule(characters="═")  # type: ignore[attr-defined]
        logger.rule(title_upper, characters="─")  # type: ignore[attr-defined]
        logger.rule(characters="═")  # type: ignore[attr-defined]


def attr(name: str, text: Any) -> None:
    """
    Log an attribute name-value pair.

    Args:
        name: Attribute name
        text: Attribute value
    """
    logger.info("[%s] %s" % (str(name), str(text)))


def attr_align(name: str, text: Any, front: str = "", align: int = 22) -> None:
    """
    Log an attribute with aligned formatting.

    Args:
        name: Attribute name
        text: Attribute value
        front: Prefix text
        align: Alignment width for the name
    """
    name_str = str(name).rjust(align)
    if front:
        name_str = front + name_str[len(front) :]
    logger.info("%s: %s" % (name_str, str(text)))


from typing import Any, Literal, cast

# Type variable for logger
LoggerT = TypeVar("LoggerT", bound="ExtendedLogger")


class ExtendedLogger(Protocol):
    """Protocol defining the extended logger interface."""

    # Standard logging.Logger attributes
    handlers: list[Any]

    def addHandler(self, handler: Any) -> None: ...
    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...
    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...
    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...
    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...
    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...

    # Extended attributes
    log_file: str
    hr: Callable[..., None]
    attr: Callable[[str, Any], None]
    attr_align: Callable[[str, Any, str, int], None]
    set_file_logger: Callable[..., None]
    set_func_logger: Callable[[Callable[[str], None]], None]
    rule: Callable[..., None]
    print: Callable[..., None]


def show() -> None:
    """Display all log levels for testing."""
    logger.info("INFO")
    logger.warning("WARNING")
    logger.debug("DEBUG")
    logger.error("ERROR")
    logger.critical("CRITICAL")
    hr("hr0", 0)
    hr("hr1", 1)
    hr("hr2", 2)
    hr("hr3", 3)
    logger.info(r"Brace { [ ( ) ] }")
    logger.info(r"True, False, None")
    logger.info(r"E:/path\\to/alas/alas.exe, /root/alas/, ./relative/path/log.txt")
    logger.info(
        "Tests very long strings. Tests very long strings. Tests very long strings. Tests very long strings. Tests very long strings."
    )
    local_var1 = "This is local variable"
    # Line before exception
    raise Exception("Exception")
    # Line below exception


def error_convert(func):
    """Decorator to convert Exception objects to strings."""

    def error_wrapper(msg, *args, **kwargs):
        if isinstance(msg, Exception):
            msg = f"{type(msg).__name__}: {msg}"
        return func(msg, *args, **kwargs)

    return error_wrapper


# Type cast to tell type checker that logger has extended methods
_logger = logger

# Apply monkey patches with type safety
_logger.error = error_convert(_logger.error)  # type: ignore[assignment]
_logger.hr = hr  # type: ignore[assignment]
_logger.attr = attr  # type: ignore[assignment]
_logger.attr_align = attr_align  # type: ignore[assignment]
_logger.set_file_logger = set_file_logger  # type: ignore[assignment]
_logger.set_func_logger = set_func_logger  # type: ignore[assignment]
_logger.rule = rule  # type: ignore[assignment]
_logger.print = print  # type: ignore[assignment]

# Declare the log_file attribute
_logger.log_file: str = ""  # type: ignore[attr-defined]

# Use the extended logger
logger = cast(ExtendedLogger, _logger)

logger.set_file_logger(name=None)
logger.hr("Start", level=0)
