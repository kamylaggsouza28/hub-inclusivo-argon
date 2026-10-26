import os
import re
import json
import html
from io import StringIO

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Hub Inclusivo Argon", page_icon="🧩", layout="wide")

PROFILES = {
    "TDAH": "Frases curtas, etapas numeradas, um conceito por bloco, exemplos e resumo.",
    "TEA": "Linguagem literal, sequência previsível, exemplos concretos e sem metáforas ambíguas.",
    "Dislexia": "Frases claras, palavras comuns, parágrafos curtos e definições diretas.",
}


def parse_json(text):
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    return json.loads(clean)


def generate_ai(kind, subject, extra, config):
    instructions = {
        "mapa": 'Responda APENAS JSON: {"titulo":"...","ramos":[{"titulo":"...","detalhes":["...","..."]}]} com 4 a 6 ramos.',
        "infografico": 'Responda APENAS JSON: {"titulo":"...","cartoes":[{"titulo":"...","texto":"...","exemplo":"..."}]} com 4 a 8 cartões.',
        "video": 'Responda APENAS JSON: {"titulo":"...","cenas":[{"tempo":"0:00–0:15","visual":"...","audio":"..."}]} com 4 a 6 cenas.',
    }
    prompt = (f"Crie conteúdo educacional em português do Brasil. Perfil: {config['perfil']}. "
              f"Acessibilidade: {PROFILES[config['perfil']]}. "
              "Não invente fatos; sinalize incertezas. Não forneça diagnósticos. "
              f"Assunto: {subject[:10000]}. Orientações adicionais: {extra[:2000]}. " + instructions[kind])
    url = config['url'].rstrip('/') + '/chat/completions'
    if not url.startswith('https://') and not url.startswith('http://localhost') and not url.startswith('http://127.0.0.1'):
        raise ValueError('Use HTTPS para provedores remotos ou localhost para testes locais.')
    headers = {"Content-Type": "application/json"}
    if config['key']:
        headers['Authorization'] = f"Bearer {config['key']}"
    resp = requests.post(url, headers=headers, json={
        "model": config['model'], "temperature": 0.35,
        "messages": [{"role": "user", "content": prompt}]
    }, timeout=65)
    resp.raise_for_status()
    data = parse_json(resp.json()['choices'][0]['message']['content'])
    expected = {"mapa": "ramos", "infografico": "cartoes", "video": "cenas"}[kind]
    if not isinstance(data, dict) or not isinstance(data.get(expected), list):
        raise ValueError('O provedor não retornou o formato esperado. Tente novamente.')
    return data


def local_generate(kind, subject):
    title = subject.strip() or 'Tema de estudo'
    if kind == 'mapa':
        return {'titulo': title, 'ramos': [
            {'titulo': 'O que é?', 'detalhes': [f'Defina {title} com suas palavras.', 'Liste as palavras-chave.']},
            {'titulo': 'Como funciona?', 'detalhes': ['Descreva as etapas em ordem.', 'Identifique causas e consequências.']},
            {'titulo': 'Exemplo', 'detalhes': ['Escreva um exemplo do cotidiano.', 'Associe o exemplo ao conceito.']},
            {'titulo': 'Revisão', 'detalhes': ['Crie uma pergunta sobre o tema.', 'Resuma em uma frase.']},
        ]}
    if kind == 'infografico':
        chunks = [x.strip() for x in re.split(r'(?<=[.!?])\s+|\n+', title) if x.strip()]
        if len(chunks) < 2:
            chunks = [f'Conceito principal: {title}', 'Quais são as características?', 'Como aplicar na prática?', 'O que revisar?']
        return {'titulo': 'Resumo visual', 'cartoes': [
            {'titulo': f'Bloco {i+1}', 'texto': part, 'exemplo': 'Adicione aqui um exemplo concreto.'}
            for i, part in enumerate(chunks[:12])]}
    return {'titulo': title, 'cenas': [
        {'tempo': '0:00–0:15', 'visual': f'Exibir o título: {title}', 'audio': f'Hoje vamos aprender sobre {title}.'},
        {'tempo': '0:15–0:30', 'visual': 'Mostrar a primeira etapa com imagem simples.', 'audio': 'Primeiro, observe o que acontece.'},
        {'tempo': '0:30–0:45', 'visual': 'Mostrar um exemplo concreto.', 'audio': 'Agora veja um exemplo no dia a dia.'},
        {'tempo': '0:45–1:00', 'visual': 'Exibir uma pergunta de revisão.', 'audio': 'O que você aprendeu? Vamos revisar.'},
    ]}


def render_tree(data):
    st.subheader(data.get('titulo', 'Mapa mental'))
    for i, branch in enumerate(data.get('ramos', []), 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {branch.get('titulo', 'Tópico')}**")
            for detail in branch.get('detalhes', []):
                st.write('• ' + str(detail))


def render_cards(data):
    st.subheader(data.get('titulo', 'Infográfico'))
    cards = data.get('cartoes', [])
    for start in range(0, len(cards), 2):
        cols = st.columns(2)
        for j, item in enumerate(cards[start:start + 2]):
            with cols[j].container(border=True):
                st.markdown(f"### {html.escape(str(item.get('titulo', 'Conceito')))}")
                st.write(item.get('texto', ''))
                if item.get('exemplo'):
                    st.caption('Exemplo: ' + str(item['exemplo']))


def cards_html(data):
    blocks = ''.join('<section><h2>' + html.escape(str(c.get('titulo', ''))) + '</h2><p>' +
                     html.escape(str(c.get('texto', ''))) + '</p><p><b>Exemplo:</b> ' +
                     html.escape(str(c.get('exemplo', ''))) + '</p></section>' for c in data.get('cartoes', []))
    return ('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Infográfico</title>'
            '<style>body{font:20px Arial;max-width:900px;margin:30px auto;line-height:1.7}'
            'section{padding:20px;margin:15px;border:2px solid #246e56;border-radius:15px}'
            'h2{color:#b45309}</style><h1>' + html.escape(str(data.get('titulo', 'Infográfico'))) +
            '</h1>' + blocks + '</html>')

with st.sidebar:
    st.header('🎯 Preferências de leitura')
    perfil = st.radio('Perfil', list(PROFILES), index=0)
    fonte = st.slider('Tamanho da fonte', 16, 28, 19)
    espacamento = st.slider('Espaçamento entre linhas', 1.3, 2.2, 1.7, step=0.1)
    contraste = st.toggle('Alto contraste', value=False)
    reduzir = st.toggle('Reduzir movimentos', value=True)
    st.divider()
    st.header('🤖 Inteligência artificial (opcional)')
    usar_ia = st.toggle('Usar IA', value=False)
    url = st.text_input('Endpoint compatível com OpenAI', value=os.getenv('ARGON_BASE_URL', 'https://api.openai.com/v1'))
    modelo = st.text_input('Nome do modelo', value=os.getenv('ARGON_MODEL', 'gpt-4o-mini'))
    chave = st.text_input('Chave de API', type='password', value=os.getenv('ARGON_API_KEY', ''))
    st.caption('Com IA, o conteúdo é enviado ao provedor escolhido. Sem IA, são usados modelos locais de estruturação.')

bg = '#ffffff' if contraste else '#f7f9fc'
fg = '#111111' if contraste else '#183044'
st.markdown(f'''<style>
.stApp {{background:{bg};color:{fg};}}
.stApp p,.stApp li,.stApp label,.stApp input,.stApp textarea {{font-size:{fonte}px!important;line-height:{espacamento}!important;}}
.stApp h1,.stApp h2,.stApp h3 {{line-height:1.3!important;letter-spacing:.02em;}}
.stApp h1,.stApp h2 {{color:{'#703600' if contraste else '#ae5600'}!important;}}
.stApp h3 {{color:{'#14503d' if contraste else '#267355'}!important;}}
[data-testid="stVerticalBlockBorderWrapper"] {{border-radius:16px;}}
{'*, *::before, *::after {animation:none!important;transition:none!important;scroll-behavior:auto!important;}' if reduzir else ''}
</style>''', unsafe_allow_html=True)

st.title('🧩 Hub Inclusivo Argon')
st.write('Mapas mentais, infográficos e roteiros educativos com opções de acessibilidade.')
st.info('Ferramenta de apoio pedagógico. Revise conteúdos gerados por IA antes de utilizar em aulas ou intervenções.')
config = {'perfil': perfil, 'url': url, 'model': modelo, 'key': chave}

tab1, tab2, tab3, tab4 = st.tabs(['🌿 Mapa mental', '📊 Infográfico', '🎬 Roteiro de vídeo', '📖 Guia'])

with tab1:
    assunto = st.text_area('Assunto do mapa', 'O ciclo da água', key='map_input')
    detalhes = st.text_input('Orientações (opcional)', key='map_extra')
    if st.button('Construir mapa mental', type='primary'):
        try:
            st.session_state['map_result'] = generate_ai('mapa', assunto, detalhes, config) if usar_ia else local_generate('mapa', assunto)
        except Exception as exc:
            st.error(f'Não foi possível gerar com IA: {exc}')
    if 'map_result' in st.session_state:
        raw = st.text_area('Editar JSON do mapa (opcional)', json.dumps(st.session_state['map_result'], ensure_ascii=False, indent=2), height=180, key='map_edit')
        try:
            data = parse_json(raw)
            render_tree(data)
            st.download_button('Baixar mapa (JSON)', json.dumps(data, ensure_ascii=False, indent=2), 'mapa_argon.json', 'application/json')
        except Exception:
            st.warning('JSON inválido. Corrija para visualizar.')

with tab2:
    texto = st.text_area('Cole o texto para transformar em cartões', height=170, key='info_input')
    if st.button('Criar infográfico', type='primary'):
        if not texto.strip():
            st.warning('Digite ou cole um texto primeiro.')
        else:
            try:
                st.session_state['info_result'] = generate_ai('infografico', texto, '', config) if usar_ia else local_generate('infografico', texto)
            except Exception as exc:
                st.error(f'Não foi possível gerar com IA: {exc}')
    if 'info_result' in st.session_state:
        raw = st.text_area('Editar JSON dos cartões', json.dumps(st.session_state['info_result'], ensure_ascii=False, indent=2), height=180, key='info_edit')
        try:
            data = parse_json(raw)
            render_cards(data)
            st.download_button('Baixar infográfico (HTML)', cards_html(data), 'infografico_argon.html', 'text/html')
        except Exception:
            st.warning('JSON inválido. Corrija para visualizar.')

with tab3:
    objetivo = st.text_input('Objetivo do vídeo', 'Aprender a esperar a vez na escola')
    orientacoes = st.text_input('Faixa etária, contexto ou observações', key='video_extra')
    if st.button('Criar roteiro', type='primary'):
        try:
            st.session_state['video_result'] = generate_ai('video', objetivo, orientacoes, config) if usar_ia else local_generate('video', objetivo)
        except Exception as exc:
            st.error(f'Não foi possível gerar com IA: {exc}')
    if 'video_result' in st.session_state:
        raw = st.text_area('Editar JSON do roteiro', json.dumps(st.session_state['video_result'], ensure_ascii=False, indent=2), height=180, key='video_edit')
        try:
            data = parse_json(raw)
            st.subheader(data.get('titulo', 'Roteiro'))
            df = pd.DataFrame(data.get('cenas', [])).rename(columns={'tempo':'Tempo', 'visual':'Visual', 'audio':'Áudio'})
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button('Baixar roteiro (CSV)', df.to_csv(index=False).encode('utf-8-sig'), 'roteiro_argon.csv', 'text/csv')
        except Exception:
            st.warning('JSON inválido. Corrija para visualizar.')

with tab4:
    st.markdown('''### Como usar
1. Selecione o perfil e ajuste a leitura no menu lateral.
2. Escolha uma aba e informe um tema ou texto.
3. Gere o material. Com IA desligada, os resultados são modelos estruturais simples.
4. Revise o conteúdo e exporte o resultado.

### Atenção
- Acessibilidade é individual: experimente as configurações e respeite as preferências do estudante.
- Não compartilhe dados pessoais sensíveis com provedores de IA.
- O gerador de vídeo produz **roteiro**, não um vídeo renderizado.
- Materiais educativos não substituem profissionais de saúde ou educação.''')



# Acessibilidade visual - Hub Inclusivo Argon
st.markdown("""
<style>
/* Textos principais */
.stApp, .stApp p, .stApp label, .stApp li {
    color: #17212B;
}

/* Campos de texto */
.stTextInput input,
.stTextArea textarea {
    background-color: #FFFFFF !important;
    color: #17212B !important;
    -webkit-text-fill-color: #17212B !important;
}

/* Textos dentro dos campos */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #526170 !important;
    opacity: 1;
}

/* Títulos */
.stApp h1, .stApp h2, .stApp h3 {
    color: #B34700;
}

/* Botões */
.stButton button {
    background-color: #B34700;
    color: #FFFFFF;
    border: 1px solid #B34700;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)
