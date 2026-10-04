"""Transcrição do áudio com Whisper (via stable-ts). Devolve o tempo de cada palavra cantada."""
import os

_modelo = None


def carregar_modelo():
    """Carrega o Whisper uma vez só. Na GPU usa 'medium'; na CPU usa 'small'.
    Dá para forçar outro com a variável de ambiente WHISPER_MODEL (tiny, base, small, medium)."""
    global _modelo
    if _modelo is None:
        import torch
        import stable_whisper
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        nome = os.environ.get('WHISPER_MODEL') or ('medium' if device == 'cuda' else 'small')
        _modelo = stable_whisper.load_model(nome, device=device)
    return _modelo


def transcrever(caminho_audio):
    """Devolve uma lista de trechos; cada trecho é uma lista de (palavra, inicio, fim)."""
    modelo = carregar_modelo()
    resultado = modelo.transcribe(caminho_audio, language='pt', condition_on_previous_text=False)
    return [[(w.word, w.start, w.end) for w in seg.words] for seg in resultado.segments]
