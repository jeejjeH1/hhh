"""Synthesised soundtrack for vaults.html, timed to its animation events.

Writes soundtrack.wav (48 kHz stereo, 26 s). Every sound is generated here, so
there is nothing to license. Event times mirror the T timeline in vaults.html.
"""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
import wave

SR = 48000
DUR = 26.0
N = int(SR * DUR)
rng = np.random.default_rng(5)

# ---- event times (keep in sync with T in vaults.html) ----
SNAP, WORD, DOCK = 1.0, 1.3, 2.3
S2, SAFE_LAND, HIT1, HIT2 = 2.7, 3.7, 4.7, 5.7
IRIS, S3 = 6.7, 7.2
WIPE, S4 = 11.3, 11.7
S4OUT, S5 = 15.8, 16.2
S5OUT, S6, LAND = 19.2, 19.7, 20.7
BEAT = 0.5                                        # 120 BPM, downbeat at S2

mix = np.zeros((2, N))
verb_send = np.zeros((2, N))


def t_axis(n):
    return np.arange(n) / SR


def place(buf, sig, start, gain=1.0, pan=0.0, send=0.0):
    """Add mono or stereo `sig` at time `start` (s) with equal-power pan."""
    i = int(start * SR)
    if i >= N:
        return
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.vstack([sig * l * 1.414, sig * r * 1.414])
    n = min(sig.shape[1], N - i)
    if i < 0:
        sig, n, i = sig[:, -i:], min(sig.shape[1] + i, N), 0
    buf[:, i:i + n] += sig[:, :n] * gain
    if send:
        verb_send[:, i:i + n] += sig[:, :n] * gain * send


def lp(x, f, order=2):
    return sosfilt(butter(order, f, 'low', fs=SR, output='sos'), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, 'high', fs=SR, output='sos'), x)


def bp(x, f1, f2, order=2):
    return sosfilt(butter(order, [f1, f2], 'band', fs=SR, output='sos'), x)


def env_ad(n, a, d_curve=6.0):
    t = np.linspace(0, 1, n)
    na = max(1, int(a * SR))
    e = np.exp(-d_curve * t)
    e[:na] *= np.linspace(0, 1, na)
    return e


def note(f):
    return 440.0 * 2 ** ((f - 69) / 12)


# ---- instruments ----
def saw(freq, n, harmonics=14):
    t = t_axis(n)
    out = np.zeros(n)
    for k in range(1, harmonics + 1):
        if freq * k > SR / 2.2:
            break
        out += np.sin(2 * np.pi * freq * k * t + rng.uniform(0, 6.28)) / k
    return out


def pad_chord(midis, dur, cutoff=1400, attack=1.2, release=1.5):
    n = int(dur * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    for m in midis:
        f = note(m)
        for det, side in ((-0.09, 0), (0.09, 1)):
            v = saw(f * 2 ** (det / 12), n, harmonics=10)
            (L if side == 0 else R)[:] += v
    t = t_axis(n)
    e = np.minimum(1, t / attack) * np.minimum(1, (dur - t) / release).clip(0)
    sig = np.vstack([lp(L, cutoff), lp(R, cutoff)]) * e / (len(midis) * 2)
    return sig


def kick(gain=1.0):
    n = int(0.55 * SR)
    t = t_axis(n)
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 7.5)
    click = hp(rng.standard_normal(n), 2500) * np.exp(-t * 180) * 0.25
    return (np.tanh((body + click) * 1.6)) * gain


def hat(gain=1.0, decay=55):
    n = int(0.12 * SR)
    t = t_axis(n)
    return hp(rng.standard_normal(n), 7000, 4) * np.exp(-t * decay) * gain


def clap(gain=1.0):
    n = int(0.35 * SR)
    t = t_axis(n)
    noise = bp(rng.standard_normal(n), 900, 4000)
    e = np.exp(-t * 18)
    for off in (0.0, 0.011, 0.023):
        k = int(off * SR)
        e[k:k + 200] += 0.6
    return noise * e * 0.5 * gain


def pluck(freq, dur=0.6, bright=3500):
    n = int(dur * SR)
    t = t_axis(n)
    s = (saw(freq, n, 8) * 0.6 + np.sin(2 * np.pi * freq * 2 * t) * 0.3)
    return lp(s, bright) * np.exp(-t * 7) * np.minimum(1, t / 0.003)


def bell(freq, dur=2.5):
    n = int(dur * SR)
    t = t_axis(n)
    s = np.zeros(n)
    for ratio, amp, dec in ((1, 1, 0), (2.76, 0.45, 3), (5.4, 0.25, 6)):
        if freq * ratio < 12000:                      # skip partials that would alias / sound piercing
            s += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t * dec)
    return s * np.exp(-t * 2.2) * np.minimum(1, t / 0.004)


def sub_boom(dur=3.0, f0=70, f1=32):
    n = int(dur * SR)
    t = t_axis(n)
    f = f1 + (f0 - f1) * np.exp(-t * 4)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.tanh(np.sin(ph) * np.exp(-t * 1.6) * 1.8)


def impact(gain=1.0, bright=1.0):
    n = int(3.0 * SR)
    t = t_axis(n)
    noise = lp(rng.standard_normal(n), 6000 * bright) * np.exp(-t * 9) * 0.5
    crack = hp(rng.standard_normal(n), 3000) * np.exp(-t * 60) * 0.5
    return (sub_boom() * 0.9 + noise + crack) * gain


def riser(dur, f_from=200, f_to=2400, gain=1.0):
    n = int(dur * SR)
    t = t_axis(n)
    x = t / dur
    noise = rng.standard_normal(n)
    # sweeping band-pass approximated by blending two filtered versions
    lo, hi = bp(noise, 150, 900), bp(noise, 1500, 9000)
    sweep = lo * (1 - x) + hi * x
    f = f_from * (f_to / f_from) ** (x ** 1.6)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.18
    e = x ** 2.2
    return (sweep * 0.55 + tone) * e * gain


def whoosh(dur=1.2, gain=1.0, pan_from=-0.8, pan_to=0.8):
    n = int(dur * SR)
    t = t_axis(n)
    x = t / dur
    e = np.sin(np.pi * x) ** 2
    noise = bp(rng.standard_normal(n), 300, 5000) * e
    pan = pan_from + (pan_to - pan_from) * x
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.vstack([noise * l, noise * r]) * 1.414 * gain


def tick(freq=2200, gain=1.0):
    n = int(0.06 * SR)
    t = t_axis(n)
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * 90) * gain


def sonar(freq=880, dur=2.2):
    n = int(dur * SR)
    t = t_axis(n)
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * 2.8) * np.minimum(1, t / 0.01)


def shimmer(dur, base=1760, gain=1.0):
    """Glassy granular sparkle used while the logo is drawn."""
    n = int(dur * SR)
    out = np.zeros(n)
    for _ in range(int(dur * 22)):
        f = base * rng.choice([1, 1.5, 2, 2.25, 3])
        g = bell(f, 0.5)[: int(0.5 * SR)] * 0.15
        i = int(rng.uniform(0, dur - 0.5) * SR)
        out[i:i + len(g)] += g * rng.uniform(0.3, 1)
    x = np.linspace(0, 1, n)
    return lp(out, 9000) * np.sin(np.pi * x) * gain




def clink(f0=2600, gain=1.0):
    """Metallic coin hit: inharmonic partials + a tick of noise."""
    n = int(1.4 * SR)
    t = t_axis(n)
    s = np.zeros(n)
    for r, a, d in ((1, 1, 7), (1.51, 0.6, 10), (2.23, 0.45, 13), (2.94, 0.3, 17), (3.76, 0.2, 22)):
        if f0 * r < 15000:
            s += a * np.sin(2 * np.pi * f0 * r * t + rng.uniform(0, 6.28)) * np.exp(-t * d)
    s += hp(rng.standard_normal(n), 5000) * np.exp(-t * 140) * 0.5
    return s * 0.35 * gain


def thud(gain=1.0):
    n = int(0.5 * SR)
    t = t_axis(n)
    f = 60 + 90 * np.exp(-t * 30)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
    knock = bp(rng.standard_normal(n), 300, 1500) * np.exp(-t * 45) * 0.4
    return np.tanh((body + knock) * 1.5) * gain


def whistle(dur, f_from, f_to, gain=1.0):
    """Falling coin: a descending sine glide with a little vibrato."""
    n = int(dur * SR)
    t = t_axis(n)
    x = t / dur
    f = f_from * (f_to / f_from) ** x * (1 + 0.01 * np.sin(2 * np.pi * 7 * t))
    e = np.sin(np.pi * np.clip(x * 1.1, 0, 1)) ** 0.6
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * e * gain


def flutter(dur, rate=13, gain=1.0):
    """Butterfly wings: band-passed noise beating at `rate` Hz."""
    n = int(dur * SR)
    t = t_axis(n)
    am = (0.5 + 0.5 * np.sin(2 * np.pi * rate * t)) ** 3
    x = t / dur
    return bp(rng.standard_normal(n), 400, 3000) * am * np.sin(np.pi * x) * gain


def snare(gain=1.0):
    n = int(0.25 * SR)
    t = t_axis(n)
    return (bp(rng.standard_normal(n), 1200, 7000) * np.exp(-t * 22) * 0.6 +
            np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * 0.4) * gain


# ================= arrangement =================
D2, E2, Fs2, G2, A2, B1 = 38, 40, 42, 43, 45, 35

# --- intro (0–2.7 s): the Startale mark assembles ---
place(mix, shimmer(2.2, 1760), 0.1, gain=0.5, send=0.6)
place(mix, lp(sub_boom(2.0, 60, 40), 200) * 0.3, 0.05)
for i in range(8):                                                   # eight pieces click into place
    place(mix, tick(1900 + i * 160, 0.11), 0.52 + i * 0.07, pan=np.sin(i * 0.8) * 0.6, send=0.35)
place(mix, impact(0.4, 0.6), SNAP - 0.02, send=0.4)
for i, m in enumerate([74, 78, 81, 86]):
    place(mix, bell(note(m)), SNAP + i * 0.06, gain=0.08, pan=-0.3 + i * 0.2, send=0.8)
place(mix, whoosh(0.8, 0.2, -0.7, 0.5), WORD - 0.1, send=0.4)
for i in range(10):                                                  # wordmark letters
    place(mix, tick(2800 + i * 70, 0.05), WORD + 0.05 + i * 0.045, pan=-0.4 + i * 0.09, send=0.3)
place(mix, pad_chord([62, 66, 69, 74, 76], 3.0, cutoff=2600, attack=0.5, release=0.6), 0.0, gain=0.28, send=0.5)
place(mix, riser(0.9, 300, 3000, 0.45), DOCK - 0.5, send=0.3)
place(mix, whoosh(0.6, 0.25, 0.6, -0.8), DOCK, send=0.3)

# --- groove (2.7–19.7 s): 120 BPM, D – A – Bm – G, one bar (2 s) each ---
PROG = [([50, 57, 62, 64, 66], D2, [62, 66, 69, 74, 76, 74, 69, 66]),
        ([45, 52, 57, 61, 64], A2, [61, 64, 69, 73, 76, 73, 69, 64]),
        ([47, 54, 59, 62, 66], B1 + 12, [59, 62, 66, 71, 74, 71, 66, 62]),
        ([43, 50, 55, 59, 62], G2, [59, 62, 67, 71, 74, 71, 67, 62])]
BREATHS = [(IRIS, S3), (WIPE, S4), (S4OUT, S5)]                   # drums drop out under transitions
in_breath = lambda x: any(a - 0.01 <= x < b - 0.01 for a, b in BREATHS)
bar = 0
s = S2
while s < S6 - 1.0 - 0.01:                                           # last bar before the end card is the build
    pad, root, arp = PROG[bar % 4]
    e = s + 2.0
    place(mix, pad_chord(pad, 2.4, cutoff=1500, attack=0.08, release=0.4), s, gain=0.32, send=0.35)
    n = int(2.0 * SR)
    t = t_axis(n)
    bass = lp(saw(note(root), n, 6), 300)
    ph = (t % BEAT) / BEAT                                           # sidechain pump on every beat
    bass *= np.minimum(1, ph * 5) * (1 - 0.5 * ph)
    place(mix, bass, s, gain=0.4)
    for k in range(16):                                              # 8th-note arp with a dotted-8th echo
        tt = s + k * BEAT / 2
        p = pluck(note(arp[k % 8] + 12), 0.45)
        pan = np.sin(k * 0.9) * 0.5
        place(mix, p, tt, gain=0.06, pan=pan, send=0.25)
        place(mix, p, tt + BEAT * 0.75, gain=0.025, pan=-pan, send=0.3)
    bar += 1
    s = e
bt = S2
while bt < S6 - 1.0 - 0.01:
    b = int(round((bt - S2) / BEAT))
    if not in_breath(bt):
        place(mix, kick(), bt, gain=0.7)
        if b % 2 == 1:
            place(mix, clap(), bt, gain=0.32, send=0.3)
        place(mix, hat(0.16), bt + BEAT / 2, pan=0.3)
        place(mix, hat(0.08, 90), bt + BEAT / 4, pan=-0.35)
    bt += BEAT
# build into the end card: snare roll + riser
for k in range(16):
    tt = S6 - 1.0 + k * (1.0 / 16)
    place(mix, snare(0.12 + 0.3 * k / 16), tt, pan=0.1, send=0.3)
place(mix, riser(1.6, 200, 4200, 0.6), S6 - 1.6, send=0.3)

# --- S2: safe + two coins ---
place(mix, whoosh(0.8, 0.25, 0.8, 0.3), SAFE_LAND - 0.8, send=0.3)
place(mix, thud(0.7), SAFE_LAND - 0.02, pan=0.35, send=0.3)
for i in range(4):                                                   # headline words
    place(mix, tick(2300 + i * 200, 0.06), S2 + 0.25 + i * 0.13, pan=-0.4, send=0.3)
for h in (HIT1, HIT2):
    place(mix, whistle(0.95, 1900, 650, 0.05), h - 0.95, pan=0.4, send=0.5)
    place(mix, whoosh(0.5, 0.16, 0.35, 0.35), h - 0.45, send=0.2)
    place(mix, thud(0.55), h, pan=0.35, send=0.3)
    place(mix, clink(2650, 0.9), h, pan=0.35, send=0.5)
    place(mix, clink(3350, 0.55), h + 0.07, pan=0.45, send=0.5)
    place(mix, bell(note(86 if h == HIT1 else 90), 1.5), h + 0.05, gain=0.07, pan=0.2, send=0.8)
place(mix, whoosh(0.35, 0.12, -0.7, -0.3), HIT2 + 0.12, send=0.2)   # marker swoosh

# --- iris into vault 1 ---
place(mix, riser(0.9, 300, 3200, 0.45), IRIS - 0.6, send=0.3)
place(mix, whoosh(0.6, 0.35, 0.5, -0.2), IRIS, send=0.3)
place(mix, impact(0.85, 1.0), S3 - 0.02, send=0.5)
for i in range(7):                                                   # vault 1 copy & chips pop in
    place(mix, tick(2000 + i * 180, 0.06), S3 + 0.3 + i * 0.18, pan=-0.5 + i * 0.05, send=0.3)
for i in range(4):                                                   # collateral coins join the orbit
    place(mix, clink(3600 + i * 300, 0.18), S3 + 0.75 + i * 0.14, pan=0.5, send=0.6)

# --- wipe into vault 2 ---
place(mix, whoosh(0.5, 0.4, -0.9, 0.9), WIPE - 0.05, send=0.25)
place(mix, whoosh(0.5, 0.3, -0.9, 0.9), S4, send=0.25)
place(mix, impact(0.5, 0.8), S4 - 0.02, send=0.4)
r = np.random.default_rng(91)                                        # one click per voxel, bottom layers first
for iy in range(4):
    for _ in range(16):
        tt = S4 + 0.15 + iy * 0.13 + r.uniform(0, 0.28) + 0.35
        place(mix, tick(1300 + iy * 350 + r.uniform(0, 200), 0.045), tt, pan=0.4 + r.uniform(-0.2, 0.2), send=0.25)
place(mix, bell(note(81), 1.5), S4 + 1.4, gain=0.07, pan=0.4, send=0.8)
for i in range(7):
    place(mix, tick(2000 + i * 180, 0.06), S4 + 0.3 + i * 0.18, pan=-0.5, send=0.3)

# --- Powered by Morpho ---
place(mix, whoosh(0.5, 0.3, 0.2, -0.6), S4OUT, send=0.3)
place(mix, impact(0.7, 0.9), S5 + 0.13, send=0.6)
place(mix, flutter(0.9, 13, 0.18), S5 + 0.05, send=0.4)
for i, m in enumerate([69, 74, 78]):
    place(mix, bell(note(m + 12), 2.0), S5 + 0.15 + i * 0.09, gain=0.08, pan=-0.3 + 0.3 * i, send=0.8)
for i in range(2):
    place(mix, tick(2400, 0.07), S5 + 0.6 + i * 0.12, pan=-0.5 + i, send=0.3)
place(mix, flutter(0.7, 18, 0.2), S5OUT, send=0.4)

# --- end card ---
place(mix, impact(1.0, 1.2), S6 - 0.02, send=0.7)
place(mix, pad_chord([50, 57, 62, 66, 69, 74], DUR - S6, cutoff=2800, attack=0.3, release=3.0), S6, gain=0.4, send=0.5)
place(mix, lp(saw(note(D2), int(6.3 * SR), 6), 220) * env_ad(int(6.3 * SR), 0.05, 0.6), S6, gain=0.35)
place(mix, thud(0.6), S6 + 0.6, pan=0.4, send=0.3)                    # safe lands
for i in range(4):
    place(mix, tick(2200 + i * 150, 0.06), S6 + 0.25 + i * 0.1, pan=-0.5, send=0.3)
place(mix, whistle(0.85, 2000, 700, 0.05), LAND - 0.85, pan=0.45, send=0.5)
place(mix, thud(0.55), LAND, pan=0.45, send=0.3)
place(mix, clink(2650, 1.0), LAND, pan=0.45, send=0.6)
place(mix, clink(3350, 0.6), LAND + 0.07, pan=0.5, send=0.6)
for k, m in enumerate([74, 78, 81, 86]):                              # "ka-ching" sparkle
    place(mix, bell(note(m + 12), 2.0), LAND + 0.12 + k * 0.08, gain=0.07, pan=0.2 + 0.1 * k, send=0.8)
place(mix, pluck(note(86), 0.8), LAND + 0.15, gain=0.12, send=0.5)    # CTA pops
for i in range(4):                                                    # partner logos
    place(mix, tick(1800 + i * 250, 0.07), LAND + 0.4 + i * 0.1, pan=-0.6 + 0.4 * i, send=0.3)
bt = S6                                                                # soft half-time pulse under the end card
while bt < DUR - 2.2:
    place(mix, kick(0.45), bt)
    place(mix, hat(0.08), bt + BEAT, pan=0.3)
    bt += BEAT * 2
place(mix, shimmer(3.5, 1175), 21.8, gain=0.35, send=0.7)

# ================= reverb + master =================
ir_n = int(2.6 * SR)
it = t_axis(ir_n)
ir = np.vstack([lp(rng.standard_normal(ir_n), 7000), lp(rng.standard_normal(ir_n), 7000)]) * np.exp(-it * 2.4)
ir[:, : int(0.012 * SR)] = 0
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(verb_send[c], ir[c])[:N] for c in range(2)])
out = mix + wet * 0.5
out = hp(out, 28)

t = t_axis(N)
out *= np.minimum(1, t / 0.03) * np.clip((DUR - t) / 2.0, 0, 1) ** 1.5
out /= np.percentile(np.abs(out), 99.95) + 1e-9
out = np.tanh(out * 1.1) * 0.89

pcm = (out.T * 32767).astype(np.int16)
with wave.open('soundtrack.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
rms = [20 * np.log10(np.sqrt(np.mean(out[:, int(a * SR):int(b * SR)] ** 2)) + 1e-9)
       for a, b in [(0, 2.7), (2.7, 7.2), (7.2, 11.7), (11.7, 16.2), (16.2, 19.7), (19.7, 24), (24, 26)]]
print('peak', np.abs(out).max().round(3), 'section RMS dBFS', [round(r, 1) for r in rms])
