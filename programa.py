import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import zipfile

# --- CONFIGURAÇÃO ---
# ⚙️ As credenciais ainda são fixas, mas a URL e a pasta de destino serão solicitadas

# URL da PÁGINA DE LOGIN do site (geralmente não muda)
URL_DA_PAGINA_LOGIN = 'https://moodle.imd.ufrn.br/login/index.php'

# Suas credenciais
SEU_LOGIN = 'SEU_NOME_DE_USUARIO'
SUA_SENHA = 'SUA_SENHA'

# --- INÍCIO DO SCRIPT ---

def baixar_tudo(url_pagina_downloads, pasta_destino):
    """
    Função que faz login, baixa e descompacta os arquivos.
    Agora recebe a URL de downloads e a pasta de destino como parâmetros.
    """
    print("🚀 Iniciando o processo...")

    # Usamos uma sessão para manter o estado de login (cookies)
    with requests.Session() as session:
        
        # --- ETAPA 1: PEGAR O TOKEN DE LOGIN ---
        try:
            print(f"Acessando a página de login para obter o token de segurança...")
            resposta_inicial = session.get(URL_DA_PAGINA_LOGIN)
            resposta_inicial.raise_for_status()
            
            soup_login = BeautifulSoup(resposta_inicial.text, 'html.parser')
            token_input = soup_login.find('input', {'name': 'logintoken'})
            
            if not token_input:
                print("❌ ERRO: Não foi possível encontrar o 'logintoken' na página de login.")
                return
            
            logintoken = token_input['value']
            print(f"✅ Token de segurança encontrado!")

        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao acessar a página de login: {e}")
            return

        # --- ETAPA 2: FAZER O LOGIN COM O TOKEN ---
        login_data = {
            'anchor': '',
            'logintoken': logintoken,
            'username': SEU_LOGIN,
            'password': SUA_SENHA,
        }
        
        try:
            print("Enviando credenciais e token para autenticação...")
            resposta_login = session.post(URL_DA_PAGINA_LOGIN, data=login_data)
            resposta_login.raise_for_status()
            
            if "login/index.php" in resposta_login.url or "invalidlogin" in resposta_login.text:
                print("❌ Falha no login! Verifique seu usuário e senha.")
                return

            print("✅ Login realizado com sucesso!")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro durante a tentativa de login: {e}")
            return

        # --- ETAPA 3: IR PARA A PÁGINA DE DOWNLOADS E BAIXAR OS ARQUIVOS ---
        # Usa a variável 'pasta_destino' que foi passada como parâmetro
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
            print(f"Pasta '{pasta_destino}' criada.")
        
        try:
            # Usa a variável 'url_pagina_downloads' que foi passada como parâmetro
            print(f"Acessando a página de downloads: {url_pagina_downloads}")
            response = session.get(url_pagina_downloads)
            response.raise_for_status()

            soup_downloads = BeautifulSoup(response.text, 'html.parser')
            links_zip = soup_downloads.find_all('a', href=lambda href: href and href.endswith('.zip'))

            if not links_zip:
                print("Login bem-sucedido, mas nenhum link .zip foi encontrado na página de downloads.")
                return

            print(f"✅ Encontrados {len(links_zip)} arquivos .zip para baixar.")

            for link in links_zip:
                url_arquivo = urljoin(url_pagina_downloads, link['href'])
                nome_arquivo = url_arquivo.split('/')[-1]
                caminho_local = os.path.join(pasta_destino, nome_arquivo)

                print(f"  -> Baixando '{nome_arquivo}'...")
                with session.get(url_arquivo, stream=True) as r:
                    r.raise_for_status()
                    with open(caminho_local, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                print(f"     '{nome_arquivo}' baixado com sucesso!")

                print(f"  -> Descompactando '{nome_arquivo}'...")
                try:
                    with zipfile.ZipFile(caminho_local, 'r') as zip_ref:
                        zip_ref.extractall(pasta_destino)
                    print(f"     Arquivo descompactado!")
                    os.remove(caminho_local)
                    print(f"     Arquivo .zip removido.")
                except zipfile.BadZipFile:
                    print(f"     Erro: O arquivo '{nome_arquivo}' não é um zip válido.")
                except Exception as e:
                    print(f"     Ocorreu um erro ao descompactar: {e}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Falha ao acessar a página de downloads. Erro: {e}")
            return
    
    print(f"\n✨ Processo concluído! Verifique a pasta '{pasta_destino}'.")

# --- Lógica Principal de Execução ---
if __name__ == '__main__':
    # Primeiro, verifica se as credenciais foram preenchidas no código
    if 'SEU_NOME_DE_USUARIO' in SEU_LOGIN or 'SUA_SENHA' in SUA_SENHA:
        print("⚠️ Atenção! Você precisa configurar as variáveis SEU_LOGIN e SUA_SENHA no script antes de usar.")
    else:
        # Se as credenciais estiverem OK, pede as informações ao usuário
        print("--- Automatizador de Downloads IMD ---")
        
        url_input = input("➡️  Cole a URL da página com os arquivos para baixar e pressione Enter: \n")
        pasta_input = input("➡️  Digite o nome da pasta de destino para salvar os arquivos e pressione Enter: \n")
        
        # Validação simples para garantir que o usuário digitou algo
        if not url_input.strip() or not pasta_input.strip():
            print("\n❌ URL e nome da pasta não podem estar vazios. O programa será encerrado.")
        else:
            # Chama a função principal com os dados fornecidos pelo usuário
            baixar_tudo(url_input.strip(), pasta_input.strip())
