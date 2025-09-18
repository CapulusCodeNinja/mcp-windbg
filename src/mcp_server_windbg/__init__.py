from .server import serve

def main():
    """MCP WinDBG Server - Windows crash dump analysis functionality for MCP"""
    import argparse
    import asyncio
    import logging
    import logging.handlers
    import os

    def default_log_path() -> str:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base_dir = os.path.join(local_app_data, "mcp-windbg")
        else:
            base_dir = os.path.join(os.getcwd(), "logs")
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception:
            base_dir = os.getcwd()
        return os.path.join(base_dir, "mcp-windbg.log")

    parser = argparse.ArgumentParser(
        description="Give a model the ability to analyze Windows crash dumps with WinDBG/CDB"
    )
    parser.add_argument("--cdb-path", type=str, help="Custom path to cdb.exe")
    parser.add_argument("--symbols-path", type=str, help="Custom symbols path")
    parser.add_argument("--timeout", type=int, default=30, help="Command timeout in seconds")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output to console and debug logs")

    # Logging options
    parser.add_argument("--log-file", type=str, default=default_log_path(), help="Path to log file (will be created if missing)")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"], help="File log level")
    parser.add_argument("--log-max-bytes", type=int, default=5 * 1024 * 1024, help="Max size of a single log file before rotation")
    parser.add_argument("--log-backup-count", type=int, default=5, help="Number of rotated log files to keep")

    args = parser.parse_args()

    # Configure logging (file + optional console)
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, args.log_level.upper(), logging.INFO))

    # Avoid duplicate handlers when running in environments that pre-configure logging
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in root_logger.handlers):
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                args.log_file,
                maxBytes=args.log_max_bytes,
                backupCount=args.log_backup_count,
                encoding="utf-8",
                delay=True,
            )
            file_handler.setFormatter(logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))
            root_logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to console-only if file handler cannot be created
            fallback = logging.StreamHandler()
            fallback.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
            root_logger.addHandler(fallback)
            root_logger.error("Failed to set up file logging at %s: %s", args.log_file, e)

    if args.verbose:
        # Console handler for interactive debugging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
        root_logger.addHandler(console_handler)
        # Also raise global level to DEBUG for verbose runs
        root_logger.setLevel(logging.DEBUG)

    logging.getLogger(__name__).info("Starting MCP WinDBG server", extra={})

    asyncio.run(serve(
        cdb_path=args.cdb_path,
        symbols_path=args.symbols_path,
        timeout=args.timeout,
        verbose=args.verbose
    ))


if __name__ == "__main__":
    main()