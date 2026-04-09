"""
Pacote de Modelos de Domínio (ORM) da Aplicação.

Este pacote concentra todas as entidades de banco de dados mapeadas
através do SQLAlchemy. A importação centralizada neste módulo garante 
que os metadados de todas as tabelas sejam devidamente registrados na 
classe base antes da execução de migrações ou criação do esquema de banco.

Módulos e Classes Exportadas:
    * :class:`~models.base.Base`: Classe base declarativa com configurações de nomenclatura.
    * :class:`~models.farmacia.Farmacia`: Entidade que representa as farmácias físicas e jurídicas.
    * :class:`~models.catalogo.CatalogoBase`: Entidade que representa o catálogo unificado com dados farmacológicos invariáveis.
    * :class:`~models.oferta_farmacia.OfertaFarmacia`: Entidade que representa a precificação e a disponibilidade (oferta) de um item numa loja.

.. note::
    Para o correto funcionamento das migrações, certifique-se de importar 
    o objeto ``Base`` diretamente deste módulo dentro do arquivo ``env.py`` 
    do Alembic (ex: ``from models import Base``).
"""

from .base import Base
from .farmacia import Farmacia
from .catalogo import CatalogoBase
from .oferta_farmacia import OfertaFarmacia

__all__ = [
    "Base",
    "Farmacia",
    "CatalogoBase",
    "OfertaFarmacia",
]