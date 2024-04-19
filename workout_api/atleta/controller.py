from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, Query, status
from pydantic import UUID4

from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate, AtletaBasico
from workout_api.atleta.models import AtletaModel
from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DatabaseDependency

# Incluido para paginação
from fastapi_pagination.utils import disable_installed_extensions_check
disable_installed_extensions_check()
from fastapi_pagination import Page, LimitOffsetPage, paginate

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

router = APIRouter()

def cpf_formatado(cpf) -> str:
    """
    Formata o CPF para exibição.
    """
    return f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"

@router.post(
    '/', 
    summary='Criar um novo atleta',
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut
)
async def post(
    db_session: DatabaseDependency, 
    atleta_in: AtletaIn = Body(...)
):
    categoria_nome = atleta_in.categoria.nome
    centro_treinamento_nome = atleta_in.centro_treinamento.nome
    cpf_input = atleta_in.cpf

    categoria = (await db_session.execute(
        select(CategoriaModel).filter_by(nome=categoria_nome))
    ).scalars().first()
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f'A categoria {categoria_nome} não foi encontrada.'
        )
    
    centro_treinamento = (await db_session.execute(
        select(CentroTreinamentoModel).filter_by(nome=centro_treinamento_nome))
    ).scalars().first()
    
    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f'O centro de treinamento {centro_treinamento_nome} não foi encontrado.'
        )

    try: 
        #atleta_out = AtletaOut(id=uuid4(), created_at=datetime.utcnow(), **atleta_in.model_dump())
        atleta_out = AtletaOut(id=uuid4(), created_at=datetime.now(timezone.utc).replace(tzinfo=None), **atleta_in.model_dump())
        atleta_model = AtletaModel(**atleta_out.model_dump(exclude={'categoria', 'centro_treinamento'}))
        atleta_model.categoria_id = categoria.pk_id
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id
        
        db_session.add(atleta_model)
        await db_session.commit()

    except IntegrityError:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Já existe um atleta cadastrado com o cpf: {cpf_formatado(cpf=cpf_input)}"
        )

    except Exception:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Ocorreu um erro ao inserir os dados no banco"
        )

    return atleta_out


@router.get(
    '/', 
    summary='Consultar todos os Atletas',
    status_code=status.HTTP_200_OK,
    response_model=Page[AtletaOut],
)

# Incluido para paginação  
async def query(db_session: DatabaseDependency, offset: int = 0, limit: int = 10) -> LimitOffsetPage[AtletaOut]:
    atletas: list[AtletaOut] = (await db_session.execute(select(AtletaModel))).scalars().all()

    # Incluido para paginação
    return paginate([AtletaOut.model_validate(atleta) for atleta in atletas])

@router.get(
    '/all', 
    summary='Consultar todos os Atletas exibindo nome, categoria e centro de treinamento',
    status_code=status.HTTP_200_OK,
    response_model=Page[AtletaBasico],
)
async def query(db_session: DatabaseDependency, offset: int = 0, limit: int = 10) -> LimitOffsetPage[AtletaBasico]:
    atletas: list[AtletaBasico] = (await db_session.execute(select(AtletaModel))).scalars().all()
    return paginate([AtletaBasico.model_validate(atleta) for atleta in atletas])


@router.get(
    '/{id}', 
    summary='Consulta um Atleta pelo id',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def get(id: UUID4, db_session: DatabaseDependency) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f'Atleta não encontrado no id: {id}'
        )
    
    return atleta


@router.patch(
    '/{id}', 
    summary='Editar um Atleta pelo id',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def patch(id: UUID4, db_session: DatabaseDependency, atleta_up: AtletaUpdate = Body(...)) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f'Atleta não encontrado no id: {id}'
        )
    
    atleta_update = atleta_up.model_dump(exclude_unset=True)
    for key, value in atleta_update.items():
        setattr(atleta, key, value)

    await db_session.commit()
    await db_session.refresh(atleta)

    return atleta


@router.delete(
    '/{id}', 
    summary='Deletar um Atleta pelo id',
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete(id: UUID4, db_session: DatabaseDependency) -> None:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f'Atleta não encontrado no id: {id}'
        )
    
    await db_session.delete(atleta)
    await db_session.commit()


@router.get(
    '/cpf/{cpf}', 
    summary='Consulta um Atleta pelo cpf',
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut,
)
async def get(cpf: str, db_session: DatabaseDependency) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(cpf=cpf))
    ).scalars().first()

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f'Atleta não encontrado no CPF: {cpf_formatado(cpf)}'
        )
    
    return atleta

# Consultar atleta pelo nome parcial e case insesitive
@router.get(
    '/nome/{nome}', 
    summary='Consultar Atletas pelo nome',
    status_code=status.HTTP_200_OK,
    response_model=Page[AtletaOut],
)
async def get(nome: str, db_session: DatabaseDependency) -> LimitOffsetPage[AtletaOut]:
    atletas: list[AtletaOut] = (await db_session.execute(select(AtletaModel).filter(AtletaModel.nome.ilike(f"{nome}%")))).scalars().all()
    if not atletas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f'Atleta não encontrado'
        )
    
    return paginate([AtletaOut.model_validate(atleta) for atleta in atletas])

