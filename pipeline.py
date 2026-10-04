"""Fluxo completo: áudio + letra -> cifra em texto e PDF."""
import os
import re
import tempfile
import unicodedata

from .cifra import make_sheet
from .harmonia import analyze_harmony
from .letra import items_from_segments, items_with_correct_lyrics
from .pdf import Meta, gerar_pdf

LOGO_PADRAO = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'logo.png')


def nome_do_arquivo(titulo):
    sem = unicodedata.normalize('NFD', titulo)
    sem = ''.join(ch for ch in sem if unicodedata.category(ch) != 'Mn')
    return 'cifra_' + (re.sub(r'[^A-Za-z0-9]+', '_', sem).strip('_') or 'musica') + '.pdf'


def achar_logo(logo_enviado=None):
    """Usa o logotipo enviado; se não houver, o que está em assets/logo.png (se existir)."""
    if logo_enviado and os.path.exists(logo_enviado):
        return logo_enviado
    return LOGO_PADRAO if os.path.exists(LOGO_PADRAO) else None


def texto_dos_tons(harmonia):
    linhas = []
    for k in harmonia['keys']:
        m, s = divmod(int(k['start']), 60)
        linhas.append(f"a partir de {m}:{s:02d} -> {k['name']}")
    return '\n'.join(linhas)


def montar_pdf(texto_cifra, titulo, artista, album, logo_enviado=None, pasta=None):
    """Cria só o PDF a partir de um texto de cifra (útil depois de editar o texto)."""
    pasta = pasta or tempfile.mkdtemp(prefix='cifra_')
    meta = Meta(titulo=(titulo or '').strip() or 'Sem título',
                artista=(artista or '').strip(), album=(album or '').strip())
    saida = os.path.join(pasta, nome_do_arquivo(meta.titulo))
    return gerar_pdf(texto_cifra, meta, achar_logo(logo_enviado), saida)


def gerar_cifra(caminho_audio, titulo, artista, album, letra, nivel=2, usar_baixo=False,
                logo_enviado=None, progresso=None, transcrever_fn=None):
    """Roda tudo. Devolve um dicionário com 'pdf', 'cifra', 'cifra_editor' e 'tons'.
    transcrever_fn existe para os testes poderem trocar o Whisper por uma versão falsa."""
    def avisar(frac, texto):
        if progresso:
            progresso(frac, texto)

    if transcrever_fn is None:
        from .transcricao import transcrever as transcrever_fn

    avisar(0.05, 'Analisando tom, modulações e acordes...')
    harmonia = analyze_harmony(caminho_audio, nivel=int(nivel), usar_baixo=bool(usar_baixo))

    avisar(0.45, 'Ouvindo a música para marcar o tempo (pode levar alguns minutos)...')
    trechos = transcrever_fn(caminho_audio)

    avisar(0.85, 'Montando a cifra...')
    if (letra or '').strip():
        itens, achou, total = items_with_correct_lyrics(trechos, letra)
        aviso = f'Letra corrigida: {achou} de {total} trechos encaixados na sua letra.'
    else:
        itens = items_from_segments(trechos)
        aviso = 'Sem letra colada: usei o texto transcrito do áudio (pode ter palavras erradas).'
    em_cima, para_editor = make_sheet(itens, harmonia)

    avisar(0.95, 'Criando o PDF...')
    pdf = montar_pdf(em_cima, titulo, artista, album, logo_enviado)
    avisar(1.0, 'Pronto.')
    return {'pdf': pdf, 'cifra': em_cima, 'cifra_editor': para_editor,
            'tons': texto_dos_tons(harmonia), 'aviso': aviso}
