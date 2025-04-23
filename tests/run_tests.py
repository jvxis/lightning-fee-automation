#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para executar todos os testes da aplicação
"""

import os
import sys
import unittest

# Adicionar diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar os testes
from tests.test_lnd_client import TestLNDClient
from tests.test_fee_manager import TestFeeManager
from tests.test_web_api import TestWebAPI
from tests.test_integration import TestIntegration

if __name__ == "__main__":
    # Criar suite de testes
    test_suite = unittest.TestSuite()
    
    # Adicionar testes à suite
    test_suite.addTest(unittest.makeSuite(TestLNDClient))
    test_suite.addTest(unittest.makeSuite(TestFeeManager))
    test_suite.addTest(unittest.makeSuite(TestWebAPI))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Verificar resultado
    if result.wasSuccessful():
        print("\nTodos os testes foram executados com sucesso!")
        sys.exit(0)
    else:
        print("\nAlguns testes falharam.")
        sys.exit(1)
