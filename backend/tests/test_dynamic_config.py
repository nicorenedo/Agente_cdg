# backend/tests/test_dynamic_config.py
import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# 🔧 CORREGIDO: Agregar rutas correctas al path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

# Agregar también la ruta src para las importaciones internas
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# 🔧 CORREGIDO: Importación con ruta corregida
from utils.dynamic_config import (
    DynamicBusinessConfig, 
    ProductoInfo, 
    CentroInfo, 
    SegmentoInfo, 
    GestorInfo,
    get_productos_activos,
    get_centros_finalistas,
    get_centros_centrales
)


class TestDynamicBusinessConfig:
    """Tests para la clase DynamicBusinessConfig"""
    
    @pytest.fixture
    def config(self):
        """Fixture que proporciona una instancia limpia de DynamicBusinessConfig"""
        return DynamicBusinessConfig()
    
    @pytest.fixture
    def mock_productos_data(self):
        """Datos mock para productos"""
        return [
            {"PRODUCTO_ID": "100100100100", "DESC_PRODUCTO": "Préstamo Hipotecario"},
            {"PRODUCTO_ID": "400200100100", "DESC_PRODUCTO": "Depósito Plazo Fijo"},
            {"PRODUCTO_ID": "600100300300", "DESC_PRODUCTO": "Fondo Banca March"}
        ]
    
    @pytest.fixture
    def mock_centros_data(self):
        """Datos mock para centros"""
        return [
            {"CENTRO_ID": 1, "DESC_CENTRO": "Madrid", "TIPO_CENTRO": "FINALISTA"},
            {"CENTRO_ID": 2, "DESC_CENTRO": "Palma", "TIPO_CENTRO": "FINALISTA"},
            {"CENTRO_ID": 6, "DESC_CENTRO": "RRHH", "TIPO_CENTRO": "CENTRAL"},
            {"CENTRO_ID": 7, "DESC_CENTRO": "Dir. Financiera", "TIPO_CENTRO": "CENTRAL"}
        ]
    
    def test_cache_mechanism(self, config):
        """Test del mecanismo de cache básico"""
        # Cache inicial vacío
        assert not config._is_cache_valid("test_key")
        
        # Establecer cache
        config._set_cache("test_key", "test_value")
        assert config._is_cache_valid("test_key")
        assert config._cache["test_key"] == "test_value"
        
        # Simular cache expirado
        config._cache_timestamp["test_key"] = datetime.now() - timedelta(seconds=400)
        assert not config._is_cache_valid("test_key")
    
    @patch('utils.dynamic_config.execute_query')
    def test_get_productos_activos(self, mock_execute, config, mock_productos_data):
        """Test obtención de productos activos"""
        mock_execute.return_value = mock_productos_data
        
        # Primera llamada - consulta BD
        productos = config.get_productos_activos()
        
        # Verificar estructura de datos
        assert len(productos) == 3
        assert isinstance(productos[0], ProductoInfo)
        assert productos[0].producto_id == "100100100100"
        assert productos[0].descripcion == "Préstamo Hipotecario"
        
        # Verificar que se llamó execute_query
        mock_execute.assert_called_once()
        
        # Segunda llamada - debe usar cache
        mock_execute.reset_mock()
        productos_cached = config.get_productos_activos()
        
        # No debe llamar a execute_query por cache
        mock_execute.assert_not_called()
        assert len(productos_cached) == 3
    
    @patch('utils.dynamic_config.execute_query')
    def test_get_centros_por_tipo(self, mock_execute, config, mock_centros_data):
        """Test obtención de centros por tipo"""
        mock_execute.return_value = mock_centros_data
        
        centros = config.get_centros_por_tipo()
        
        # Verificar estructura
        assert "FINALISTA" in centros
        assert "CENTRAL" in centros
        assert len(centros["FINALISTA"]) == 2
        assert len(centros["CENTRAL"]) == 2
        
        # Verificar tipos de datos
        assert isinstance(centros["FINALISTA"][0], CentroInfo)
        assert centros["FINALISTA"][0].centro_id == 1
        assert centros["FINALISTA"][0].tipo == "FINALISTA"
    
    @patch('utils.dynamic_config.execute_query')
    def test_get_gestores_por_centro_sin_filtro(self, mock_execute, config):
        """Test obtención de gestores sin filtro"""
        mock_gestores = [
            {"GESTOR_ID": "G001", "DESC_GESTOR": "Juan Pérez", "CENTRO": 1, "SEGMENTO_ID": "N10101"},
            {"GESTOR_ID": "G002", "DESC_GESTOR": "María García", "CENTRO": 2, "SEGMENTO_ID": "N10102"}
        ]
        mock_execute.return_value = mock_gestores
        
        gestores = config.get_gestores_por_centro()
        
        assert len(gestores) == 2
        assert isinstance(gestores[0], GestorInfo)
        assert gestores[0].gestor_id == "G001"
        assert gestores[0].centro_id == 1
        
        # Verificar que no se pasaron parámetros (sin filtro)
        args, kwargs = mock_execute.call_args
        assert len(args) == 2  # query y params
        assert args[1] is None  # params debe ser None
    
    @patch('utils.dynamic_config.execute_query')
    def test_get_gestores_por_centro_con_filtro(self, mock_execute, config):
        """Test obtención de gestores con filtro de centro"""
        mock_gestores = [
            {"GESTOR_ID": "G001", "DESC_GESTOR": "Juan Pérez", "CENTRO": 1, "SEGMENTO_ID": "N10101"}
        ]
        mock_execute.return_value = mock_gestores
        
        gestores = config.get_gestores_por_centro(centro_id=1)
        
        assert len(gestores) == 1
        
        # Verificar que se pasó el parámetro de filtro
        args, kwargs = mock_execute.call_args
        assert args[1] == (1,)  # params debe contener el centro_id
    
    @patch('utils.dynamic_config.execute_query')
    def test_get_configuracion_fondos(self, mock_execute, config):
        """Test obtención de configuración de fondos"""
        mock_cuentas = [
            {"CUENTA_ID": "760025", "FRECUENCIA": 100},
            {"CUENTA_ID": "760024", "FRECUENCIA": 80}
        ]
        mock_execute.return_value = mock_cuentas
        
        config_fondos = config.get_configuracion_fondos()
        
        # Verificar estructura básica
        assert "producto_fondos" in config_fondos
        assert "distribucion" in config_fondos
        assert "cuentas_reparto" in config_fondos
        
        # Verificar valores específicos
        assert config_fondos["distribucion"]["fabrica_pct"] == 85
        assert config_fondos["distribucion"]["banco_pct"] == 15
        assert config_fondos["cuentas_reparto"]["fabrica"] == "760025"
        assert config_fondos["cuentas_reparto"]["banco"] == "760024"
    
    @patch('utils.dynamic_config.execute_query')
    def test_error_handling(self, mock_execute, config):
        """Test manejo de errores en consultas"""
        mock_execute.side_effect = Exception("Error de conexión")
        
        with pytest.raises(RuntimeError, match="Error obteniendo productos"):
            config.get_productos_activos()
    
    def test_cache_invalidation(self, config):
        """Test invalidación de cache"""
        # Establecer algunos valores en cache
        config._set_cache("key1", "value1")
        config._set_cache("key2", "value2")
        
        assert config._is_cache_valid("key1")
        assert config._is_cache_valid("key2")
        
        # Invalidar cache específico
        config.invalidate_cache("key1")
        assert not config._is_cache_valid("key1")
        assert config._is_cache_valid("key2")
        
        # Invalidar todo el cache
        config.invalidate_cache()
        assert not config._is_cache_valid("key2")
    
    @patch('utils.dynamic_config.execute_query')
    def test_force_refresh(self, mock_execute, config, mock_productos_data):
        """Test del parámetro force_refresh"""
        mock_execute.return_value = mock_productos_data
        
        # Primera llamada - llena cache
        config.get_productos_activos()  # 🔧 CORREGIDO: eliminado typo "produtos"
        assert mock_execute.call_count == 1
        
        # Segunda llamada normal - usa cache
        config.get_productos_activos()
        assert mock_execute.call_count == 1  # No incrementa
        
        # Tercera llamada con force_refresh - ignora cache
        config.get_productos_activos(force_refresh=True)
        assert mock_execute.call_count == 2  # Incrementa


class TestConvenienceFunctions:
    """Tests para las funciones de conveniencia"""
    
    @patch('utils.dynamic_config.business_config')
    def test_get_productos_activos(self, mock_business_config):
        """Test función de conveniencia get_productos_activos"""
        mock_productos = [ProductoInfo("001", "Producto Test")]
        mock_business_config.get_productos_activos.return_value = mock_productos
        
        result = get_productos_activos()
        
        assert result == mock_productos
        mock_business_config.get_productos_activos.assert_called_once()
    
    @patch('utils.dynamic_config.business_config')
    def test_get_centros_finalistas(self, mock_business_config):
        """Test función de conveniencia get_centros_finalistas"""
        mock_centros = {
            "FINALISTA": [CentroInfo(1, "Madrid", "FINALISTA"), CentroInfo(2, "Palma", "FINALISTA")],
            "CENTRAL": [CentroInfo(6, "RRHH", "CENTRAL")]
        }
        mock_business_config.get_centros_por_tipo.return_value = mock_centros
        
        result = get_centros_finalistas()
        
        assert result == [1, 2]
        mock_business_config.get_centros_por_tipo.assert_called_once()
    
    @patch('utils.dynamic_config.business_config')
    def test_get_centros_centrales(self, mock_business_config):
        """Test función de conveniencia get_centros_centrales"""
        mock_centros = {
            "FINALISTA": [CentroInfo(1, "Madrid", "FINALISTA")],
            "CENTRAL": [CentroInfo(6, "RRHH", "CENTRAL"), CentroInfo(7, "Dir.Fin", "CENTRAL")]
        }
        mock_business_config.get_centros_por_tipo.return_value = mock_centros
        
        result = get_centros_centrales()
        
        assert result == [6, 7]
        mock_business_config.get_centros_por_tipo.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
