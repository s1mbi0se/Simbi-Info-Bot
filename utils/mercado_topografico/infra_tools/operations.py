import os

import paramiko

import shlex

from config import Config

def remove_keys(password):
    PASSWORD = password

    key = paramiko.RSAKey.from_private_key_file(Config.SSH_KEY_PATH)

    def execute_on_host(hostname, label):
        print(f"🔐 Iniciando conexão SSH em {label}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=hostname,
            port=Config.SSH_PORT,
            username=Config.SSH_USER,
            pkey=key,
        )

        script_path = shlex.quote(Config.REMOVE_KEYS_PATH)
        password = shlex.quote(PASSWORD)

        command = (
            f"source ~/.bashrc && "
            f"bash {script_path} {password}"
        )
        
        print(f"🚀 Executando comando em {label}: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)

        print(f"Iniciando a remoção das chaves em {label}...")

        stdout_msg = stdout.read().decode().strip()
        stderr_msg = stderr.read().decode().strip()
        exit_code = stdout.channel.recv_exit_status()
        
        print("📄 STDOUT:")
        print(stdout_msg)
        
        print("⚠️ STDERR:")
        print(stderr_msg)

        ssh.close()
        print(f"✅ Remoção das chaves em {label} concluída.")
        
        return {
            "label": label,
            "stdout": stdout_msg,
            "stderr": stderr_msg,
            "exit_code": exit_code
        }

    try:
        log1 = execute_on_host(Config.SSH_HOST_PROD01, "Produção - PROD01")
        log2 = execute_on_host(Config.SSH_HOST_PROD02, "Produção - PROD02")
        log3 = execute_on_host(Config.SSH_HOST_STAGE, "Stage")
        log4 = execute_on_host(Config.SSH_HOST_WHITELABEL, "Whitelabel")
        log5 = execute_on_host(Config.SSH_HOST_DATABASE, "Database")

        final_log = (
            f"=== REMOVER CHAVES ===\n"
            f"BRANCH: {BRANCH}\n\n"
            f"--- {log1['label']} ---\n"
            f"📄 STDOUT:\n{log1['stdout'] or '(vazio)'}\n\n"
            f"⚠️ STDERR:\n{log1['stderr'] or '(vazio)'}\n\n"
            f"Exit Code: {log1['exit_code']}\n\n"
            
            f"--- {log2['label']} ---\n"
            f"📄 STDOUT:\n{log2['stdout'] or '(vazio)'}\n\n"
            f"⚠️ STDERR:\n{log2['stderr'] or '(vazio)'}\n"
            f"Exit Code: {log2['exit_code']}\n\n"
            
            f"--- {log3['label']} ---\n"
            f"📄 STDOUT:\n{log3['stdout'] or '(vazio)'}\n\n"
            f"⚠️ STDERR:\n{log3['stderr'] or '(vazio)'}\n"
            f"Exit Code: {log3['exit_code']}\n\n"

            f"--- {log4['label']} ---\n"
            f"📄 STDOUT:\n{log4['stdout'] or '(vazio)'}\n\n"
            f"⚠️ STDERR:\n{log4['stderr'] or '(vazio)'}\n"
            f"Exit Code: {log4['exit_code']}\n\n"

            f"--- {log5['label']} ---\n"
            f"📄 STDOUT:\n{log5['stdout'] or '(vazio)'}\n\n"
            f"⚠️ STDERR:\n{log5['stderr'] or '(vazio)'}\n"
            f"Exit Code: {log5['exit_code']}\n\n"
        )
        
        if log1["exit_code"] != 0 or log2["exit_code"] != 0 or log3["exit_code"] != 0 or log4["exit_code"] != 0 or log5["exit_code"] != 0:
            return f"❌ Erro durante a remoção das chaves!\n\n{final_log}"

        return f"✅ Remoção das chaves concluída com sucesso!"
        
    except Exception as e:
        return f"❌ Ocorreu um erro: {e}"