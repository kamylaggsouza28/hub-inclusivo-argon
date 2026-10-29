# Hub Inclusivo Argon

Aplicação Streamlit para mapas mentais, infográficos, roteiros educativos e apoio à leitura, com configurações de acessibilidade e IA opcional.

## Iniciar

1. Instale Python 3.10 ou superior.
2. No terminal, dentro desta pasta:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

3. Abra o endereço local mostrado no terminal (geralmente http://localhost:8501).

## IA opcional

No menu lateral, habilite IA, informe endpoint compatível com OpenAI, nome do modelo e chave. Também é possível configurar `ARGON_API_KEY`, `ARGON_BASE_URL` e `ARGON_MODEL` como variáveis de ambiente. A chave não é gravada pelo aplicativo. Nunca coloque chaves em repositórios públicos.

Sem IA, o app usa geradores locais simples e editáveis; não finge interpretar qualquer tema profundamente. A aba de vídeo gera **roteiros**, não arquivos de vídeo.

## Privacidade e segurança

Textos enviados ao modelo de IA vão para o provedor configurado. Evite inserir dados pessoais de crianças, informações médicas ou escolares identificáveis. Para ambientes institucionais, implemente autenticação, política de retenção e revisão humana do conteúdo antes da publicação.

## Recursos

- Perfil TDAH, TEA ou dislexia, fonte, espaçamento, contraste e movimento reduzido
- Mapas mentais em árvore visual e texto para download
- Infográficos em cartões e exportação HTML
- Roteiros com canais visual e auditivo, exportação CSV
- Ajuste do conteúdo gerado antes de exportar

## Atualização: tutor, mapas e exportações

As quatro áreas originais foram mantidas. A quinta aba, Tutor, corrige uma resposta com base no material de referência e apresenta acertos, melhorias, explicação e próxima pergunta. Requer IA habilitada; sem IA não há correção automática. O feedback deve ser revisado por um educador.

- Mapas com conexões, descrição textual equivalente e PNG com ramos.
- PDF e JSON de conteúdo editado; PNG para mapa, cartões, roteiro e feedback.
- Modo de foco com uma coluna, destaque de foco de teclado e ajustes de leitura existentes.
- Validação de estruturas e atualização do editor ao gerar outro material.
- PDF contém texto selecionável; não é PDF/UA certificado. PNG exige a alternativa textual disponível no aplicativo.
- PNG muito extenso é recusado com orientação para usar PDF/JSON.

## Implantar no Streamlit Community Cloud

1. Envie os arquivos desta atualização ao mesmo repositório, incluindo `argon_tools.py` e `requirements.txt`.
2. Em https://share.streamlit.io, entre com GitHub e escolha **Create app**.
3. Selecione `kamylaggsouza28/hub-inclusivo-argon`, a branch com a atualização e o arquivo principal `app.py`.
4. Em Advanced settings, selecione Python 3.12. Para IA, configure em Secrets:

```toml
ARGON_API_KEY = "sua-chave"
ARGON_BASE_URL = "https://api.openai.com/v1"
ARGON_MODEL = "modelo-disponivel-na-sua-conta"
```

5. Clique em Deploy. Se o app já estiver implantado na mesma branch, o envio de um commit dispara a atualização; consulte os logs se houver falha.
6. Gere um material em cada área, baixe as exportações e teste o tutor. Confira a leitura por teclado e as preferências com os estudantes.

O mapa na tela é desenhado pelo Streamlit. A exportação usa Pillow e ReportLab; não requer instalação do executável Graphviz. Uma chave configurada no servidor não aparece no campo de chave e só é usada com o endpoint configurado no servidor. Em um app público, chamadas com essa chave consomem sua cota; use autenticação e limites antes de disponibilizar amplamente.

Documentação oficial: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

## Testar

```bash
python -m unittest -v test_argon.py
```

Os testes usam Streamlit AppTest para geração local, atualização do editor, rejeição de JSON inválido, tutor com provedor simulado e falha de conexão. Verificam PNG decodificável e cabeçalho PDF. Chamadas reais de IA exigem credenciais e validação própria do conteúdo. Acessibilidade assistiva precisa de avaliação com leitores de tela; os ajustes não equivalem a certificação WCAG.
