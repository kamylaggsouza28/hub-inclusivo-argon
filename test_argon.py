import json
import unittest
from io import BytesIO
from unittest.mock import patch, Mock
from PIL import Image
from streamlit.testing.v1 import AppTest
from argon_tools import validate, png_bytes, pdf_bytes, map_dot

class ArgonTests(unittest.TestCase):
    def test_exports_and_invalid_schema(self):
        data = {'titulo':'Água e ação', 'ramos':[{'titulo':'Evaporação', 'detalhes':['A água aquece.', 'Forma vapor.']}]}
        validate(data, 'mapa')
        Image.open(BytesIO(png_bytes(data))).verify()
        self.assertTrue(pdf_bytes(data).startswith(b'%PDF'))
        self.assertIn('root -> b0', map_dot(data))
        with self.assertRaises(ValueError):
            validate({'titulo':'x', 'ramos':[{'titulo':'x','detalhes':'inválido'}]}, 'mapa')

    def test_app_generation_and_editor_refresh(self):
        app = AppTest.from_file('app.py', default_timeout=30).run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.tabs), 5)
        for label in ['Construir mapa mental', 'Criar roteiro']:
            next(b for b in app.button if b.label == label).click().run()
            self.assertEqual(len(app.exception), 0)
        app.text_area(key='info_input').set_value('A água evapora. Depois condensa.')
        next(b for b in app.button if b.label == 'Criar infográfico').click().run()
        self.assertEqual(len(app.exception), 0)
        app.text_area(key='map_input').set_value('Novo assunto')
        next(b for b in app.button if b.label == 'Construir mapa mental').click().run()
        self.assertIn('Novo assunto', app.text_area(key='map_edit').value)
        app.text_area(key='map_edit').set_value('{"titulo":"x","ramos":[1]}').run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(len(app.warning))

    def test_tutor_feedback_and_network_failure(self):
        app = AppTest.from_file('app.py', default_timeout=30).run()
        next(t for t in app.toggle if t.label == 'Usar IA').set_value(True).run()
        for label, value in [('Material de referência','A água evapora ao aquecer.'), ('Sua resposta','A água vira vapor.')]:
            next(t for t in app.text_area if t.label == label).set_value(value)
        next(t for t in app.text_input if t.label == 'Pergunta').set_value('O que ocorre ao aquecer?')
        feedback = dict(titulo='Correção', acertos='Reconheceu o vapor.', melhorias='Explique o calor.', explicacao='O calor favorece a evaporação.', proxima_pergunta='Qual é o processo inverso?')
        response = Mock()
        response.json.return_value = {'choices':[{'message':{'content':json.dumps(feedback)}}]}
        with patch('requests.post', return_value=response):
            next(b for b in app.button if b.label == 'Corrigir resposta').click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state['tutor_feedback'], feedback)
        with patch('requests.post', side_effect=TimeoutError):
            next(b for b in app.button if b.label == 'Corrigir resposta').click().run()
        self.assertTrue(len(app.error))
        self.assertNotIn('tutor_feedback', app.session_state)

if __name__ == '__main__':
    unittest.main()
