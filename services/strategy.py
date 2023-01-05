import numpy as np
import pandas as pd


def st_strategy(source, st):
    st_signal = np.zeros(len(st))
    signal = 0

    for i in range(1, len(st)):
        if st[i-1] > source[i-1] and st[i] < source[i]:
            if signal != 1:
                signal = 1
                st_signal[i] = signal
        elif st[i-1] < source[i-1] and st[i] > source[i]:
            if signal != -1:
                signal = -1
                st_signal[i] = signal

    st = pd.Series(st_signal)
    return st


def rf_strategy(source, filt, upw, dnw):
    rf_signal = np.zeros(len(source), dtype=int)
    long_cond = np.zeros(len(source), dtype=bool)
    short_cond = np.zeros(len(source), dtype=bool)
    signal = np.zeros(len(source))

    for i in range(1, len(source)):
        long_cond[i] = (source[i] > filt[i] and source[i] > source[i-1] and upw[i] > 0) or \
                       (source[i] > filt[i] and source[i]
                        < source[i-1] and upw[i] > 0)
        short_cond[i] = (source[i] < filt[i] and source[i] < source[i-1] and dnw[i] > 0) or \
                        (source[i] < filt[i] and source[i]
                         > source[i-1] and dnw[i] > 0)

        if long_cond[i]:
            signal[i] = 1
        elif short_cond[i]:
            signal[i] = -1
        else:
            signal[i] = signal[i-1]

        if long_cond[i] and signal[i-1] == -1:
            rf_signal[i] = 1
        elif short_cond[i] and signal[i-1] == 1:
            rf_signal[i] = -1

    rf = pd.Series(rf_signal)
    return rf


def macd_cross_strategy(macd):
    macd_signal = np.zeros(len(macd), dtype=int)
    macd_1 = np.zeros(len(macd))
    macd_2 = np.zeros(len(macd))

    macd_1[1:] = macd[1:]
    macd_2[1:] = macd[:-1]

    macd_signal = np.where((macd_1 > 0) & (macd_2 < 0), 1, 0)
    macd_signal += np.where((macd_1 < 0) & (macd_2 > 0), -1, 0)
    macd = pd.Series(macd_signal)
    return macd


def macdh_cross_strategy(macdh):
    macdh_signal = np.zeros(len(macdh))
    macdh_1 = np.zeros(len(macdh))
    macdh_2 = np.zeros(len(macdh))
    macdh_3 = np.zeros(len(macdh))

    macdh_1[2:] = macdh[2:]
    macdh_2[2:] = macdh[1:-1]
    macdh_3[2:] = macdh[:-2]

    macdh_signal = np.where((macdh_1 > 0) & (macdh_2 < 0) & (macdh_2 > macdh_3), 1, 0)
    macdh_signal += np.where((macdh_1 < 0) & (macdh_2 > 0) & (macdh_2 < macdh_3), -1, 0)
    macdh = pd.Series(macdh_signal)
    return macdh
