import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
import os
from flask import Flask

# Importa tu aplicación Flask y el método que deseas probar
from app import app


class TestDownloadAllFormats(unittest.TestCase):

    def setUp(self):
        # Configura una instancia de la aplicación para pruebas
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.modules.dataset.routes.generate_uvl_file')
    @patch('app.modules.dataset.routes.generate_glencoe_file')
    @patch('app.modules.dataset.routes.generate_cnf_file')
    @patch('app.modules.dataset.routes.generate_splot_file')
    @patch('app.modules.dataset.routes.send_file')
    def test_download_all_formats_success(
        self,
        mock_send_file,
        mock_generate_splot,
        mock_generate_cnf,
        mock_generate_glencoe,
        mock_generate_uvl
    ):
        # Mockear las rutas de los archivos generados
        mock_generate_uvl.return_value = '/tmp/file.uvl'
        mock_generate_glencoe.return_value = '/tmp/file_glencoe.json'
        mock_generate_cnf.return_value = '/tmp/file.cnf'
        mock_generate_splot.return_value = '/tmp/file.splx'

        # Mockear el comportamiento de send_file
        mock_send_file.return_value = MagicMock()

        # Simular la existencia de los archivos
        for path in [
            mock_generate_uvl.return_value,
            mock_generate_glencoe.return_value,
            mock_generate_cnf.return_value,
            mock_generate_splot.return_value
        ]:
            with open(path, 'w') as f:
                f.write('mock content')

        # Hacer la solicitud a la ruta
        response = self.app.get('/download_all/123')

        # Validar que la respuesta sea exitosa
        self.assertEqual(response.status_code, 200)
        mock_send_file.assert_called_once()

        # Verificar que los métodos de generación se llamaron con el ID correcto
        mock_generate_uvl.assert_called_once_with(123)
        mock_generate_glencoe.assert_called_once_with(123)
        mock_generate_cnf.assert_called_once_with(123)
        mock_generate_splot.assert_called_once_with(123)

        # Limpiar los archivos temporales
        for path in [
            mock_generate_uvl.return_value,
            mock_generate_glencoe.return_value,
            mock_generate_cnf.return_value,
            mock_generate_splot.return_value
        ]:
            if os.path.exists(path):
                os.remove(path)

    @patch('app.modules.dataset.routes.generate_uvl_file')
    @patch('app.modules.dataset.routes.generate_glencoe_file')
    @patch('app.modules.dataset.routes.generate_cnf_file')
    @patch('app.modules.dataset.routes.generate_splot_file')
    def test_download_all_formats_file_generation_failure(
        self,
        mock_generate_splot,
        mock_generate_cnf,
        mock_generate_glencoe,
        mock_generate_uvl
    ):
        # Simular que una de las funciones de generación lanza un error
        mock_generate_uvl.side_effect = RuntimeError("UVL generation failed")
        mock_generate_glencoe.return_value = '/tmp/file_glencoe.json'
        mock_generate_cnf.return_value = '/tmp/file.cnf'
        mock_generate_splot.return_value = '/tmp/file.splx'

        # Hacer la solicitud a la ruta
        response = self.app.get('/download_all/123')

        # Validar que la respuesta indique un error
        self.assertEqual(response.status_code, 500)
        self.assertIn(b'"error": "UVL generation failed"', response.data)

        # Verificar que las funciones se llamaron
        mock_generate_uvl.assert_called_once_with(123)
        mock_generate_glencoe.assert_not_called()
        mock_generate_cnf.assert_not_called()
        mock_generate_splot.assert_not_called()


if __name__ == '__main__':
    unittest.main()
