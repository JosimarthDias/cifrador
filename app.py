"""Tela web do cifrador (Gradio). Roda localmente com `python app.py` e no Hugging Face Spaces."""
import os

import gradio as gr

from cifrador.pipeline import gerar_cifra, montar_pdf

NIVEIS = {
    '1 - só maiores e menores (mais limpo)': 1,
    '2 - com sétimas e maj7 (recomendado)': 2,
    '3 - com sus, nonas e diminutos (mais completo, erra mais)': 3,
}


def acao_gerar(audio, titulo, artista, album, letra, nivel, baixo, logo, progress=gr.Progress()):
    if not audio:
        raise gr.Error('Escolha o arquivo de áudio da música.')
    if not (titulo or '').strip():
        raise gr.Error('Escreva o nome da música.')
    r = gerar_cifra(audio, titulo, artista, album, letra, nivel=NIVEIS[nivel], usar_baixo=baixo,
                    logo_enviado=logo, progresso=lambda f, t: progress(f, desc=t))
    return r['pdf'], r['cifra'], r['tons'], r['aviso']


def acao_so_pdf(texto, titulo, artista, album, logo):
    if not (texto or '').strip():
        raise gr.Error('Não há texto de cifra para gerar o PDF.')
    return montar_pdf(texto, titulo, artista, album, logo)


with gr.Blocks(title='Cifrador') as demo:
    gr.Markdown('# Cifrador\nEnvie o áudio, cole a letra e baixe a cifra em PDF, com tom, modulações e acordes.')
    with gr.Row():
        with gr.Column():
            titulo = gr.Textbox(label='Música')
            artista = gr.Textbox(label='Artista', value='A Mensagem')
            album = gr.Textbox(label='Álbum (pode deixar vazio)')
            letra = gr.Textbox(label='Letra (um verso por linha; use [Refrão] ou [Verso 1] para as partes)', lines=14)
        with gr.Column():
            audio = gr.Audio(label='Áudio da música', type='filepath', sources=['upload'])
            logo = gr.File(label='Logotipo (opcional; se vazio, usa o logotipo padrão do projeto)',
                           file_types=['image'], type='filepath')
            nivel = gr.Dropdown(list(NIVEIS), value=list(NIVEIS)[1], label='Detalhe dos acordes')
            baixo = gr.Checkbox(label='Mostrar acordes com baixo invertido (ex.: C/E)', value=False)
            botao = gr.Button('Gerar cifra', variant='primary')
    aviso = gr.Textbox(label='Aviso', interactive=False)
    tons = gr.Textbox(label='Tons e modulações', interactive=False, lines=3)
    cifra = gr.Textbox(label='Cifra (você pode editar o texto e gerar o PDF de novo)', lines=18, interactive=True)
    pdf = gr.File(label='PDF da cifra')
    botao2 = gr.Button('Gerar PDF do texto acima')

    botao.click(acao_gerar, [audio, titulo, artista, album, letra, nivel, baixo, logo], [pdf, cifra, tons, aviso])
    botao2.click(acao_so_pdf, [cifra, titulo, artista, album, logo], pdf)

demo.queue(default_concurrency_limit=1)

if __name__ == '__main__':
    # No Colab: APP_SHARE=1 cria um link público temporário; APP_USUARIO e APP_SENHA protegem o acesso.
    usuario = os.environ.get('APP_USUARIO')
    senha = os.environ.get('APP_SENHA')
    demo.launch(share=os.environ.get('APP_SHARE') == '1',
                auth=(usuario, senha) if usuario and senha else None)
