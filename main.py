from flask import Flask, request, jsonify
from collections import defaultdict
from statistics import median

app = Flask(__name__)

# ==========================================
# FUNÇÃO PARA REMOVER OUTLIERS (IQR)
# ==========================================
def remover_outliers(lista):
    
    if len(lista) < 4:
        return lista

    lista_ordenada = sorted(lista)

    meio = len(lista_ordenada) // 2

    if len(lista_ordenada) % 2 == 0:
        inferior = lista_ordenada[:meio]
        superior = lista_ordenada[meio:]
    else:
        inferior = lista_ordenada[:meio]
        superior = lista_ordenada[meio + 1:]

    q1 = median(inferior)
    q3 = median(superior)

    iqr = q3 - q1

    limite_inferior = q1 - (1.5 * iqr)
    limite_superior = q3 + (1.5 * iqr)

    filtrados = [
        x for x in lista
        if limite_inferior <= x <= limite_superior
    ]

    return filtrados


# ==========================================
# ROTA PRINCIPAL
# ==========================================
@app.route('/')
def home():
    return "API de previsão funcionando!"


# ==========================================
# ROTA DE PREVISÃO
# ==========================================
@app.route('/prever', methods=['POST'])
def prever():

    try:

        dados = request.get_json()

        if not dados:
            return jsonify({
                "status": "erro",
                "mensagem": "Nenhum dado recebido"
            }), 400

        # ==========================================
        # ORGANIZAR VENDAS POR PRODUTO
        # ==========================================
        vendas_por_produto = defaultdict(list)

        for item in dados:

            # Validação básica
            if (
                "produto" not in item or
                "total_vendido" not in item
            ):
                continue

            produto = item["produto"]

            try:
                quantidade = float(item["total_vendido"])
            except:
                continue

            # Ignorar valores inválidos
            if quantidade <= 0:
                continue

            vendas_por_produto[produto].append(quantidade)

        # ==========================================
        # CALCULAR PREVISÕES
        # ==========================================
        previsoes = []

        for produto, vendas in vendas_por_produto.items():

            # Remover outliers
            vendas_filtradas = remover_outliers(vendas)

            if len(vendas_filtradas) == 0:
                continue

            media = sum(vendas_filtradas) / len(vendas_filtradas)

            previsao = round(media * 30)

            previsoes.append({
                "produto": produto,
                "media_diaria": round(media, 2),
                "previsao_proximo_mes": previsao,
                "quantidade_registros": len(vendas),
                "registros_utilizados": len(vendas_filtradas)
            })

        # ==========================================
        # TOP 5 PRODUTOS
        # ==========================================
        top_5 = sorted(
            previsoes,
            key=lambda x: x["previsao_proximo_mes"],
            reverse=True
        )[:5]

        return jsonify({
            "status": "ok",
            "total_produtos": len(previsoes),
            "top_5_produtos": top_5,
            "previsoes": previsoes
        })

    except Exception as e:

        return jsonify({
            "status": "erro",
            "mensagem": str(e)
        }), 500


# ==========================================
# EXECUÇÃO
# ==========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)