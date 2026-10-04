"""Montagem da cifra: acordes em cima da letra."""


def _dedupe(names):
    out = []
    for n in names:
        if not out or out[-1] != n:
            out.append(n)
    return out


def _chords_between(csegs, a, b, min_ov=0.8):
    nomes = []
    for c in csegs:
        if min(c['end'], b) - max(c['start'], a) >= min_ov:
            nomes.append(c['name'])
    return _dedupe(nomes)


def place_chords(ws, ls, scope_end, csegs):
    """Decide em qual palavra do verso cada acorde entra."""
    evs = []
    for c in csegs:
        ov = min(c['end'], scope_end) - max(c['start'], ls)
        if c['end'] > ls and c['start'] < scope_end and ov >= 0.35:
            evs.append(c)
    if not evs:
        evs = [c for c in csegs if c['start'] <= ls < c['end']][:1]
    assign, used, last = {}, set(), None
    for c in evs:
        if c['name'] == last:
            continue
        if c['start'] <= ls:
            k0 = 0
        else:
            k0 = min(range(len(ws)), key=lambda j: abs(ws[j][1] - c['start']))
        while k0 in used and k0 < len(ws) - 1:
            k0 += 1
        if k0 in used:
            continue
        used.add(k0)
        assign[k0] = c['name']
        last = c['name']
    return assign


def sheet_blocks(items, harmony):
    csegs, ksegs, dur = harmony['chords'], harmony['keys'], harmony['duration']
    lines = [(i, it[1]) for i, it in enumerate(items) if it[0] == 'line']
    if not lines:
        return []
    out = []
    first_start = lines[0][1][0][1]
    if ksegs:
        out.append(('text', 'Tom: ' + ksegs[0]['name']))
        out.append(('text', ''))
    intro = _chords_between(csegs, 0, first_start)
    if intro and first_start > 3:
        out.append(('text', '[Intro]'))
        out.append(('chords', intro[:12]))
        out.append(('text', ''))

    def key_at(t):
        for k in ksegs:
            if k['start'] <= t < k['end']:
                return k
        return ksegs[-1]

    cur_scale = key_at(first_start)['r'] if ksegs else None
    line_pos = {i: n for n, (i, _) in enumerate(lines)}
    for i, it in enumerate(items):
        if it[0] == 'blank':
            out.append(('text', ''))
            continue
        if it[0] == 'sec':
            out.append(('text', '[' + it[1] + ']'))
            continue
        ws = it[1]
        n = line_pos[i]
        ls = ws[0][1]
        le = ws[-1][1] + 0.6
        nxt = None
        if n + 1 < len(lines):
            nxt = lines[n + 1][1][0][1]
            if nxt > ls:
                le = min(le, nxt)
        k = key_at(ls)
        if cur_scale is not None and k['r'] != cur_scale:
            out.append(('text', '[Modulação para ' + k['name'] + ']'))
            cur_scale = k['r']
        assign = place_chords(ws, ls, le + 0.4, csegs)
        out.append(('pair', [(w, assign.get(j)) for j, (w, _) in enumerate(ws)]))
        if nxt is not None and nxt - (ws[-1][1] + 0.6) > 6:
            gap = _chords_between(csegs, ws[-1][1] + 0.6, nxt)
            if gap:
                out.append(('text', ''))
                out.append(('text', '[Instrumental]'))
                out.append(('chords', gap[:12]))
                out.append(('text', ''))
    last_end = lines[-1][1][-1][1] + 0.6
    if dur - last_end > 4:
        fim = _chords_between(csegs, last_end, dur)
        if fim:
            out.append(('text', ''))
            out.append(('text', '[Final]'))
            out.append(('chords', fim[:8]))
    return out


def render_blocks(out):
    above, inline = [], []
    for kind, val in out:
        if kind == 'text':
            above.append(val)
            inline.append(val)
        elif kind == 'chords':
            s = ''
            for n in val:
                s += n + ' ' * max(2, 7 - len(n))
            above.append(s.rstrip())
            inline.append(s.rstrip())
        else:
            ch, ly, parts = '', '', []
            for w, c in val:
                if c:
                    if ch and len(ch) >= len(ly):
                        ly = ly.ljust(len(ch) + 1)
                    ch = ch.ljust(len(ly)) + c
                    parts.append('[' + c + ']' + w)
                else:
                    parts.append(w)
                ly += w + ' '
            above.append(ch.rstrip())
            above.append(ly.rstrip())
            inline.append(' '.join(parts))
    return '\n'.join(above), '\n'.join(inline)


def make_sheet(items, harmony):
    return render_blocks(sheet_blocks(items, harmony))
