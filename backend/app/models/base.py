"""
Módulo responsável pela configuração central do mapeamento objeto-relacional (ORM).
"""
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Dicionário de convenção de nomenclatura padrão para metadados relacionais.
# Garante que chaves e índices tenham nomes previsíveis no banco de dados.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Instância de MetaData injetando as convenções
metadata_obj = MetaData(naming_convention=NAMING_CONVENTION)

class Base(DeclarativeBase):
    """
    Classe base declarativa para todos os modelos de domínio do SQLAlchemy.

    Esta classe serve como registro central para as entidades mapeadas, 
    incorporando convenções de nomenclatura padronizadas para garantir 
    a estabilidade e previsibilidade das migrações de esquema (via Alembic).

    :cvar metadata: Objeto MetaData configurado com convenções de nomenclatura.
    :type metadata: sqlalchemy.MetaData
    """
    metadata = metadata_obj