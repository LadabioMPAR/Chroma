import os
import time
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ================= CONFIGURAÇÕES =================
PASTA_ORIGEM = r'C:\Caminho\Para\Os\Dados\Do\HPLC'
ARQUIVO_CREDENCIAIS = 'credenciais.json'
ID_PASTA_DRIVE_PRINCIPAL = 'COLOQUE_O_ID_DA_PASTA_PRINCIPAL_AQUI'
# =================================================

# Autenticação com escopo ampliado para gerenciar subpastas
SCOPES = ['https://www.googleapis.com/auth/drive']
creds = service_account.Credentials.from_service_account_file(ARQUIVO_CREDENCIAIS, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

def obter_ou_criar_pasta_do_dia():
    """Busca a subpasta com a data de hoje. Se não existir, cria."""
    hoje = datetime.now().strftime('%Y-%m-%d') # Formato: YYYY-MM-DD
    
    # Query para buscar a pasta de hoje dentro da pasta principal
    query = f"name='{hoje}' and mimeType='application/vnd.google-apps.folder' and '{ID_PASTA_DRIVE_PRINCIPAL}' in parents and trashed=false"
    
    resultados = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    pastas = resultados.get('files', [])
    
    if pastas:
        # Se a pasta já existe hoje, retorna o ID dela
        return pastas[0]['id']
    else:
        # Se não existe, cria a pasta com a data de hoje
        metadata_pasta = {
            'name': hoje,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [ID_PASTA_DRIVE_PRINCIPAL]
        }
        print(f"Criando nova subpasta para hoje: {hoje}")
        nova_pasta = drive_service.files().create(body=metadata_pasta, fields='id').execute()
        return nova_pasta.get('id')

def fazer_upload_e_apagar(caminho_arquivo):
    nome_arquivo = os.path.basename(caminho_arquivo)
    
    # 1. Pega o ID da subpasta correta (com a data de hoje)
    id_pasta_destino = obter_ou_criar_pasta_do_dia()
    
    # 2. Configura o upload
    file_metadata = {'name': nome_arquivo, 'parents': [id_pasta_destino]}
    # Removido o mimetype específico para aceitar qualquer tipo de arquivo (pdf, txt, cdf, etc)
    media = MediaFileUpload(caminho_arquivo, resumable=True)
    
    try:
        print(f"Iniciando upload de: {nome_arquivo} para a pasta de hoje...")
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Sucesso! {nome_arquivo} enviado para o Drive.")
        
        # 3. APAGA O ARQUIVO LOCAL APÓS O UPLOAD
        try:
            os.remove(caminho_arquivo)
            print(f"Limpeza: Arquivo local apagado -> {nome_arquivo}")
        except Exception as e_del:
            print(f"Atenção: Upload concluído, mas falha ao apagar o arquivo local {nome_arquivo}: {e_del}")
            
    except Exception as e_up:
        print(f"Erro crítico no upload de {nome_arquivo}: {e_up}")
        print("O arquivo não foi apagado do computador local para evitar perda de dados.")

class MeuMonitor(FileSystemEventHandler):
    def on_created(self, event):
        # Verifica se é um arquivo (ignora criação de diretórios locais)
        if not event.is_directory:
            print(f"Novo arquivo detectado: {event.src_path}")
            
            # ATENÇÃO REDOBRADA: Como vamos APAGAR o arquivo depois, precisamos 
            # ter certeza absoluta que o HPLC terminou de salvá-lo.
            # 15 segundos costumam ser suficientes, mas você pode aumentar se o arquivo for muito grande.
            time.sleep(15) 
            
            fazer_upload_e_apagar(event.src_path)

if __name__ == "__main__":
    event_handler = MeuMonitor()
    observer = Observer()
    observer.schedule(event_handler, PASTA_ORIGEM, recursive=False)
    observer.start()
    
    print(f"Monitorando a pasta: {PASTA_ORIGEM}...")
    print("Arquivos serão movidos para o Drive e apagados localmente.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()