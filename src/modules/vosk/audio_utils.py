import logging

from scipy import signal

import numpy as np
logger = logging.getLogger("root")

def find_offset(audio1, audio2):
    correlation = signal.correlate(audio2, audio1, mode="same", method="direct")
    lags = signal.correlation_lags(audio2.size, audio1.size, mode="full")
    lag = lags[np.argmax(correlation)]

    return lag


def filter_voice_gen(raw, generated):
    logger.info(f"Filtering voice gen, input len = {len(raw)}, {raw}")
    try:
        lag = find_offset(raw, generated)

        if lag > 0:
            print(lag)
            raw = raw - generated[lag:lag+len(raw)]
    except Exception as e:
        logger.error("filter error: ", exc_info=True)

    logger.info(f"222 Filtering voice gen, input len = {len(raw)}, {raw}")
    return raw
