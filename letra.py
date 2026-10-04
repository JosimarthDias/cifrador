"""Letra: tempo das palavras e correção do texto da transcrição pela letra certa."""
import re
import unicodedata
import difflib
import numpy as np


def items_from_segments(segments):
    """segments: lista de listas [(palavra, inicio, fim), ...], uma por verso transcrito."""
    items, prev_end = [], None
    for seg in segments:
        ws = [(w.strip(), float(s)) for w, s, e in seg if w.strip()]
        if not ws: continue
        if prev_end is not None and ws[0][1] - prev_end > 4:
            items.append(('blank',))
        items.append(('line', ws))
        prev_end = seg[-1][2]
    return items


def _norm(t):
    t = unicodedata.normalize('NFD', t.lower())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    return ''.join(c for c in t if c.isalnum() or c == ' ').strip()


def _parse_lyrics(letra):
    lines, tags, pend = [], {}, []
    for raw in letra.split('\n'):
        s = raw.strip()
        if not s:
            continue
        m = re.fullmatch(r'\[([^\]]+)\]:?', s) or re.fullmatch(r'#\s*(.+)', s)
        if m:
            pend.append(m.group(1).strip())
            continue
        if pend:
            tags[len(lines)] = pend
            pend = []
        lines.append(s)
    return lines, tags


def _best_span(seg_text, norm_lines, expected):
    best, n = (0.0, None), len(norm_lines)
    for i in range(n):
        for span in (1, 2):
            if i + span > n:
                continue
            cand = ' '.join(norm_lines[i:i + span])
            r = difflib.SequenceMatcher(None, seg_text, cand).ratio()
            if i == expected:
                r += 0.06
            if r > best[0]:
                best = (r, (i, i + span))
    return best


def _retime(tw, lyric_words):
    """tw: [(palavra, inicio)] da transcrição. Devolve inicio de cada palavra da letra."""
    tot = sum(len(_norm(w)) or 1 for w, _ in tw)
    xs, acc = [], 0
    for w, _ in tw:
        xs.append(acc / tot)
        acc += len(_norm(w)) or 1
    ys = [t for _, t in tw]
    xs.append(1.0)
    ys.append(ys[-1] + 0.6)
    ltot = sum(len(_norm(w)) or 1 for w in lyric_words)
    out, acc = [], 0
    for w in lyric_words:
        out.append(float(np.interp(acc / ltot, xs, ys)))
        acc += len(_norm(w)) or 1
    return out


def items_with_correct_lyrics(segments, letra, min_ratio=0.55):
    lines, tags = _parse_lyrics(letra)
    nlines = [_norm(x) for x in lines]
    groups, expected = [], None
    for seg in segments:
        tw = [(w.strip(), float(s)) for w, s, e in seg if w.strip()]
        if not tw:
            continue
        text = _norm(' '.join(w for w, _ in tw))
        r, span = _best_span(text, nlines, expected)
        if span is None or r < min_ratio:
            groups.append({'tw': tw, 'span': None, 'len': len(text)})
            continue
        expected = span[1]
        prev = groups[-1] if groups else None
        if prev and prev['span'] and span[0] < prev['span'][1] and span[1] > prev['span'][0]:
            alvo = len(' '.join(nlines[min(span[0], prev['span'][0]):max(span[1], prev['span'][1])]))
            if prev['len'] < 0.75 * alvo:
                prev['tw'] += tw
                prev['len'] += len(text)
                prev['span'] = (min(span[0], prev['span'][0]), max(span[1], prev['span'][1]))
                continue
        groups.append({'tw': tw, 'span': span, 'len': len(text)})
    items, used_tags, last_t, achou = [], set(), None, 0
    for g in groups:
        t0 = g['tw'][0][1]
        if last_t is not None and t0 - last_t > 4:
            items.append(('blank',))
        if g['span'] is None:
            items.append(('line', g['tw']))
            last_t = g['tw'][-1][1]
            continue
        achou += 1
        for idx in range(g['span'][0], g['span'][1]):
            for tg in tags.get(idx, []):
                if (idx, tg) not in used_tags:
                    used_tags.add((idx, tg))
                    if items and items[-1][0] != 'blank':
                        items.append(('blank',))
                    items.append(('sec', tg))
        lw = []
        for idx in range(g['span'][0], g['span'][1]):
            lw += [(idx, w) for w in lines[idx].split()]
        times = _retime(g['tw'], [w for _, w in lw])
        by_line = {}
        for (idx, w), t in zip(lw, times):
            by_line.setdefault(idx, []).append((w, t))
        for idx in sorted(by_line):
            items.append(('line', by_line[idx]))
        last_t = g['tw'][-1][1]
    return items, achou, len(groups)
