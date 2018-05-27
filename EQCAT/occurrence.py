from math import exp, sqrt
from scipy.stats import norm


class OccurrenceProcess(object):
    def __init__(self):
        self.type = 'Process'

    def occurrence(self, unif, time_lapse=1):
        prob = self.occ_proba(time_lapse)
        if unif <= prob:
            return True
        else:
            return False


class PoissonProcess(OccurrenceProcess):
    def __init__(self, avract):
        super(self.__class__, self).__init__()
        self.avract = float(avract)

    def desc(self):
        return "P(lmbd=" + str(self.avract) + ")"

    def occ_proba(self, time_lapse):
        lambd = 1 / self.avract * time_lapse
        prob = 1 - exp(-lambd)
        return prob


class BrownianPTProcess(OccurrenceProcess):
    def __init__(self, avract, newact, alpha):
        super(self.__class__, self).__init__()
        self.avract = float(avract)
        self.newact = float(newact)
        self.alpha = float(alpha)

    def desc(self):
        return "BPT(mu=" + str(self.avract) + ",t0=" + str(self.newact) + ",alph=" + str(self.alpha) + ")"

    def u1(self, t):
        return (sqrt(t / self.avract) - sqrt(self.avract / t)) / self.alpha

    def u2(self, t):
        return (sqrt(t / self.avract) + sqrt(self.avract / t)) / self.alpha

    def cdf(self, t):
        return norm.cdf(self.u1(t)) + exp(2 / self.alpha**2) * norm.cdf(-self.u2(t))

    def occ_proba(self, time_lapse):
        return (self.cdf(self.newact + time_lapse) - self.cdf(self.newact))/(1 - self.cdf(self.newact))


class YearFreqProcess(OccurrenceProcess):
    def __init__(self, year_freq):
        super(self.__class__, self).__init__()
        self.freq = year_freq

    def desc(self):
        return "FRQ(" + str(self.freq) + ")"

    def occ_proba(self, time_lapse):
        return self.freq * time_lapse


class MultiSegmentProcess(OccurrenceProcess):
    def __init__(self, segments):
        super(self.__class__, self).__init__()
        self.segments = segments

    def desc(self):
        out = "MULTI("
        for seg in self.segments:
            out += seg.code + ","
        return out[:-1] + ")"

    def occ_proba(self, time_lapse):
        proba = 1
        for seg in self.segments:
            proba = proba * seg.proc.occ_proba(time_lapse)
        return proba
