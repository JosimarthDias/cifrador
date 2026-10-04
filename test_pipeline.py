"""Testes sem Whisper: usam um áudio sintético (C G Am F, depois D A Bm G) e uma transcrição falsa."""
import os
import sys

import numpy as np
import pytest
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import gerar_cifra, montar_pdf, nome_do_arquivo  # noqa: E402

SR = 22050


def _nota(m):
    return 440 * 2 ** ((m - 69) / 12)


@pytest.fixture(scope='module')
def audio(tmp_path_factory):
    prog1 = [[0, 4, 7], [7, 11, 2], [9, 0, 4], [5, 9, 0]]
    prog2 = [[(p + 2) % 12 for p in c] for c in prog1]
    dur = 64
    t = np.arange(SR * dur) / SR
    y = np.zeros_like(t)
    for k in range(dur // 2):
        m = (t >= k * 2) & (t < (k + 1) * 2)
        prog = prog1 if k * 2 < 32 else prog2
        for pc in prog[k % 4]:
            for oitava in (48, 60, 72):
                for h in (1, 2, 3):
                    y[m] += np.sin(2 * np.pi * _nota(oitava + pc) * h * t[m]) / h
    y = y * 0.05 + np.random.RandomState(0).randn(len(y)) * 0.01
    caminho = tmp_path_factory.mktemp('audio') / 'sintetico.wav'
    sf.write(str(caminho), y, SR)
    return str(caminho)


LETRA = "[Verso 1]\n" + "\n".join(f"palavra{i} beleza do canto agora" for i in range(8)) + \
        "\n\n[Refrão]\n" + "\n".join(f"palavra{i} beleza do canto agora" for i in range(8, 16))


def transcricao_falsa(_caminho):
    """Transcrição com erros de grafia ('belesa'), um verso a cada 4 segundos."""
    return [[(' ' + w, 0.5 + i * 4 + j * 0.7, 0.5 + i * 4 + j * 0.7 + 0.5)
             for j, w in enumerate(f'palavra{i} belesa do canto agora'.split())] for i in range(16)]


def test_cifra_completa(audio, tmp_path):
    r = gerar_cifra(audio, 'Casa Favorita', 'A Mensagem', 'Álbum X', LETRA, nivel=2,
                    transcrever_fn=transcricao_falsa)
    assert os.path.exists(r['pdf']) and r['pdf'].endswith('cifra_Casa_Favorita.pdf')
    assert 'beleza' in r['cifra'] and 'belesa' not in r['cifra']        # letra corrigida
    assert 'Modulação para D' in r['cifra']                              # modulação detectada
    for acorde in ('C ', 'G', 'Am', 'F', 'D', 'A', 'Bm'):
        assert acorde in r['cifra']
    assert 'Letra corrigida: 16 de 16' in r['aviso']
    assert '0:00 -> C' in r['tons']


def test_sem_letra_usa_transcricao(audio):
    r = gerar_cifra(audio, 'Sem Letra', '', '', '', transcrever_fn=transcricao_falsa)
    assert 'belesa' in r['cifra']
    assert os.path.exists(r['pdf'])


def test_pdf_a_partir_de_texto_editado(tmp_path):
    pdf = montar_pdf('Tom: C\n\n[Verso 1]\nC      G\nTeste de cifra', 'Teste', 'Artista', 'Álbum',
                     pasta=str(tmp_path))
    assert os.path.getsize(pdf) > 1000


def test_nome_do_arquivo():
    assert nome_do_arquivo('Canção da manhã!') == 'cifra_Cancao_da_manha.pdf'
    assert nome_do_arquivo('???') == 'cifra_musica.pdf'
