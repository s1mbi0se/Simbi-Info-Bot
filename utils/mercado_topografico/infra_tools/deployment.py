import os
import paramiko

from dotenv import load_dotenv

load_dotenv()

SSH_USER = os.getenv("SSH_USER")
SSH_HOST_STAGE = os.getenv("SSH_HOST_STAGE")
SSH_HOST_PROD01 = os.getenv("SSH_HOST_PROD01")
SSH_HOST_PROD02 = os.getenv("SSH_HOST_PROD02")
SSH_HOST_WHITELABEL = os.getenv("SSH_HOST_WHITELABEL")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_KEY_PATH = os.path.expanduser(os.getenv("SSH_KEY_PATH"))

SCRIPT_PATH_PROD = "/simbiose/script/shell/deployMercado/deployStage/manualDeployStage.sh"
SCRIPT_PATH_wHITELABEL = "/simbiose/script/shell/deployMercado/deployWhiteLabel/manualDeployWhiteLabel.sh"
SCRIPT_PATH_STAGE = "/simbiose/script/shell/deployMercado/deployStage/manualDeployStage.sh"

def deploy_production ():
    ENVIRONMENT = "production"
    BRANCH = "main"

    try:
        print("🔐 Iniciando conexão SSH...")
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=SSH_HOST_PROD01, 
            port=SSH_PORT,
            username=SSH_USER,
            pkey=key            
        )

        command = f"bash {SCRIPT_PATH_PROD} {ENVIRONMENT} {BRANCH}"
        print(f"🚀 Executando comando: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)

        print("Iniciando o deploy em Produção - PROD01...")
       
        print("⚠️ STDERR:")
        print(stderr.read().decode())

        ssh.close()
        print("✅ Deploy em Produção - PROD01 concluído.")

        key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=SSH_HOST_PROD02, 
            port=SSH_PORT,
            username=SSH_USER,
            pkey=key            
        )

        command = f"bash {SCRIPT_PATH_PROD} {ENVIRONMENT} {BRANCH}"
        print(f"🚀 Executando comando: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)

        print("Iniciando o deploy em Produção - PROD02...")
       
        print("⚠️ STDERR:")
        print(stderr.read().decode())

        ssh.close()
        print("✅ Deploy em Produção - PROD02 concluído.")

    except Exception as e:
        print(f"❌ Ocorreu um erro: {e}")

def deploy_whitelabel():
    ENVIRONMENT = "whitelabel"
    BRANCH = "main"

    try:
        print("🔐 Iniciando conexão SSH...")
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=SSH_HOST_WHITELABEL, 
            port=SSH_PORT,
            username=SSH_USER,
            pkey=key            
        )

        command = f"bash {SCRIPT_PATH_wHITELABEL} {ENVIRONMENT} {BRANCH}"
        print(f"🚀 Executando comando: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)

        print("Iniciando o deploy em Whitelabel...")
       
        print("⚠️ STDERR:")
        print(stderr.read().decode())

        ssh.close()
        print("✅ Deploy em Whitelabal concluído.")

    except Exception as e:
        print(f"❌ Ocorreu um erro: {e}")

def deploy_stage ()
    ENVIRONMENT = "stage"
    BRANCH = "develop"

    try:
        print("🔐 Iniciando conexão SSH...")
        key = paramiko.RSAKey.from_private_key_file(SSH_KEY_PATH)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=SSH_HOST_STAGE, 
            port=SSH_PORT,
            username=SSH_USER,
            pkey=key            
        )

        command = f"bash {SCRIPT_PATH_STAGE} {ENVIRONMENT} {BRANCH}"
        print(f"🚀 Executando comando: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)

        print("Iniciando o deploy em Stage...")
       
        print("⚠️ STDERR:")
        print(stderr.read().decode())

        ssh.close()
        print("✅ Deploy em Stage concluído.")

    except Exception as e:
        print(f"❌ Ocorreu um erro: {e}")
