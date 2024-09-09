from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

jsonListEnglish = []
jsonListPortugues = []

def search_and_extract(search_term, language):
    search_url = search_term
    response = requests.get(search_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table_div = soup.find('table')  # Ajuste o seletor conforme necessário

        if table_div:
            text_content = table_div.get_text(separator='\n', strip=True)
            terms_list = text_content.split('\n')

            data = {
                'search_term': search_term,
                'terms': terms_list
            }
            return data
        else:
            return {"error": "Table not found."}
    else:
        return {"error": f"Failed to retrieve search results. Status code: {response.status_code}"}

def search_and_extract_PUBMED(search_url):
    # Enviar a solicitação GET
    response = requests.get(search_url)

    # Verifique se a solicitação foi bem-sucedida
    if response.status_code == 200:
        # Fazer o parsing do conteúdo HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrar a div com a classe 'rprt abstract'
        div_class = 'rprt abstract'
        div = soup.find('div', class_=div_class)  # Encontrar a div pela classe

        if div:
            # Extrair todo o texto dentro da div
            text_content = div.get_text(separator='\n', strip=True)

            # Separar o texto em uma lista de termos usando o caractere de nova linha
            terms_list = text_content.split('\n')

            return terms_list
        else:
            return "Div with class 'rprt abstract' not found."
    else:
        return f"Failed to retrieve search results. Status code: {response.status_code}"

@app.route('/searchPubMed', methods=['GET'])
def searchPubMed():
    search_term = request.args.get('term')
    if not search_term:
        return jsonify({"error": "Nenhum termo de pesquisa fornecido"}), 400
        
    if search_term[:34] == "https://www.ncbi.nlm.nih.gov/mesh/":    

        # Realiza a busca
        terms_list = search_and_extract_PUBMED(search_term)
    
        if isinstance(terms_list, str):
            return jsonify({"error": terms_list}), 404
    
        # Processa os termos e formata a r0esposta
        disctCorrect = {"Components":[]}
        UltText = ''
    
        for text in terms_list:
            if text == "Emigration and Immigration":
                disctCorrect['Components'].append(text)
            elif text[-1] == ":":
                disctCorrect[text] = []
                UltText = text
            elif UltText == '':
                disctCorrect['Components'].append(text)
            else:
                disctCorrect[UltText].append(text)
    
        stringCorrect = ''
        MH = ''
    
        for i, val in disctCorrect.items():
            if i == "Components":
                for i in val:
                    stringCorrect += (f'"{i}"[Mesh] ')
                    break
            elif i == "Entry Terms:":
                for i in val:
                    if i == 'All MeSH Categories':
                        break
                    else:  
                        stringCorrect += (f'OR ({i}) ')
            else:
                continue
    
        return jsonify({
            # "formatted_data": disctCorrect,
            "result": stringCorrect + MH
        })
    else:
        return jsonify({"error": "O link não está correto, verifique o link e tente novamente."}), 400;

@app.route('/search', methods=['GET'])
def search():
    search_term = request.args.get('search_term')
    language = request.args.get('language')

    # Verificar se search_term começa com a URL esperada
    if search_term[:25] == "https://decs.bvsalud.org/":
        try:
            # Fazer uma solicitação HTTP para verificar a URL
            response = requests.get(search_term)

            if response.status_code == 200:
                # Lógica para processar a pesquisa
                if not search_term or not language:
                    return jsonify({"error": "Missing search_term or language"}), 400

                if language == 'english':
                    result = search_and_extract(search_term, 'english')
                    jsonListEnglish.append(result["terms"])
                elif language == 'portuguese':
                    result = search_and_extract(search_term, 'portuguese')
                    jsonListPortugues.append(result["terms"])
                else:
                    return jsonify({"error": "Invalid language. Use 'english' or 'portuguese'."}), 400

                return jsonify(result)
            else:
                jsonListEnglish.clear()
                jsonListPortugues.clear()
                return jsonify({"error": "O link não está correto, verifique o link e tente novamente."}), 400
        except requests.RequestException as e:
            jsonListEnglish.clear()
            jsonListPortugues.clear()
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    else:
        jsonListEnglish.clear()
        jsonListPortugues.clear()
        return jsonify({"error": "O link não está correto, verifique o link e tente novamente."}), 400

@app.route('/process', methods=['GET'])
def process():
    spanishDescription = request.args.get('spanishDescription')
    frenchDescription = request.args.get('frenchDescription')
    typeSearch = request.args.get('typeSearch')

    if typeSearch == '1':
        disctCorretEnglish = {}
        disctCorretPortugues = {}
        UltTextEnglish = ''
        UltTextPortugues = ''

        # Verifica se jsonListEnglish não está vazio antes de processar
        if jsonListEnglish:
            for text in jsonListEnglish[0]:
                if text[-1] == ":":
                    disctCorretEnglish[text] = []
                    UltTextEnglish = text
                else:
                    disctCorretEnglish[UltTextEnglish].append(text)

            # Processa jsonListPortugues mesmo que jsonListEnglish esteja vazio
            for text in jsonListPortugues[0]:
                if text[-1] == ":":
                    disctCorretPortugues[text] = []
                    UltTextPortugues = text
                else:
                    disctCorretPortugues[UltTextPortugues].append(text)

            # Atualiza disctCorretPortugues com dados de disctCorretEnglish
            for i, val in disctCorretEnglish.items():
                if i == "Entry term(s):":
                    disctCorretPortugues[i] = val

        else:
            # Processa jsonListPortugues caso jsonListEnglish esteja vazio
            for text in jsonListPortugues[0]:
                if text[-1] == ":":
                    disctCorretPortugues[text] = []
                    UltTextPortugues = text
                else:
                    disctCorretPortugues[UltTextPortugues].append(text)

        stringCorrect = ''
        MH = ''

        # Monta a string de resultado baseado em disctCorretPortugues
        for i, val in disctCorretPortugues.items():
            if i == "Descritor em português:":
                stringCorrect += (f'MH:"{val[0]}" ')
            elif i == 'Código(s) hierárquico(s):':
                for item in val:
                    MH += (f'OR MH:{item}$ ')
            elif i == "Descritor em inglês:":
                stringCorrect += (f'OR ({val[0]}) ')
            elif i == 'Descritor em espanhol:' and spanishDescription == 'true':
                stringCorrect += (f'OR ({val[0]}) ')
                continue
            elif i == 'Descritor em francês:' and frenchDescription == 'true':
                stringCorrect += (f'OR ({val[0]}) ')
                continue
            elif i == "Termo(s) alternativo(s):":
                for item in val:
                    stringCorrect += (f'OR ({item}) ')
            elif i == "Entry term(s):":
                for item in val:
                    stringCorrect += (f'OR ({item}) ')
            else:
                continue

        jsonListEnglish.clear()
        jsonListPortugues.clear()

        return jsonify({"result": f"{stringCorrect + MH }"})

    # Caso `typeSearch` não seja '1'
    return jsonify({"error": "Invalid typeSearch value. Ensure it is '1'."}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
