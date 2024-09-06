from flask import Flask, request, render_template_string
import pandas as pd
from fuzzywuzzy import fuzz, process

app = Flask(__name__)

df = pd.read_excel('lista_de_produtos.xlsx')
produtos = dict(zip(df['Item'], df['Preço']))

sinonimos = {
    'luva': 'Luvas de Procedimento (Brancas, Rosas ou Pretas)',
    'luvas': 'Luvas de Procedimento (Brancas, Rosas ou Pretas)',
}

def buscar_com_sinonimos(produto_cliente):
    if produto_cliente in sinonimos:
        return sinonimos[produto_cliente]
    return produto_cliente

def encontrar_produto(produto_cliente, produtos):
    produto_cliente = buscar_com_sinonimos(produto_cliente)
    produto_encontrado, score = process.extractOne(produto_cliente, produtos.keys(), scorer=fuzz.token_sort_ratio)
    if score > 75:
        return produto_encontrado, produtos[produto_encontrado]
    else:
        return None, None

@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    if request.method == "POST":
        lista_cliente = request.form["lista"]
        itens_cliente = [item.strip() for item in lista_cliente.split('\n') if item.strip()]
        
        for item in itens_cliente:
            produto, preco = encontrar_produto(item, produtos)
            if produto:
                resultados.append(f"Produto: {produto}, Preço: R${preco:.2f}")
            else:
                resultados.append(f"Produto '{item}' não encontrado na lista.")
    
    return render_template_string('''
        <form method="post">
            <textarea name="lista" rows="10" cols="50"></textarea><br>
            <input type="submit" value="Processar Lista">
        </form>
        <pre>{{ resultados }}</pre>
    ''', resultados="\n".join(resultados))

if __name__ == "__main__":
    app.run(debug=True)
