"""Synthesised soundtrack for roadmap.html, timed to its animation events.

Writes soundtrack.wav (48 kHz stereo, 42 s). Every sound is generated here, so
there is nothing to license. Event times mirror the constants in roadmap.html.
"""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
import wave

SR = 48000
DUR = 42.0
N = int(SR * DUR)
rng = np.random.default_rng(11)

# ---- event times (keep in sync with roadmap.html) ----
ARR = [10.4 + i * 5.0 for i in range(5)]          # node arrivals
DEP = [a + 3.8 for a in ARR[:4]]                  # camera moves between nodes
MOVE = 1.2
DIVE_HIT = 4.95                                   # fly into the diamond
FLASH_HIT = 34.45                                 # flash to the white end card
BEAT = 60 / 96                                    # 96 BPM -> a node every 8 beats

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


# ================= arrangement =================
D2, F2, G2, A2, Bb1, C2 = 38, 41, 43, 45, 34, 36

# --- intro on white (0–5 s): airy, bright ---
place(mix, shimmer(1.8), 0.2, gain=0.6, send=0.6)
place(mix, lp(sub_boom(2.0, 60, 40), 200) * 0.35, 0.05)            # soft opening swell
for i, m in enumerate([74, 76, 81, 86]):                             # D E A D bell motif
    place(mix, bell(note(m)), 0.35 + i * 0.32, gain=0.12, pan=(-0.4 + i * 0.27), send=0.7)
place(mix, impact(0.35, 0.6), 1.35, send=0.4)                        # logo fills black
for i in range(8):                                                   # wordmark letters
    place(mix, tick(2600 + i * 90, 0.07), 1.95 + i * 0.045, pan=-0.5 + i * 0.14, send=0.3)
place(mix, whoosh(0.9, 0.18, -0.6, 0.6), 2.0, send=0.4)              # blue shimmer sweep
place(mix, bell(note(81)), 2.5, gain=0.08, send=0.8)
place(mix, pad_chord([62, 66, 69, 74], 5.2, cutoff=3000, attack=0.6, release=0.8), 0.0, gain=0.3, send=0.5)

# --- dive into the diamond ---
place(mix, riser(1.6, 150, 3000, 0.5), DIVE_HIT - 1.6, send=0.3)
place(mix, impact(1.0), DIVE_HIT, send=0.5)

# --- title (5–9.6 s) ---
place(mix, pad_chord([50, 53, 57, 62], 5.6, cutoff=900, attack=1.0), 5.0, gain=0.55, send=0.4)
place(mix, lp(saw(note(D2), int(5.6 * SR), 6), 300) * env_ad(int(5.6 * SR), 0.5, 0.6), 5.0, gain=0.35)
place(mix, impact(0.55, 0.7), 5.6, send=0.5)                          # THE ROAD
place(mix, impact(0.65, 0.8), 5.8, send=0.5)                          # TO MAINNET
place(mix, whoosh(1.1, 0.16, -0.7, 0.7), 6.6, send=0.5)               # light sweep
place(mix, bell(note(69)), 6.3, gain=0.08, send=0.8)
place(mix, riser(1.6, 200, 2600, 0.5), ARR[0] - 1.6, send=0.3)        # warp
place(mix, whoosh(1.4, 0.35, 0.8, -0.8), 9.0, send=0.3)

# --- timeline (10.4–34.45 s): beat + progression ---
chords = [  # (start, end, pad notes, bass root, arp notes)
    (ARR[0], ARR[1], [50, 57, 62, 64, 65], D2, [62, 65, 69, 72, 74, 72, 69, 65]),        # Dm add9
    (ARR[1], ARR[2], [46, 53, 57, 62, 65], Bb1 + 12, [58, 62, 65, 69, 70, 69, 65, 62]),  # Bbmaj7
    (ARR[2], ARR[3], [53, 57, 60, 65, 67], F2, [65, 69, 72, 74, 77, 74, 72, 69]),        # F add9
    (ARR[3], ARR[4], [48, 55, 60, 62, 64], C2 + 12, [60, 64, 67, 72, 74, 72, 67, 64]),   # C add9
    (ARR[4], FLASH_HIT, [45, 52, 57, 62, 64], A2, [57, 62, 64, 69, 74, 69, 64, 62]),      # A sus4 (unresolved: Mainnet ahead)
]
for (s, e, pad, root, arp) in chords:
    dur = e - s + 0.6
    place(mix, pad_chord(pad, dur, cutoff=1100, attack=0.35, release=0.6), s - 0.05, gain=0.42, send=0.35)
    # pulsing sub bass on 8ths, ducked by the kick
    n = int((e - s) * SR)
    t = t_axis(n)
    bass = lp(saw(note(root), n, 6), 260)
    ph = (t % (BEAT / 2)) / (BEAT / 2)
    bass *= np.minimum(1, ph * 6) * (1 - 0.6 * ph)
    place(mix, bass, s, gain=0.42)
    # arpeggio (8ths) with a dotted-8th echo
    k = 0
    tt = s
    while tt < e - 0.05:
        f = note(arp[k % len(arp)] + 12)
        pan = np.sin(k * 0.9) * 0.5
        p = pluck(f, 0.5)
        place(mix, p, tt, gain=0.07, pan=pan, send=0.25)
        place(mix, p, tt + BEAT * 0.75, gain=0.03, pan=-pan, send=0.3)
        k += 1
        tt += BEAT / 2

beat_t = ARR[0]
while beat_t < FLASH_HIT - 0.05:
    b = int(round((beat_t - ARR[0]) / BEAT))
    in_move = any(d - 0.02 <= beat_t < d + MOVE for d in DEP)
    if b % 2 == 0:
        place(mix, kick(), beat_t, gain=0.75)
    if b % 4 == 2 and not in_move:
        place(mix, clap(), beat_t, gain=0.35, send=0.3)
    place(mix, hat(0.18), beat_t + BEAT / 2, pan=0.3)
    if beat_t > ARR[4] + 1.2:                                          # build toward the flash
        place(mix, hat(0.12, 80), beat_t + BEAT / 4, pan=-0.3)
        place(mix, hat(0.12, 80), beat_t + BEAT * 3 / 4, pan=-0.3)
    beat_t += BEAT

for i, a in enumerate(ARR):
    if i < 4:
        place(mix, impact(0.55, 0.8), a - 0.05, send=0.4)             # node lands
        place(mix, bell(note([74, 70, 77, 72][i])), a, gain=0.1, send=0.8)
        for k in range(3):                         # chips pop in
            place(mix, tick(1800 + k * 300, 0.06), a + 0.5 + 0.1 * k, pan=-0.2 + 0.2 * k, send=0.3)
    else:
        # Mainnet is ahead, not reached: a sonar ping instead of a landing
        for k in range(3):
            place(mix, sonar(880), a + k * 1.0, gain=0.12, pan=0.25, send=0.8)
        place(mix, tick(2400, 0.09), a + 0.45, send=0.4)               # UPCOMING badge
        place(mix, sub_boom(2.5, 55, 38), a - 0.05, gain=0.35)
for d in DEP:
    place(mix, whoosh(MOVE + 0.2, 0.32, -0.8, 0.8), d - 0.1, send=0.25)
    place(mix, riser(0.6, 400, 2000, 0.2), d + MOVE - 0.6, send=0.2)

# --- flash into the end card ---
place(mix, riser(1.3, 200, 4000, 0.6), FLASH_HIT - 1.3, send=0.3)
place(mix, impact(0.95, 1.2), FLASH_HIT, send=0.7)
place(mix, bell(note(86), 4.0), FLASH_HIT, gain=0.16, send=0.9)

# --- end card (34.45–42 s): open, hopeful, "the road continues" ---
place(mix, pad_chord([50, 57, 62, 64, 69, 74], DUR - FLASH_HIT, cutoff=2600, attack=0.4, release=3.0),
      FLASH_HIT, gain=0.42, send=0.5)
place(mix, lp(saw(note(D2), int(7.5 * SR), 6), 200) * env_ad(int(7.5 * SR), 0.2, 0.5), FLASH_HIT, gain=0.3)
for k, m in enumerate([62, 66, 69, 74, 76]):                           # recap dots, last one left open
    place(mix, bell(note(m + 12)), FLASH_HIT + 1.3 + k * 0.4, gain=0.11, pan=-0.6 + k * 0.3, send=0.8)
place(mix, shimmer(3.0, 1175), 38.0, gain=0.4, send=0.7)

# ================= reverb + master =================
ir_n = int(3.2 * SR)
it = t_axis(ir_n)
ir = np.vstack([lp(rng.standard_normal(ir_n), 7000), lp(rng.standard_normal(ir_n), 7000)]) * np.exp(-it * 2.1)
ir[:, : int(0.012 * SR)] = 0
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.vstack([fftconvolve(verb_send[c], ir[c])[:N] for c in range(2)])
out = mix + wet * 0.55
out = hp(out, 28)

# fades + soft limiter
t = t_axis(N)
out *= np.minimum(1, t / 0.05) * np.clip((DUR - t) / 2.5, 0, 1) ** 1.5
out /= np.percentile(np.abs(out), 99.95) + 1e-9
out = np.tanh(out * 1.1) * 0.89

pcm = (out.T * 32767).astype(np.int16)
with wave.open('soundtrack.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
rms = [20 * np.log10(np.sqrt(np.mean(out[:, int(a * SR):int(b * SR)] ** 2)) + 1e-9)
       for a, b in [(0, 5), (5, 10), (10, 20), (20, 30), (30, 34.4), (34.4, 40), (40, 42)]]
print('peak', np.abs(out).max().round(3), 'section RMS dBFS', [round(r, 1) for r in rms])
