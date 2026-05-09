from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/auth", tags=["Autenticação"])

TEST_USER = {
    "id": 1,
    "name": "Usuário Teste",
    "email": "teste@precobao.com",
    "password": "123456",
}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class LoginResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    message: str


class RegisterRequest(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    confirm_password: str = Field(min_length=6, max_length=100)


class RegisterResponse(BaseModel):
    message: str
    available: bool


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    if (
        payload.email.lower() != TEST_USER["email"]
        or payload.password != TEST_USER["password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    return LoginResponse(
        id=TEST_USER["id"],
        name=TEST_USER["name"],
        email=TEST_USER["email"],
        message="Login realizado com sucesso.",
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_202_ACCEPTED)
def register(payload: RegisterRequest):
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="As senhas não coincidem.",
        )

    if payload.email.lower() == TEST_USER["email"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email já está reservado para o usuário de teste.",
        )

    return RegisterResponse(
        message=(
            "Cadastro real ainda não está habilitado. "
            "Por enquanto, use o usuário de teste: teste@precobao.com / 123456."
        ),
        available=False,
    )