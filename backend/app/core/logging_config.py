import logging
import logging.config
import sys
from app.config import settings


def setup_logging():
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","line":%(lineno)d,"msg":"%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if settings.is_production else "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {"level": "INFO", "propagate": False, "handlers": ["console"]},
            "uvicorn.access": {"level": "WARNING", "propagate": False, "handlers": ["console"]},
            "sqlalchemy.engine": {"level": "WARNING", "propagate": False, "handlers": ["console"]},
            "httpx": {"level": "WARNING", "propagate": False, "handlers": ["console"]},
        },
    }
    logging.config.dictConfig(config)
    logger = logging.getLogger("app")
    logger.info("Logging configured: level=%s, env=%s", settings.log_level, settings.environment)
