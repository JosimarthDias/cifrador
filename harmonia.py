"""Detecção de tom, modulações e acordes a partir do áudio."""
import numpy as np
import librosa
from scipy.ndimage import uniform_filter1d

SHARP = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
FLAT  = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
KS_MAJ = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
KS_MIN = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
SR, HOP = 22050, 2048
FLAT_SCALES = {1, 3, 5, 6, 8, 10}   # escalas (tom maior relativo) que usam bemóis


# ---------------------------------------------------------- utilidades
def viterbi(E, p_stay):
    T, N = E.shape
    ls, lw = np.log(p_stay), np.log((1 - p_stay) / (N - 1))
    dp = E[0].copy()
    back = np.zeros((T, N), dtype=np.int32)
    idx = np.arange(N)
    for t in range(1, T):
        b = int(dp.argmax()); bv = dp[b]
        stay = dp + ls; sw = bv + lw
        keep = stay >= sw
        back[t] = np.where(keep, idx, b)
        dp = np.where(keep, stay, sw) + E[t]
    path = np.zeros(T, dtype=np.int32)
    path[-1] = int(dp.argmax())
    for t in range(T - 1, 0, -1):
        path[t - 1] = back[t, path[t]]
    return path


def to_segments(path, times_edges, ids=None):
    segs, st = [], 0
    for i in range(1, len(path) + 1):
        if i == len(path) or path[i] != path[st]:
            segs.append({'start': float(times_edges[st]), 'end': float(times_edges[i]), 'id': int(path[st])})
            st = i
    return segs


def merge_short(segs, min_dur):
    def join(ss):
        out = []
        for s in ss:
            if out and out[-1]['id'] == s['id']:
                out[-1]['end'] = s['end']
            else:
                out.append(dict(s))
        return out
    segs = join(segs)
    while len(segs) > 1:
        d = [s['end'] - s['start'] for s in segs]
        i = int(np.argmin(d))
        if d[i] >= min_dur:
            break
        L = segs[i - 1] if i > 0 else None
        R = segs[i + 1] if i + 1 < len(segs) else None
        if L is None: tgt = R
        elif R is None: tgt = L
        else: tgt = L if (L['end'] - L['start']) >= (R['end'] - R['start']) else R
        if tgt is L: L['end'] = segs[i]['end']
        else: R['start'] = segs[i]['start']
        segs.pop(i)
        segs = join(segs)
    return segs


# ---------------------------------------------------------- harmonia
# nome: (intervalos, pesos, nível mínimo, penalidade)
# A penalidade faz um acorde mais "exótico" só ganhar quando há evidência clara no áudio.
QUAL = {
    '':       ([0, 4, 7],        [1, .8, .7],         1,  0.0),
    'm':      ([0, 3, 7],        [1, .8, .7],         1,  0.0),
    '7':      ([0, 4, 7, 10],    [1, .8, .7, .7],     2, -0.02),
    'm7':     ([0, 3, 7, 10],    [1, .8, .7, .7],     2, -0.02),
    'maj7':   ([0, 4, 7, 11],    [1, .8, .7, .7],     2, -0.03),
    'sus4':   ([0, 5, 7],        [1, .85, .7],        3, -0.07),
    'sus2':   ([0, 2, 7],        [1, .85, .7],        3, -0.07),
    '7sus4':  ([0, 5, 7, 10],    [1, .85, .7, .7],    3, -0.08),
    'add9':   ([0, 2, 4, 7],     [1, .6, .8, .7],     3, -0.07),
    '9':      ([0, 2, 4, 7, 10], [1, .6, .8, .7, .7], 3, -0.08),
    'm9':     ([0, 2, 3, 7, 10], [1, .6, .8, .7, .7], 3, -0.08),
    'maj9':   ([0, 2, 4, 7, 11], [1, .6, .8, .7, .7], 3, -0.09),
    'm7(b5)': ([0, 3, 6, 10],    [1, .8, .8, .7],     3, -0.05),
    'dim':    ([0, 3, 6],        [1, .8, .8],         3, -0.07),
    'dim7':   ([0, 3, 6, 9],     [1, .8, .8, .8],     3, -0.09),
    'aug':    ([0, 4, 8],        [1, .8, .8],         3, -0.10),
}


def chord_states(nivel=3):
    states, vecs, prior = [], [], []
    for suf, (iv, w, niv, pen) in QUAL.items():
        if niv > nivel:
            continue
        for root in range(12):
            v = np.zeros(12)
            for i, wt in zip(iv, w): v[(root + i) % 12] = wt
            states.append((root, suf)); vecs.append(v / np.linalg.norm(v)); prior.append(pen)
    return states, np.array(vecs), np.array(prior)


def scale_bonus(states):
    """bonus[r, s]: favorece acordes da escala cujo tom maior relativo é r."""
    B = np.zeros((12, len(states)))
    for r in range(12):
        maj = {r, (r + 5) % 12, (r + 7) % 12}
        mnr = {(r + 2) % 12, (r + 4) % 12, (r + 9) % 12}
        tonsub = {r, (r + 5) % 12}
        dom, dimr = (r + 7) % 12, (r + 11) % 12
        for s, (root, suf) in enumerate(states):
            b = 0.0
            if suf == '' and root in maj: b = .06
            elif suf == 'm' and root in mnr: b = .06
            elif suf == 'maj7' and root in tonsub: b = .04
            elif suf in ('7', '9', '7sus4') and root == dom: b = .05
            elif suf in ('m7', 'm9') and root in mnr: b = .04
            elif suf in ('add9', 'sus2', 'sus4') and root in maj: b = .03
            elif suf == 'maj9' and root in tonsub: b = .03
            elif suf in ('m7(b5)', 'dim') and root == dimr: b = .03
            B[r, s] = b
    return B


def bass_chroma(y, sr):
    """Energia das notas graves por classe de nota (para achar acordes com baixo invertido)."""
    Cq = np.abs(librosa.cqt(y, sr=sr, hop_length=HOP, fmin=librosa.note_to_hz('E1'), n_bins=36, bins_per_octave=12))
    B = np.zeros((12, Cq.shape[1]))
    for i in range(36):
        B[(4 + i) % 12] += Cq[i]
    return B


def _norm_rows(X):
    X = X - X.mean(axis=1, keepdims=True)
    return X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-9)


def analyze_harmony(path, nivel=3, usar_baixo=True, min_key_sec=25.0, min_chord_sec=1.2, log=None):
    log = log or (lambda *a: None)
    log('Lendo o áudio...')
    y, sr = librosa.load(path, sr=SR, mono=True)
    dur = len(y) / sr
    try:
        log('Separando a parte harmônica (reduz o ruído da bateria)...')
        yh = librosa.effects.harmonic(y, margin=3.0)
    except Exception:
        yh = y
    log('Calculando o cromagrama...')
    # ignora as notas muito graves (o baixo é analisado à parte, para os acordes invertidos)
    C = librosa.feature.chroma_cqt(y=yh, sr=sr, hop_length=HOP, fmin=librosa.note_to_hz('C3'), n_octaves=5)   # (12, T)
    C = uniform_filter1d(C, size=3, axis=1, mode='nearest')
    energy = np.linalg.norm(C, axis=0)
    C = C / np.maximum(energy, 1e-9)
    quiet = energy < 0.12 * np.median(energy)
    C[:, quiet] = 1 / np.sqrt(12)
    T = C.shape[1]
    edges = np.concatenate([[0], (np.arange(1, T) - 0.5) * HOP / sr, [dur]])

    # ---- tom por trecho (escala = tom maior relativo) e modulações
    log('Detectando tom e modulações...')
    win = max(3, int(12 * sr / HOP))
    smooth = uniform_filter1d(C, size=win, axis=1, mode='nearest').T      # (T, 12)
    X = _norm_rows(smooth)
    sc = np.zeros((T, 12)); is_minor = np.zeros((T, 12), dtype=bool)
    for r in range(12):
        pm = np.roll(KS_MAJ, r); pn = np.roll(KS_MIN, (r + 9) % 12)
        pm = (pm - pm.mean()) / np.linalg.norm(pm - pm.mean())
        pn = (pn - pn.mean()) / np.linalg.norm(pn - pn.mean())
        a, b = X @ pm, X @ pn
        sc[:, r] = np.maximum(a, b); is_minor[:, r] = b > a
    spath = viterbi(4.0 * sc, 0.998)
    ksegs = merge_short(to_segments(spath, edges), min_key_sec)
    for s in ksegs:
        r = s['id']
        a = int(np.searchsorted(edges, s['start'], side='right')) - 1
        b = max(a + 1, int(np.searchsorted(edges, s['end'], side='left')))
        m = C[:, a:b].mean(axis=1)
        pm = np.roll(KS_MAJ, r); pn = np.roll(KS_MIN, (r + 9) % 12)
        ca = np.corrcoef(m, pm)[0, 1]; cb = np.corrcoef(m, pn)[0, 1]
        s['r'] = r; s['minor'] = bool(cb > ca)
    # escala dominante da música decide bemóis/sustenidos para todos os acordes
    tot = {}
    for s in ksegs: tot[s['r']] = tot.get(s['r'], 0) + s['end'] - s['start']
    main_r = max(tot, key=tot.get)
    names = FLAT if main_r in FLAT_SCALES else SHARP
    for s in ksegs:
        tn = (s['r'] + 9) % 12 if s['minor'] else s['r']
        tab = FLAT if s['r'] in FLAT_SCALES else SHARP
        s['name'] = tab[tn] + ('m' if s['minor'] else '')

    # ---- acordes, usando o tom de cada trecho como pista
    log('Detectando os acordes...')
    states, vecs, prior = chord_states(nivel)
    B = scale_bonus(states)
    E = 10.0 * (C.T @ vecs.T + B[spath] + prior[None, :])
    cpath = viterbi(E, 0.92)
    csegs = merge_short(to_segments(cpath, edges), min_chord_sec)
    BC = None
    if usar_baixo:
        try:
            log('Procurando acordes com baixo invertido...')
            BC = bass_chroma(y, sr)
            nb = min(BC.shape[1], T)
        except Exception:
            BC = None
    for s in csegs:
        s['root'], s['suf'] = states[s['id']]
        s['name'] = names[s['root']] + s['suf']
        if BC is not None and s['end'] - s['start'] >= 1.0:
            a = int(np.searchsorted(edges, s['start'], side='right')) - 1
            b = max(a + 1, int(np.searchsorted(edges, s['end'], side='left')))
            a, b = min(a, nb - 1), min(b, nb)
            bass = BC[:, a:b].mean(axis=1)
            if bass.sum() > 0:
                pc = int(bass.argmax())
                rel = (pc - s['root']) % 12
                # notas vizinhas "vazam" no CQT grave, então o baixo precisa se destacar das notas distantes
                outras = [bass[i] for i in range(12) if i not in (pc, (pc + 1) % 12, (pc - 1) % 12)]
                if pc != s['root'] and rel in QUAL[s['suf']][0] and bass[pc] >= 2.0 * max(outras):
                    s['name'] += '/' + names[pc]
    return {'duration': dur, 'keys': ksegs, 'chords': csegs, 'names': names}
