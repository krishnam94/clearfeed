import logging
import os

LOG_PATH = os.path.join(os.path.dirname(__file__), '../clearfeed.log')
logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def log_event(event):
    logging.info(event)
