"""
core.utils
----------
Módulo de utilitários transversais e funções auxiliares do sistema.

Este módulo centraliza algoritmos independentes, ferramentas de validação
matemática e rotinas de higienização de dados que suportam toda a infraestrutura
do web scraper. Ao isolar estas funções estáticas (como a validação rigorosa 
de códigos EAN-13), garantimos que os controladores da API e os serviços 
de negócio permaneçam limpos, coesos e focados apenas na orquestração.

As funções aqui definidas são desenhadas para serem puras (sem efeitos colaterais)
e altamente testáveis, não possuindo dependências diretas com o estado da 
base de dados (SQLAlchemy) ou com chamadas de rede (httpx).
"""

def validar_ean13(ean: str) -> bool:
    """
    Valida a integridade de um código de barras EAN-13 através do cálculo do seu dígito verificador.

    O algoritmo baseia-se na norma global do sistema GS1, utilizando o cálculo de Módulo 10.
    Os primeiros 12 dígitos compõem o corpo do código, e o 13º é o checksum de segurança. 
    A validação garante que falhas de leitura ótica ou erros de extração web
    sejam detetados antes da inserção na base de dados.

    :param ean: Sequência de caracteres que representa o código de barras completo.
    :type ean: str
    :return: True se a string contiver exatamente 13 numerais e o checksum for matematicamente válido; False em qualquer cenário de não conformidade ou formato inválido.
    :rtype: bool
    """
    # Verificação de sanitização: garante que a entrada é uma string estritamente numérica com 13 posições
    if not (isinstance(ean, str) and len(ean) == 13 and ean.isdigit()):
        return False
    
    try:
        # Extrai os 12 primeiros dígitos (corpo estrutural do EAN) convertendo-os em inteiros
        corpo = [int(d) for d in ean[:12]]
        
        # Aplica a regra de pesos alternados do GS1: 
        # Dígitos em posições ímpares (índice par na lista) multiplicam por 1.
        # Dígitos em posições pares (índice ímpar na lista) multiplicam por 3.
        pesos = [1, 3] * 6
        soma = sum(d * p for d, p in zip(corpo, pesos))
        
        # Calcula o dígito verificador subtraindo o último dígito da soma (módulo 10) da dezena imediatamente superior (ou 10).
        digito_esperado = (10 - (soma % 10)) % 10
        
        # Compara o dígito matematicamente esperado com o 13º dígito fornecido na string
        return int(ean[12]) == digito_esperado
        
    except ValueError:
        # Fallback de segurança caso a conversão para int falhe num cenário atípico de memória
        return False