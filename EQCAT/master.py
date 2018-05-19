from __future__ import division, print_function
import os
import pandas as pd
import numpy as np
from parse_files import parse_quakes


def instrumental_fit(time_lapse=1, min_pga=0.039):
    quakes = parse_quakes()
    foo = 0
    fname = '../Results/Instrumental/Domains.csv'
    if os.path.isfile(fname):
        foo = 1
    for code, quake in quakes.viewitems():
        if quake.__class__.__name__ == 'DomainEarthquake':
            if foo == 1:
                outputs = pd.read_csv(fname, header=0)
                compiled_codes = list(np.unique(outputs['Code']))
            else:
                compiled_codes = []
            if code not in compiled_codes:
                print(code, quake, quake.proc, quake.mag, quake.shape)
                summary = quake.sesm(time_lapse, min_pga)
                if not summary.empty:
                    # print(list(summary))
                    print(summary)
                    if foo == 1:
                        outputs = outputs.append(summary)
                    else:
                        outputs = summary
                        foo = 1
                    outputs.to_csv('../Results/Instrumental/Domains.csv', index=False)


#instrumental_fit(time_lapse=1, min_pga=0.039)
