import pandas as pd

def st_strategy(source, st):
    st_signal = [0]
    signal = 0
    
    for i in range(len(st)):
        if i > 0:
            if st[i-1] > source[i-1] and st[i] < source[i]:
                if signal != 1:
                    signal = 1
                    st_signal.append(signal)
                else:
                    st_signal.append(0)
            elif st[i-1] < source[i-1] and st[i] > source[i]:
                if signal != -1:
                    signal = -1
                    st_signal.append(signal)
                else:
                    st_signal.append(0)
            else:
                st_signal.append(0)
            
    st = pd.Series(st_signal)
    return st

def rf_strategy(source, filt, upw, dnw):
    rf_signal = [0]
    long_cond = [False]
    short_cond = [False]
    signal = [0]
    
    for i in range(len(source)):
        if i > 0:
            if (source[i] > filt[i] and source[i] > source[i-1] and upw[i] > 0) or \
            (source[i] > filt[i] and source[i] < source[i-1] and upw[i] > 0):
                long_cond.append(True)
            else:
                long_cond.append(False)

            if (source[i] < filt[i] and source[i] < source[i-1] and dnw[i] > 0) or \
            (source[i] < filt[i] and source[i] > source[i-1] and dnw[i] > 0):
                short_cond.append(True)
            else:
                short_cond.append(False)
            
            if long_cond[i]:
                signal.append(1)
            elif short_cond[i]:
                signal.append(-1)
            else:
                signal.append(signal[i-1])

            if long_cond[i] and signal[i-1] == -1:
                rf_signal.append(1)
            elif short_cond[i] and signal[i-1] == 1:
                rf_signal.append(-1)
            else:
                rf_signal.append(0)

    rf = pd.Series(rf_signal)
    return rf

def macd_cross_strategy(macd):
    macd_signal = [0]

    for i in range(len(macd)):
        if i > 0:
            if macd[i] > 0 and macd[i-1] < 0:
                macd_signal.append(1)
            elif macd[i] < 0 and macd[i-1] > 0:
                macd_signal.append(-1)
            else:
                macd_signal.append(0)

    macd = pd.Series(macd_signal)
    return macd

def macdh_cross_strategy(macdh):
    macdh_signal = [0, 0]

    for i in range(len(macdh)):
        if i > 1:
            if macdh[i] > 0 and macdh[i-1] < 0 and macdh[i-1] > macdh[i-2]:
                macdh_signal.append(1)
            elif macdh[i] < 0 and macdh[i-1] > 0 and macdh[i-1] < macdh[i-2]:
                macdh_signal.append(-1)
            else:
                macdh_signal.append(0)

    macdh = pd.Series(macdh_signal)
    return macdh
