import os
import datetime
import config
import logging
import neptune
from pathlib import Path
from settings import LOG_DIR

def setup_logging():
    """Set up logging configuration."""
    # Ensure the log directory exists
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    
    # Generate the log file name based on current timestamp
    now_time = datetime.datetime.now()
    date_str = now_time.strftime('%Y%m%d%H%M%S')
    log_file_name = f'{date_str}.log'
    
    # Full log file path
    app_log_file_path = os.path.join(LOG_DIR, log_file_name)
    
    # Configure the logging settings
    logging.basicConfig(filename=app_log_file_path,
                        filemode='a',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S',
                        level=logging.INFO,
                        force=True)
    logging.info("Logging setup complete.")  # Test log message


def initialize_neptune(neptune_mode="debug"):
    # Initialize Neptune
    run = neptune.init_run(
        project = "GIoT/DebtGuardian",
        api_token = config.neptune_api_token,
        # mode = neptune_mode
        # TODO: not working on debug mode!
    )
    logging.info("Neptune initialized.")
    return run

def log_metrics_to_neptune(run, mode, metrics):
    """
    Log evaluation metrics to Neptune based on the selected mode.
    
    Parameters:
    - run: Neptune run object
    - mode: str, the evaluation mode ("file_level", "multi_class", or "line_level")
    - metrics: dict, the evaluation metrics to log
    """
    if run is not None:
        for metric, value in metrics.items():
            run[f"{mode}/{metric}"] = value
