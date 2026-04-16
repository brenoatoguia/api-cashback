from fastapi import FastAPI, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Usando SQLite temporariamente para testar localmente
DATABASE_URL = "postgresql://neondb_owner:npg_kp0ED5KqnPVw@ep-curly-pond-an4dbm19.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Configuração do Banco (O connect_args é necessário apenas para o SQLite)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo da Tabela
class ConsultaModel(Base):
    __tablename__ = "consultas_cashback"
    id = Column(Integer, primary_key=True, index=True)
    ip_usuario = Column(String, index=True)
    tipo_cliente = Column(String)
    valor_compra = Column(Float)
    valor_cashback = Column(Float)
    data_consulta = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cashback API Nology")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompraRequest(BaseModel):
    tipo_cliente: str  # "vip" ou "normal"
    valor_compra: float

# Importando a função isolada da Questão 1 (assumindo cupom 0% na interface, conforme enunciado)
def calcular_cashback_final(valor_original: float, percentual_desconto: float, is_vip: bool) -> float:
    valor_final = valor_original * (1 - percentual_desconto / 100)
    cashback_base = valor_final * 0.05
    bonus_vip = (cashback_base * 0.10) if is_vip else 0.0
    total = cashback_base + bonus_vip
    if valor_final > 500:
        total *= 2
    return round(total, 2)

@app.post("/calcular")
def calcular_e_registrar(req: CompraRequest, request: Request):
    ip_cliente = request.client.host
    is_vip = req.tipo_cliente.lower() == "vip"
    
    # Enunciado pede apenas valor_compra e tipo, assumimos desconto 0.
    cashback = calcular_cashback_final(req.valor_compra, 0.0, is_vip)
    
    # Registrar no BD
    db = SessionLocal()
    nova_consulta = ConsultaModel(
        ip_usuario=ip_cliente,
        tipo_cliente=req.tipo_cliente,
        valor_compra=req.valor_compra,
        valor_cashback=cashback
    )
    db.add(nova_consulta)
    db.commit()
    db.close()
    
    return {"cashback": cashback}

@app.get("/historico")
def listar_historico(request: Request):
    ip_cliente = request.client.host
    db = SessionLocal()
    # Filtra as consultas EXCLUSIVAMENTE pelo IP de quem chamou a API
    historico = db.query(ConsultaModel).filter(ConsultaModel.ip_usuario == ip_cliente).order_by(ConsultaModel.id.desc()).all()
    db.close()
    return historico