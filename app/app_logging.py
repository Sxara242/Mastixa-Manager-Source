from __future__ import annotations

import logging
import copy
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import threading


LOGGER_NAME = "mastixa"
_log_path: Path | None = None
_configured = False


class _PrivacyFormatter(logging.Formatter):
    def __init__(self, *args, redactions: tuple[tuple[str, str], ...], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.redactions = tuple(
            (source, replacement)
            for source, replacement in redactions
            if source
        )

    def format(self, record: logging.LogRecord) -> str:
        record = copy.copy(record)
        record.exc_text = None  # Do not reuse another handler's unsanitized cache.
        rendered = super().format(record)
        for source, replacement in self.redactions:
            rendered = rendered.replace(source, replacement)
            rendered = rendered.replace(source.replace("\\", "/"), replacement)
        return rendered

    def formatException(self, exc_info) -> str:
        # Exception messages, source lines and locals may contain imported data.
        lines = ["Exception: " + exc_info[0].__name__]
        tb = exc_info[2]
        while tb is not None:
            code = tb.tb_frame.f_code
            lines.append(f"  {Path(code.co_filename).name}:{tb.tb_lineno} in {code.co_name}")
            tb = tb.tb_next
        return "\n".join(lines)

    def formatStack(self, stack_info: str) -> str:
        return "[stack text omitted for privacy]"


def configure_logging(base_dir: Path) -> Path:
    """Configure bounded local diagnostics without recording business data."""
    global _configured, _log_path
    base_dir = Path(base_dir).resolve()
    log_dir = base_dir / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    _log_path = log_dir / "mastixa_manager.log"
    if _configured:
        return _log_path

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = RotatingFileHandler(
        _log_path,
        maxBytes=1_048_576,
        backupCount=5,
        encoding="utf-8",
        delay=True,
    )
    home = str(Path.home().resolve())
    formatter = _PrivacyFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        redactions=(
            (str(base_dir), "<APP_DIR>"),
            (home, "<USER_HOME>"),
        ),
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    _install_exception_hooks(logger)
    _configured = True
    logger.info("Application diagnostics initialized")
    return _log_path


def get_logger(component: str) -> logging.Logger:
    clean = str(component).replace("app.", "").strip(".") or "application"
    return logging.getLogger(f"{LOGGER_NAME}.{clean}")


def log_path() -> Path | None:
    return _log_path


def _install_exception_hooks(logger: logging.Logger) -> None:
    def handle_exception(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        if sys.stderr is not None:
            sys.stderr.write("Unhandled exception; see local diagnostic log (details redacted).\n")

    sys.excepthook = handle_exception

    if hasattr(threading, "excepthook"):
        def handle_thread_exception(args) -> None:
            logger.critical(
                "Unhandled background-thread exception",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )

        threading.excepthook = handle_thread_exception
