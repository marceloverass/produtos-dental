from flask import Flask, request, render_template_string
import pandas as pd
from fuzzywuzzy import fuzz, process
from unidecode import unidecode

app = Flask(__name__)

# Carregar a lista de produtos
df = pd.read_excel('lista_de_produtos.xlsx')
produtos = {unidecode(item).lower(): preco for item, preco in zip(df['Item'], df['Preço'])}

sinonimos = {
    'luva': 'luvas de procedimento (brancas, rosas ou pretas)',
    'luvas': 'luvas de procedimento (brancas, rosas ou pretas)',
}

def buscar_com_sinonimos(produto_cliente):
    produto_normalizado = unidecode(produto_cliente).lower()
    return sinonimos.get(produto_normalizado, produto_normalizado)

def encontrar_produtos(produto_cliente, produtos, limite=10, pontuacao_minima=80):
    produto_cliente = buscar_com_sinonimos(produto_cliente)
    
    # Busca múltiplos resultados que correspondem ao produto do cliente
    resultados = process.extract(
        produto_cliente, 
        produtos.keys(), 
        scorer=fuzz.partial_ratio,  # Usa uma função de pontuação mais permissiva
        limit=limite
    )
    
    # Filtra resultados com base na pontuação mínima e que contém o termo da busca
    produtos_encontrados = [
        (produto, produtos[produto]) 
        for produto, score in resultados 
        if score >= pontuacao_minima and produto_cliente in produto
    ]
    
    # Formata os nomes dos produtos para capitalização
    produtos_encontrados = [
        (produto.title(), preco) 
        for produto, preco in produtos_encontrados
    ]
    
    return produtos_encontrados

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    if request.method == "POST":
        lista_cliente = request.form["lista"]
        itens_cliente = [item.strip() for item in lista_cliente.split('\n') if item.strip()]

        for item in itens_cliente:
            produtos_encontrados = encontrar_produtos(item, produtos)
            if produtos_encontrados:
                for produto, preco in produtos_encontrados:
                    preco_desconto = preco * 0.9  # Aplica 10% de desconto
                    resultados.append(f"{produto} \nPreço: R${preco:.2f} | Preço com Desconto (Pix/Dinheiro): R${preco_desconto:.2f}")
            else:
                resultados.append(f"Produto '{item}' não encontrado na lista.")

    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Busca de Produtos</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            pre {
                white-space: pre-wrap; /* Mantém os espaços e quebras de linha */
                font-family: monospace; /* Fonte monoespaçada para melhor visualização */
            }
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <h2 class="text-center mb-4">Busca de Produtos</h2>
            <form method="post" class="mb-4">
                <div class="mb-3">
                    <textarea name="lista" rows="10" class="form-control" placeholder="Digite os produtos, um por linha..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary w-100">Processar Lista</button>
            </form>
            
            {% if resultados %}
                <div class="alert alert-info">
                    <h4 class="alert-heading">Resultados:</h4>
                    <pre id="resultados">{{ resultados|safe }}</pre>
                    <button class="btn btn-secondary mt-2" onclick="copiarResultados()">Copiar</button>
                </div>
            {% endif %}
        </div>

        <script>
            function copiarResultados() {
                var resultados = document.getElementById("resultados");
                var range = document.createRange();
                range.selectNode(resultados);
                window.getSelection().removeAllRanges();
                window.getSelection().addRange(range);
                document.execCommand("copy");
                window.getSelection().removeAllRanges();
                alert("Resultados copiados para a área de transferência!");
            }
        </script>

        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.min.js"></script>
    </body>
    </html>
    ''', resultados="\n\n".join(resultados))

if __name__ == "__main__":
    app.run(debug=True)
