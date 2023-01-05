import pandas as pd
import numpy as np


def get_supertrend(high, low, close, lookback, multiplier):
    # ATR

    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = tr.ewm(lookback).mean()

    # H/L AVG AND BASIC UPPER & LOWER BAND

    hl_avg = (high + low) / 2
    upper_band = (hl_avg + multiplier * atr).dropna()
    lower_band = (hl_avg - multiplier * atr).dropna()

    # FINAL UPPER BAND
    final_bands = pd.DataFrame(columns=['upper', 'lower'], dtype=object)
    final_bands.iloc[:, 0] = [x for x in upper_band - upper_band]
    final_bands.iloc[:, 1] = final_bands.iloc[:, 0]
    for i in range(len(final_bands)):
        if i == 0:
            final_bands.iloc[i, 0] = 0
        else:
            if (upper_band[i] < final_bands.iloc[i-1, 0]) | (close[i-1] > final_bands.iloc[i-1, 0]):
                final_bands.iloc[i, 0] = upper_band[i]
            else:
                final_bands.iloc[i, 0] = final_bands.iloc[i-1, 0]

    # FINAL LOWER BAND

    for i in range(len(final_bands)):
        if i == 0:
            final_bands.iloc[i, 1] = 0
        else:
            if (lower_band[i] > final_bands.iloc[i-1, 1]) | (close[i-1] < final_bands.iloc[i-1, 1]):
                final_bands.iloc[i, 1] = lower_band[i]
            else:
                final_bands.iloc[i, 1] = final_bands.iloc[i-1, 1]

    # SUPERTREND

    supertrend = pd.DataFrame(columns=[f'supertrend_{lookback}'], dtype=object)
    supertrend.iloc[:, 0] = [
        x for x in final_bands['upper'] - final_bands['upper']]

    for i in range(len(supertrend)):
        if i == 0:
            supertrend.iloc[i, 0] = 0
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 0] and close[i] < final_bands.iloc[i, 0]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 0]
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 0] and close[i] > final_bands.iloc[i, 0]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 1] and close[i] > final_bands.iloc[i, 1]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 1] and close[i] < final_bands.iloc[i, 1]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 0]

    supertrend = supertrend.set_index(upper_band.index)
    supertrend = supertrend.dropna()[1:]

    # ST UPTREND/DOWNTREND

    upt = []
    dt = []
    close = close.iloc[len(close) - len(supertrend):]

    for i in range(len(supertrend)):
        if close[i+1] > supertrend.iloc[i, 0]:
            upt.append(supertrend.iloc[i, 0])
            dt.append(np.nan)
        elif close[i+1] < supertrend.iloc[i, 0]:
            upt.append(np.nan)
            dt.append(supertrend.iloc[i, 0])
        else:
            upt.append(np.nan)
            dt.append(np.nan)

    st, upt, dt = pd.Series(
        supertrend.iloc[:, 0]), pd.Series(upt), pd.Series(dt)
    upt.index, dt.index = supertrend.index, supertrend.index

    return st, upt, dt


def get_range_filter(source, sampling_period, multiplier):
    tr1 = pd.DataFrame({'source': source})
    tr2 = pd.DataFrame({'source': abs(source - source.shift(1))})

    avrng = tr2['source'].ewm(span=sampling_period).mean()

    smrng = avrng.ewm(span=sampling_period*2-1).mean() * multiplier

    filt = range_filter(tr1['source'], smrng)
    filt = pd.DataFrame({'Filt': filt})

    upward = [0]
    downward = [0]

    for i in range(len(filt)):
        len_ward = len(upward)
        if i > 0:
            if filt.iloc[i, 0] > filt.iloc[i-1, 0]:
                upward.append(upward[len_ward-1] + 1)
            elif filt.iloc[i, 0] < filt.iloc[i-1, 0]:
                upward.append(0)
            else:
                upward.append(upward[len_ward-1])

            if filt.iloc[i, 0] < filt.iloc[i-1, 0]:
                downward.append(downward[len_ward-1] + 1)
            elif filt.iloc[i, 0] > filt.iloc[i-1, 0]:
                downward.append(0)
            else:
                downward.append(downward[len_ward-1])

    ft, upw, dnw = pd.Series(filt.iloc[:, 0]), pd.Series(
        upward), pd.Series(downward)
    upw.index, dnw.index = filt.index, filt.index
    return ft, upw, dnw


def exp_moving_average(values, window):
    weights = np.exp(np.linspace(1., 0., window))
    weights /= weights.sum()
    a = np.convolve(values, weights, mode='full')[:len(values)]
    a[:window] = a[window]
    return a


def range_filter(x, r):
    nz_rng = []

    for index in range(len(x)):
        len_rng = len(nz_rng)
        rng = 0
        if len_rng:
            rng = nz_rng[len_rng - 1]

        if x[index] > rng:
            if (x[index] - r[index]) < rng:
                nz_rng.append(rng)
            else:
                nz_rng.append(x[index] - r[index])
        elif (x[index] + r[index] > rng):
            nz_rng.append(rng)
        else:
            nz_rng.append(x[index] + r[index])
    return nz_rng
