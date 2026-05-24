"""Настройки логирования для плагинов"""

import logging
from pathlib import Path

from pydantic import BaseModel


class LoggingSettings(BaseModel):
    """Настройки для логирования"""

    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_default_handlers: tuple[str, ...] = ("console", "file")
    log_level_handlers: str = "INFO"
    log_level_loggers: str = "INFO"
    log_level_root: str = "INFO"
    log_dir: str = "logs"

    def init_logging(self):
        log_path = Path(self.log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        root_level = getattr(logging, self.log_level_root.upper())
        handler_level = getattr(logging, self.log_level_handlers.upper())

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(root_level)

        formatter = logging.Formatter(self.log_format, datefmt="%Y-%m-%d %H:%M:%S")

        if "console" in self.log_default_handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(handler_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        if "file" in self.log_default_handlers:
            file_handler = logging.FileHandler(
                log_path / "app.log",
                encoding="utf-8",
            )
            file_handler.setLevel(handler_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
