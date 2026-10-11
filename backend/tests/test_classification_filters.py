"""Regression tests for source-backed catalog filters."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.base import Base
from app.models.catalogo import CatalogoBase


def test_filters_use_official_exact_classification_and_keep_unknowns_unknown():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    with sessions() as db:
        db.add_all(
            [
                CatalogoBase(
                    name_search="Similar confirmado",
                    principio_ativo="Substância A",
                    laboratorio="Lab A",
                    categoria_regulatoria="Similar",
                    referencia_anvisa=True,
                    exige_receita_confirmada=True,
                    controle_especial=None,
                    categorias=["Generico"],  # Legacy inference must be ignored.
                ),
                CatalogoBase(
                    name_search="Genérico",
                    principio_ativo="Substância B",
                    laboratorio="Lab B",
                    categoria_regulatoria="Genérico",
                    referencia_anvisa=False,
                    exige_receita_confirmada=False,
                    categorias=["Similar"],
                ),
                CatalogoBase(
                    name_search="Sem registro confirmado",
                    principio_ativo="Substância C",
                    laboratorio="Lab C",
                    categorias=["Generico", "Indeterminado"],
                ),
            ]
        )
        db.commit()

    def override_db():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            similar = client.get("/catalogo?filtros=categoria:Similar")
            assert similar.status_code == 200
            assert [row["name_search"] for row in similar.json()["items"]] == [
                "Similar confirmado"
            ]
            legacy_mismatch = client.get("/catalogo?filtros=categoria:Genérico")
            assert [row["name_search"] for row in legacy_mismatch.json()["items"]] == [
                "Genérico"
            ]
            reference_and_similar = client.get(
                "/catalogo?filtros=categoria:Similar&filtros=referencia:sim"
            )
            assert reference_and_similar.json()["total"] == 1
            no_false_otc = client.get("/catalogo?filtros=receita:venda_livre")
            assert [row["name_search"] for row in no_false_otc.json()["items"]] == [
                "Genérico"
            ]
            unknown = client.get("/catalogo?filtros=classificacao:desconhecida")
            assert [row["name_search"] for row in unknown.json()["items"]] == [
                "Sem registro confirmado"
            ]
            options = client.get("/catalogo/filtros/opcoes").json()
            assert options["categorias"] == ["Genérico", "Similar"]
            assert options["contagens"]["desconhecida"] == 1
            invalid = client.get("/catalogo?filtros=foo:bar")
            assert invalid.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)
        engine.dispose()
