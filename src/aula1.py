# %%
# Packages
import os
import time 
import pandas as pd

from binance.client import Client
from binance.enums import *

from dotenv import load_dotenv

# %%
# Config
load_dotenv()

api_key = os.getenv("KEY_BINANCE")
secret_key = os.getenv("SECRET_BINANCE")

cliente_binance = Client(api_key, secret_key)

# %%
# Parâmetros

codigo_operado = "SOLBRL"
ativo_operado = "SOL"
periodo_candle = Client.KLINE_INTERVAL_1HOUR
quantidade = 0.01

symbol_info = cliente_binance.get_symbol_info(codigo_operado)
lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
min_qty = float(lot_size_filter['minQty'])
max_qty = float(lot_size_filter['maxQty'])
step_size = float(lot_size_filter['stepSize'])

print(lot_size_filter, min_qty, max_qty, step_size)

# %%
# Funções
def corrigir_casas_decimais(n: float, casas: int) -> int:
    return int(n * 10**casas) / 10**casas


def mostrar_ativos_disponiveis(cliente_binance: Client) -> None:
    
    conta = cliente_binance.get_account()
    
    for ativo in conta["balances"]:
        if float(ativo["free"]) > 0:
            print(ativo)

         
def executar_ordem_mercado(operacao: str, codigo: str, quantidade: float) -> None:
    
    if operacao.lower() == "compra":
        side = SIDE_BUY
    elif operacao.lower() == "venda":
        side = SIDE_SELL
    
    order = cliente_binance.create_order(
        symbol=codigo, # BTCBRL, ETHBRL, SOLBRL...
        side=side,
        type=ORDER_TYPE_MARKET,
        quantity=quantidade
    )
    
    print(f"ATIVO {codigo} NEGOCIADO:")
    print(order)


def buscar_dados(codigo: str, intervalo: str) -> pd.DataFrame:
    
    candles = cliente_binance.get_klines(symbol = codigo, interval = intervalo, limit = 1000)
    precos = pd.DataFrame(candles)
    precos.columns = [
        "tempo_abertura", "abertura", "maxima", "minima", "fechamento",
        "volume", "tempo_fechamento", "moedas_negociadas", "numero_trades",
        "volume_ativo_base_compra", "volume_ativo_cotação", "-"
    ]
    precos = precos[["fechamento", "tempo_fechamento"]]
    precos["tempo_fechamento"] = pd.to_datetime(precos["tempo_fechamento"], unit = "ms").dt.tz_localize("UTC")
    precos["tempo_fechamento"] = precos["tempo_fechamento"].dt.tz_convert("America/Sao_Paulo")
    
    return precos


def estrategia_trade(dados: pd.DataFrame, codigo_ativo: str, ativo_operado: str, quantidade_comprada: float, posicao: bool) -> bool:
    
    dados["media_rapida"] = dados["fechamento"].rolling(window = 7).mean()
    dados["media_devagar"] = dados["fechamento"].rolling(window = 40).mean()
    
    ultima_media_rapida = dados["media_rapida"].iloc[-1]
    ultima_media_devagar = dados["media_devagar"].iloc[-1]
    
    print(f"Última Média Rápida: {ultima_media_rapida} | Última Média Devagar: {ultima_media_devagar}")
    
    conta = cliente_binance.get_account()
    
    for ativo in conta["balances"]:
        if ativo["asset"] == ativo_operado:
            quantidade_atual = float(ativo["free"])
            
    if ultima_media_rapida > ultima_media_devagar:
        if posicao == False:
            executar_ordem_mercado(
                operacao="compra",
                codigo=codigo_operado,
                quantidade=quantidade_comprada
            )
            posicao = True
            
    elif ultima_media_rapida < ultima_media_devagar:
        if posicao == True:
            executar_ordem_mercado(
                operacao="venda",
                codigo=codigo_operado,
                quantidade=quantidade_atual
            )
            posicao = False
            
    return posicao

# %%
# Executar
posicao_atual = True
# while True:

dados_atualizados = buscar_dados(codigo=codigo_operado, intervalo=periodo_candle)
posicao_atual = estrategia_trade(
    dados=dados_atualizados,
    codigo_ativo=codigo_operado, 
    ativo_operado=ativo_operado,
    quantidade_comprada=quantidade,
    posicao=posicao_atual
)

# %%
