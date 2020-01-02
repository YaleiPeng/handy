import pandas as pd
import numpy as np
from jellyfish import soundex

dd = pd.read_csv("dma_mapping.csv")
ref = dd.DMA

def clean(x):
    for _s in list(",.<>[]{}?!@#$%^&*-=+~`;:_/"):
        x = x.replace(_s," ")
    while "  " in x:
        x = x.replace("  ", " ")
        if x[0] == " ":
            x = x[1:]
        if x[-1] == " ":
            x = x[:-1]
    return x.upper()


def match_dma(x, ref=dd.DMA):
    x_clean = clean(x)
    ref = {
        d: {
            'clean': clean(d), 
            'prounce': soundex(clean(d)),
            'clean_w': clean(d).split(" "), 
            'prounce_w': [soundex(_d) for _d in clean(d).split(" ")]
        } for d in ref
    }
    
    def match_str_or_prounce(str1, str2):
        return str1 == str2 or soundex(str1) == soundex(str2)

    # exact match
    exact_match = [r for r in ref if x_clean == ref[r]['clean']]
    if len(exact_match) == 1:
#         print(f"EXACT MATCH: {x} --> {exact_match[0]}")
        return exact_match[0]
    if len(exact_match) > 1:
        raise Exception(f"Exact Matched > 1: '{x}' --> {exact_match}")        
    
    
    # word-level match
    scores = {}
    x_clean_w = x_clean.split(" ")

    for r in ref:
        score = 0
        clean_w = ref[r]['clean_w']
#         prounce_w = ref[r]['prounce_w']
        loc_ind = [np.nan] * len(x_clean_w)
        cursor = 0
        score_flag = False
        for i_x, w in enumerate(x_clean_w):
            for i_r, r_w in enumerate(clean_w):
                if match_str_or_prounce(w, r_w):
                    if i_r >= cursor:
                        loc_ind[i_x] = i_r
                        cursor = i_r
                        score_flag = True
        if score_flag:
            loc_ind = np.array(loc_ind)
            score = np.nansum(1/(loc_ind + 1)) + sum([int(~np.isnan(e)) for e in loc_ind])
            scores[r] = {x: score}
    
    if len(scores) == 1:
        return list(scores)[0]
    elif len(scores) > 1:
        _df = pd.DataFrame.from_dict(scores, orient='index').sort_values(by=x, ascending=False)
        pick = list(_df.index)[0]
        print(f"** SOFT MATCH: {x} --> {pick}")
        display(_df)       
        return pick
    else:
        # raise Exception(f"No match founded for '{x}'.")
        print(f"No match founded for '{x}'.")
