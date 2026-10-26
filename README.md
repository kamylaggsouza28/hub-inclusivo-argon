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
