import pytest
from cfdi_generator import CFDIGenerator
from datetime import datetime
import json

def test_cfdi_generator_test_mode():
    """Test CFDI generator in test mode"""
    generator = CFDIGenerator(test_mode=True)
    assert generator.test_mode == True

def test_prepare_emisor(app):
    """Test emisor data preparation"""
    generator = CFDIGenerator(test_mode=True)
    emisor = generator._prepare_emisor()
    assert 'Rfc' in emisor
    assert 'Nombre' in emisor
    assert 'RegimenFiscal' in emisor

def test_prepare_receptor(app):
    """Test receptor data preparation"""
    generator = CFDIGenerator(test_mode=True)
    
    # Test public receptor
    public_receptor = generator._prepare_receptor(is_public=True)
    assert public_receptor['Rfc'] == 'XAXX010101000'
    assert public_receptor['Nombre'] == 'PUBLICO EN GENERAL'
    
    # Test normal receptor
    normal_receptor = generator._prepare_receptor(is_public=False)
    assert 'Rfc' in normal_receptor
    assert 'Nombre' in normal_receptor

def test_generate_cfdi(app, test_db_session, test_sale):
    """Test CFDI generation"""
    with app.app_context():
        generator = CFDIGenerator(test_mode=True)
        result = generator.generate_cfdi(test_sale)
        test_db_session.refresh(test_sale)
        
        assert 'uuid' in result
        assert 'xml' in result
        assert result['uuid'].startswith('TEST-UUID-')
        
        # Verify XML content
        xml_data = json.loads(result['xml'])
        assert xml_data['Version'] == '4.0'
        assert 'Emisor' in xml_data
        assert 'Receptor' in xml_data
        assert 'Conceptos' in xml_data

def test_generate_global_cfdi(app, test_db_session, test_sale):
    """Test global CFDI generation"""
    with app.app_context():
        generator = CFDIGenerator(test_mode=True)
        date = datetime.now().date()
        result = generator.generate_global_cfdi([test_sale], date)
        test_db_session.refresh(test_sale)
        
        assert result['cfdi_uuid'].startswith('TEST-GLOBAL-')
        assert 'xml_content' in result
        
        # Verify XML content
        xml_data = json.loads(result['xml_content'])
        assert xml_data['Version'] == '4.0'
        assert xml_data['Serie'] == 'G'
        assert 'Emisor' in xml_data
        assert 'Receptor' in xml_data
        assert xml_data['Receptor']['Rfc'] == 'XAXX010101000'  # Public receptor
