from flask import Flask, request, jsonify
from collections import defaultdict
from statistics import median

app = Flask(__name__)

# ==========================================
# REMOVER OUTLIERS (IQR)
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
# HOME
# ==========================================
@app.route('/')
def home():
    return "API NOVA FUNCIONANDO"


# ==========================================
# PREVISÃO
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

        vendas_por_produto = defaultdict(list)

        # ==========================================
        # ORGANIZAR DADOS
        # ==========================================
        for item in dados:

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

            # ignorar inválidos
            if quantidade <= 0:
                continue

            vendas_por_produto[produto].append(quantidade)

        previsoes = []

        # ==========================================
        # CALCULAR PREVISÕES
        # ==========================================
        for produto, vendas in vendas_por_produto.items():

            vendas_filtradas = remover_outliers(vendas)

            if len(vendas_filtradas) == 0:
                continue

            # ==========================================
            # TOTAL FILTRADO
            # ==========================================
            total_filtrado = sum(vendas_filtradas)

            # ==========================================
            # MÉDIA MENSAL (12 MESES)
            # ==========================================
            media_mensal = total_filtrado / 12

            previsao = round(media_mensal)

            # ==========================================
            # NÍVEL DE CONFIANÇA
            # ==========================================
            qtd = len(vendas_filtradas)

            if qtd >= 10:
                confianca = "Alta"
            elif qtd >= 5:
                confianca = "Média"
            else:
                confianca = "Baixa"

            previsoes.append({
                "produto": produto,
                "media_mensal": round(media_mensal, 2),
                "previsao_proximo_mes": previsao,
                "quantidade_registros": len(vendas),
                "registros_utilizados": qtd,
                "confianca": confianca
            })

        # ==========================================
        # TOP 5
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