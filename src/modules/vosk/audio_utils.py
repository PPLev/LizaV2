from scipy import signal

import numpy as np


def find_offset(audio1, audio2):
    correlation = signal.correlate(audio2, audio1, mode="same")
    lags = signal.correlation_lags(audio2.size, audio1.size, mode="same")
    lag = lags[np.argmax(correlation)]

    return lag


def filter_voice_gen(raw, generated):
    if not generated:
        return raw

    lag = find_offset(raw, generated)

    if lag > 0:
        raw = raw - generated[lag:lag+len(raw)]

    return raw
