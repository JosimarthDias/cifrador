"""Geração do PDF da cifra: logotipo, título, artista, álbum e desenhos dos acordes de violão."""
import os
import re
from dataclasses import dataclass

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

AZUL = (0.11, 0.31, 0.85)
VERDE = (0.06, 0.46, 0.43)
CINZA = (0.35, 0.38, 0.45)
CHORD_RE = re.compile(r'^([A-G][#b]?)(m7\(b5\)|maj7|maj9|m7|m9|7sus4|sus4|sus2|dim7|dim|aug|add9|m|9|7|)(/[A-G][#b]?)?$')
NOTAS = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}


@dataclass
class Meta:
    titulo: str = "Sem título"
    artista: str = ""
    album: str = ""


# ---------------------------------------------------------- formas de acorde (violão)
# 6 casas (da corda 6 grave para a 1 aguda): -1 = não toca, 0 = solta
ABERTOS = {
    'C': [-1,3,2,0,1,0], 'D': [-1,-1,0,2,3,2], 'G': [3,2,0,0,0,3],
    'Dm': [-1,-1,0,2,3,1], 'C7': [-1,3,2,3,1,0], 'D7': [-1,-1,0,2,1,2],
    'G7': [3,2,0,0,0,1], 'B7': [-1,2,1,2,0,2],
    'Cmaj7': [-1,3,2,0,0,0], 'Fmaj7': [-1,-1,3,2,1,0], 'Dmaj7': [-1,-1,0,2,2,2],
    'Gmaj7': [3,2,0,0,0,2], 'Dsus4': [-1,-1,0,2,3,3], 'Dsus2': [-1,-1,0,2,3,0],
}
# formas móveis: relativas à casa-base (nota fundamental na corda 6 ou na corda 5)
FORMA_E = {'': [0,2,2,1,0,0], 'm': [0,2,2,0,0,0], '7': [0,2,0,1,0,0], 'm7': [0,2,0,0,0,0],
           'maj7': [0,2,1,1,0,0], 'sus4': [0,2,2,2,0,0], 'sus2': [0,2,4,4,0,0], '7sus4': [0,2,0,2,0,0],
           'dim': [0,1,2,0,-1,-1], 'm7(b5)': [0,1,0,0,-1,-1], 'aug': [0,3,2,1,1,0],
           'add9': [0,2,2,1,0,2], '9': [0,2,0,1,0,2], 'm9': [0,2,0,0,0,2], 'maj9': [0,2,1,1,0,2]}
FORMA_A = {'': [-1,0,2,2,2,0], 'm': [-1,0,2,2,1,0], '7': [-1,0,2,0,2,0], 'm7': [-1,0,2,0,1,0],
           'maj7': [-1,0,2,1,2,0], 'sus4': [-1,0,2,2,3,0], 'sus2': [-1,0,2,2,0,0], '7sus4': [-1,0,2,0,3,0],
           'dim': [-1,0,1,2,1,-1], 'm7(b5)': [-1,0,1,0,1,-1], 'dim7': [-1,0,1,2,1,2], 'aug': [-1,0,3,2,2,1],
           'add9': [-1,0,2,4,2,0], '9': [-1,0,2,4,2,3], 'm9': [-1,0,2,4,1,3]}
SUFIXOS = ['', 'm', '7', 'm7', 'maj7', 'sus4', 'sus2', '7sus4', 'dim', 'm7(b5)', 'dim7', 'aug', 'add9', '9', 'm9', 'maj9']

def nome_da_nota(raiz):
    return [k for k, v in NOTAS.items() if v == raiz]

def forma_acorde(raiz, suf):
    """Devolve (casas, pestana_na_casa) para a raiz (0-11) e o sufixo do acorde."""
    for n in nome_da_nota(raiz):
        if n + suf in ABERTOS:
            return ABERTOS[n + suf], 0
    cand = []
    if suf in FORMA_E:
        b = (raiz - 4) % 12
        cand.append((b, 0, [(f + b if f >= 0 else -1) for f in FORMA_E[suf]]))
    if suf in FORMA_A:
        b = (raiz - 9) % 12
        cand.append((b, 1, [(f + b if f >= 0 else -1) for f in FORMA_A[suf]]))
    base, _, casas = min(cand, key=lambda c: (c[0], c[1]))
    return casas, base


def desenhar_acorde(c, x, y, nome, raiz, suf, w=24*mm, h=30*mm):
    """x,y = canto superior esquerdo do desenho."""
    casas, pest = forma_acorde(raiz, suf)
    c.setFillColorRGB(*AZUL); c.setFont('Helvetica-Bold', 11)
    c.drawCentredString(x + w / 2, y + 3 * mm, nome)
    gx, gy = x + 3 * mm, y - 3 * mm
    gw, gh = w - 6 * mm, h - 8 * mm
    esp_c, esp_f = gw / 5, gh / 5
    pos = [f for f in casas if f > 0]
    inicio = 1 if (not pos or max(pos) <= 4) else min(pos)
    c.setStrokeColorRGB(0.25, 0.28, 0.35); c.setFillColorRGB(0.1, 0.12, 0.18)
    c.setLineWidth(0.6)
    for i in range(6):
        c.line(gx + i * esp_c, gy, gx + i * esp_c, gy - gh)
    for j in range(6):
        c.setLineWidth(2.2 if (j == 0 and inicio == 1) else 0.6)
        c.line(gx, gy - j * esp_f, gx + gw, gy - j * esp_f)
    if inicio > 1:
        c.setFont('Helvetica', 7); c.setFillColorRGB(*CINZA)
        c.drawString(gx + gw + 1 * mm, gy - esp_f * 0.65, f'{inicio}ª')
    # pestana
    if pest > 0:
        cordas = [i for i, f in enumerate(casas) if f == pest]
        if len(cordas) >= 2:
            lin = pest - inicio + 1
            yy = gy - (lin - 0.5) * esp_f
            c.setFillColorRGB(0.1, 0.12, 0.18)
            c.roundRect(gx + cordas[0] * esp_c - 1.6 * mm, yy - 1.5 * mm,
                        (cordas[-1] - cordas[0]) * esp_c + 3.2 * mm, 3 * mm, 1.5 * mm, stroke=0, fill=1)
    c.setFillColorRGB(0.1, 0.12, 0.18)
    for i, f in enumerate(casas):
        cx = gx + i * esp_c
        if f == -1:
            c.setFont('Helvetica-Bold', 8); c.drawCentredString(cx, gy + 1.2 * mm, 'x')
        elif f == 0:
            c.setLineWidth(0.7); c.circle(cx, gy + 2 * mm, 1.1 * mm, stroke=1, fill=0)
        else:
            lin = f - inicio + 1
            if 1 <= lin <= 5 and not (pest > 0 and f == pest):
                c.circle(cx, gy - (lin - 0.5) * esp_f, 1.5 * mm, stroke=0, fill=1)


def eh_linha_de_acordes(s):
    t = s.split()
    return bool(t) and all(CHORD_RE.match(x) or x in ('|', '-', '/') for x in t) and any(CHORD_RE.match(x) for x in t)


# ---------------------------------------------------------- páginas
def desenhar_cabecalho(c, logo, primeira, meta):
    W, H = A4
    ml, mt = 18 * mm, 16 * mm
    y = H - mt
    if not primeira:
        return y
    hl = 20 * mm
    xt = ml
    if logo:
        iw, ih = logo.getSize()
        wl = hl * iw / ih
        if wl > 55 * mm:
            wl = 55 * mm
            hl = wl * ih / iw
        c.drawImage(logo, ml, y - hl, width=wl, height=hl, mask='auto')
        xt = ml + wl + 6 * mm
    c.setFillColorRGB(0.1, 0.12, 0.18)
    c.setFont('Helvetica-Bold', 20)
    c.drawString(xt, y - 8 * mm, meta.titulo)
    sub = meta.artista
    if meta.album:
        sub = (meta.artista + '  |  ' if meta.artista else '') + 'Álbum: ' + meta.album
    c.setFillColorRGB(*CINZA)
    c.setFont('Helvetica', 11)
    c.drawString(xt, y - 14 * mm, sub)
    c.setStrokeColorRGB(0.8, 0.83, 0.88)
    c.setLineWidth(0.6)
    c.line(ml, y - hl - 3 * mm, W - ml, y - hl - 3 * mm)
    return y - hl - 10 * mm


def desenhar_rodape(c, logo, n, meta):
    W, H = A4
    ml = 18 * mm
    c.setFont('Helvetica', 8)
    c.setFillColorRGB(*CINZA)
    c.drawString(ml, 9 * mm, meta.titulo + ('  |  ' + meta.artista if meta.artista else ''))
    c.drawRightString(W - ml, 9 * mm, str(n))
    if logo:
        iw, ih = logo.getSize()
        hh = 6 * mm
        ww = hh * iw / ih
        c.drawImage(logo, W / 2 - ww / 2, 6 * mm, width=ww, height=hh, mask='auto')


def pagina_de_acordes(c, logo, linhas, pagina, meta):
    W, H = A4
    ml, mb = 18 * mm, 18 * mm
    usados = []
    for l in linhas:
        if eh_linha_de_acordes(l):
            for t in l.split():
                if CHORD_RE.match(t) and t not in usados:
                    usados.append(t)
    formas = []
    for t in usados:
        m = CHORD_RE.match(t)
        suf = m.group(2) or ''
        baixo = m.group(3)[1:] if m.group(3) else None
        if suf in SUFIXOS:
            formas.append((t, NOTAS[m.group(1)], suf, baixo))
    if not formas:
        return pagina
    desenhar_rodape(c, logo, pagina, meta)
    c.showPage()
    pagina += 1
    y = desenhar_cabecalho(c, logo, False, meta)
    c.setFillColorRGB(*VERDE)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(ml, y - 6 * mm, 'Acordes usados (violão)')
    y -= 16 * mm
    w, h = 30 * mm, 44 * mm
    por_linha = int((W - 2 * ml) // w)
    for k, (nome, raiz, suf, baixo) in enumerate(formas):
        col, lin = k % por_linha, k // por_linha
        desenhar_acorde(c, ml + col * w, y - lin * h, nome, raiz, suf)
        if baixo:
            c.setFont('Helvetica', 7)
            c.setFillColorRGB(*CINZA)
            c.drawCentredString(ml + col * w + 12 * mm, y - lin * h - 32 * mm, 'baixo em ' + baixo)
    c.setFont('Helvetica', 8)
    c.setFillColorRGB(*CINZA)
    c.drawString(ml, mb + 2 * mm, 'Formas de violão. x = corda não tocada, o = corda solta, barra preta = pestana.')
    return pagina


def gerar_pdf(texto, meta, logo_path=None, caminho_saida='cifra.pdf'):
    W, H = A4
    ml, mb = 18 * mm, 18 * mm
    c = canvas.Canvas(caminho_saida, pagesize=A4)
    c.setTitle(meta.titulo)
    c.setAuthor(meta.artista)
    linhas = texto.split('\n')
    maior = max((len(l) for l in linhas), default=40)
    tam = max(7.5, min(11, (W - 2 * ml) / (0.6 * maior)))
    lh = tam * 1.38
    logo = ImageReader(logo_path) if logo_path and os.path.exists(logo_path) else None
    pagina = 1
    y = desenhar_cabecalho(c, logo, True, meta)
    for l in linhas:
        if y < mb + 2 * lh:
            desenhar_rodape(c, logo, pagina, meta)
            c.showPage()
            pagina += 1
            y = desenhar_cabecalho(c, logo, False, meta)
        s = l.rstrip()
        if not s:
            y -= lh * 0.6
            continue
        if re.fullmatch(r'\[[^\]]+\]', s.strip()):
            y -= lh * 0.4
            c.setFillColorRGB(*VERDE)
            c.setFont('Helvetica-Bold', tam + 1)
            c.drawString(ml, y - tam, s.strip('[]'))
            y -= lh * 1.1
            continue
        if s.startswith('Tom:'):
            c.setFillColorRGB(*AZUL)
            c.setFont('Courier-Bold', tam + 1)
            c.drawString(ml, y - tam, s)
            y -= lh * 1.1
            continue
        if eh_linha_de_acordes(s):
            c.setFillColorRGB(*AZUL)
            c.setFont('Courier-Bold', tam)
        else:
            c.setFillColorRGB(0.1, 0.12, 0.18)
            c.setFont('Courier', tam)
        c.drawString(ml, y - tam, s)
        y -= lh
    pagina = pagina_de_acordes(c, logo, linhas, pagina, meta)
    desenhar_rodape(c, logo, pagina, meta)
    c.save()
    return caminho_saida
