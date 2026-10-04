---
title: Cifrador
emoji: 🎸
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.29.1
python_version: "3.11"
app_file: app.py
pinned: false
---

# Cifrador

Envie o áudio de uma música, cole a letra e baixe a **cifra em PDF**, com o tom, as modulações e os
acordes encaixados em cima da letra, o logotipo, o artista, o álbum e os desenhos dos acordes de violão.

## Como funciona

1. **Harmonia** (`cifrador/harmonia.py`): detecta o tom por trecho (e as modulações) e os acordes
   (maiores, menores, com sétima e, no nível 3, sus, nonas, diminutos).
2. **Transcrição** (`cifrador/transcricao.py`): o Whisper ouve a música e marca o tempo de cada palavra.
3. **Letra** (`cifrador/letra.py`): troca o texto transcrito (que erra palavras) pela letra certa que você colou,
   verso por verso, respeitando repetições do refrão.
4. **Cifra** (`cifrador/cifra.py`): coloca cada acorde na palavra onde ele troca.
5. **PDF** (`cifrador/pdf.py`): gera o PDF com logotipo e diagramas de acordes.

## Rodar no computador

```
pip install -r requirements.txt gradio
python app.py
```

## Testes

```
pip install pytest
python -m pytest -q
```

Os testes usam um áudio sintético e uma transcrição falsa, então não precisam baixar o Whisper.

## Logotipo padrão

Coloque o arquivo do logotipo em `assets/logo.png`. Ele é usado quando nenhum logotipo é enviado na tela.

## Publicar no Hugging Face Spaces

1. Crie um Space em huggingface.co/new-space (SDK **Gradio**, visibilidade **Private** se quiser só para você).
2. Crie um token de acesso com permissão de escrita em huggingface.co/settings/tokens.
3. No GitHub, em **Settings > Secrets and variables > Actions**:
   - em **Secrets**, crie `HF_TOKEN` com o token;
   - em **Variables**, crie `HF_USER` (seu usuário do Hugging Face) e `HF_SPACE` (nome do Space).
4. A cada mesclagem na branch `main`, o GitHub Actions envia o projeto para o Space.

## Limites conhecidos

- No Space gratuito não há placa de vídeo: usa o Whisper `small` e cada música leva alguns minutos.
  Na GPU, o app usa o `medium`. Dá para forçar outro com a variável `WHISPER_MODEL`.
- Os arquivos do Space gratuito não são permanentes: o logotipo padrão deve ficar em `assets/logo.png` no repositório.
- Acordes são sugestões automáticas: confira de ouvido.
