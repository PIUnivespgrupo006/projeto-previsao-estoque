from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "API funcionando!"

@app.route('/prever', methods=['POST'])
def prever():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Nenhum dado recebido"}), 400

        total = 0
        count = 0

        for item in dados:
            if "total_vendido" in item:
                total += item["total_vendido"]
                count += 1

        if count == 0:
            return jsonify({"erro": "Dados inválidos"}), 400

        media = total / count
        previsao = round(media * 30)

        return jsonify({
            "status": "ok",
            "previsao_proximo_mes": previsao
        })

    except Exception as e:
        return jsonify({
            "status": "erro",
            "mensagem": str(e)
        }), 500