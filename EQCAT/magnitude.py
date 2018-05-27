from __future__ import division
from math import log, exp
import matplotlib.pyplot as plt


def magnitude_conversion(mag):
    if mag < 0:
        mag = -round(mag, 2)
    else:
        mag = round(0.78 * mag + 1.08, 2)
    return mag


class GutenbergRichter(object):
    def __init__(self, min_mag, b_val, max_mag=8):
        self.b_val = b_val
        self.beta = self.b_val * log(10)
        self.min_mag = magnitude_conversion(min_mag)
        self.a1 = exp(-self.beta * self.min_mag)
        self.max_mag = magnitude_conversion(max_mag)
        self.a2 = exp(-self.beta * self.max_mag)

    def desc(self):
        return "GR(min=" + str(self.min_mag) + ",max=" + str(self.max_mag) + ",beta=" + str(self.beta) + ")"

    def cum_prob(self, mag):
        prob = (self.a1 - exp(-self.beta * mag)) / (self.a1 - self.a2)
        return prob

    def mag_probs(self, mag_step=0.1):
        out = []
        max_min = int(round((self.max_mag - self.min_mag) / mag_step))
        for i in range(1, max_min):
            mag = self.min_mag + i * mag_step
            prob = self.cum_prob(mag) - sum([out[i][1] for i in range(len(out))])
            out += [(mag, prob)]
        out += [(self.max_mag, self.cum_prob(self.max_mag) - sum([out[i][1] for i in range(len(out))]))]
        return out


class CharacteristicMag(object):
    def __init__(self, mag):
        mag = magnitude_conversion(mag)
        self.mag = mag

    def desc(self):
        return "CHAR(mag=" + str(self.mag) + ")"

    def mag_probs(self, mag_step=0.1):
        return [(self.mag, 1)]


class DiscreteMagnitude(object):
    def __init__(self, dico):
        self.dico = dico

    def desc(self):
        out = "DISC("
        for mag_id in self.dico:
            out += "M" + str(magnitude_conversion(self.dico[mag_id]['mag'])) + "P" + str(self.dico[mag_id]['prob']) + ","
        return out[:-1] + ")"

    def mag_probs(self, mag_step=0.1):
        out = []
        for mag_id in self.dico:
            out += [(magnitude_conversion(self.dico[mag_id]['mag']), self.dico[mag_id]['prob'],
                     self.dico[mag_id]['dom_id'])]
        return out


def plot_gutenberg(min_mag, b_val, max_mag=8):
    mag = GutenbergRichter(min_mag, b_val, max_mag)
    print(mag.min_mag, mag.max_mag, mag.beta)
    diff = int(round((mag.max_mag - mag.min_mag) * 10))
    mags = [mag.min_mag + d / 10 for d in range(diff)]
    probs = [mag.cum_prob(m) for m in mags]
    plt.plot(mags, probs)
    plt.ylabel('Probabilite cumulee')
    plt.xlabel('Magnitude des moments')
    plt.show()

# plot_gutenberg(5, 0.9)
