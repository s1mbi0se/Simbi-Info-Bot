import os

import paramiko

from config import Config

def deploy_production():
    ENVIRONMENT = "production"
    BRANCH = "main"

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

        command = f"bash {Config.SCRIPT_PATH_PROD} {ENVIRONMENT} {BRANCH}"
        print(f"🚀 Executando comando em {label}: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)

        print(f"Iniciando o deploy em {label}...")

        stdout_msg = stdout.read().decode().strip()
        stderr_msg = stderr.read().decode().strip()
        exit_code = stdout.channel.recv_exit_status()
        
        print("📄 STDOUT:")
        print(stdout_msg)
        
        print("⚠️ STDERR:")
        print(stderr_msg)

        ssh.close()
        print(f"✅ Deploy em {label} concluído.")
        
        return {
            "label": label,
            "stdout": stdout_msg,
            "stderr": stderr_msg,
            "exit_code": exit_code
        }

    try:
        log1 = execute_on_host(Config.SSH_HOST_PROD01, "Produção - PROD01")
        log2 = execute_on_host(Config.SSH_HOST_PROD02, "Produção - PROD02")

        final_log = (
            f"=== DEPLOY PRODUÇÃO ===\n"
            f"BRANCH: {BRANCH}\n\n"
            f"--- {log1['label']} ---\n"
            f"📄 STDOUT:\n{log1['stdout'] or '(vazio)'}\n\n"
            f"⚠️ STDERR:\n{log1['stderr'] or '(vazio)'}\n\n"
            f"Exit Code: {log1['exit_code']}\n\n"
            
            f"--- {log2['label']} ---\n"
            f"📄 STDOUT:\n{log2['stdout'] or '(vazio)'}\n\n"
            f"⚠️ STDERR:\n{log2['stderr'] or '(vazio)'}\n"
            f"Exit Code: {log2['exit_code']}\n\n"
        )
        
        if log1["exit_code"] != 0 or log2["exit_code"] != 0:
            return f"❌ Erro durante o deploy!\n\n{final_log}"

        return f"✅ Deploy em Produção concluído com sucesso!\n\n{final_log}"
        
    except Exception as e:
        return f"❌ Ocorreu um erro: {e}"


def deploy_whitelabel():
    ENVIRONMENT = "whitelabel"
    BRANCH = "main"

    try:
        print("🔐 Iniciando conexão SSH...")
        key = paramiko.RSAKey.from_private_key_file(Config.SSH_KEY_PATH)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=Config.SSH_HOST_WHITELABEL,
            port=Config.SSH_PORT,
            username=Config.SSH_USER,
            pkey=key,
        )

        command = f"bash {Config.SCRIPT_PATH_WHITELABEL} {ENVIRONMENT} {BRANCH}"
        print(f"🚀 Executando comando: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)

        print("Iniciando o deploy em Whitelabel...")

        stdout_msg = stdout.read().decode().strip()
        stderr_msg = stderr.read().decode().strip()
        exit_code = stdout.channel.recv_exit_status()
        
        print("📄 STDOUT:")
        print(stdout_msg)
        
        print("⚠️ STDERR:")
        print(stderr_msg)

        ssh.close()
        print("✅ Deploy em Whitelabal concluído.")
        
        if exit_code != 0:
            return f"❌ Erro durante o deploy em Whitelabel:\n{stderr_msg}"
        
        return f"✅ Deploy em Whitelabel concluído.\n{stdout_msg}"

    except Exception as e:
        return f"❌ Ocorreu um erro: {e}"


def deploy_stage(branch):
    ENVIRONMENT = "stage"
    BRANCH = branch

    try:
        print("🔐 Iniciando conexão SSH...")
        key = paramiko.RSAKey.from_private_key_file(Config.SSH_KEY_PATH)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=Config.SSH_HOST_STAGE,
            port=Config.SSH_PORT,
            username=Config.SSH_USER,
            pkey=key,
        )

        command = f"bash {Config.SCRIPT_PATH_STAGE} {ENVIRONMENT} {BRANCH}"
        print(f"🚀 Executando comando: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)
        
        print("Iniciando o deploy em Stage...")
        
        stdout_msg = stdout.read().decode().strip()
        stderr_msg = stderr.read().decode().strip()
        exit_code = stdout.channel.recv_exit_status()
        
        print("📄 STDOUT:")
        print(stdout_msg)
        
        print("⚠️ STDERR:")
        print(stderr_msg)

        ssh.close()
        print("🔌 Conexão encerrada.")

        if exit_code != 0:
            return f"❌ Erro durante o deploy em Stage:\n{stderr_msg}"

        return f"✅ Deploy em Stage concluído.\n{stdout_msg}"

    except Exception as e:
        return f"❌ Ocorreu um erro: {e}"
    

def restart_production(option):
    ENVIRONMENT = "production"

    servers = {
        "1": (Config.SSH_HOST_PROD01, "Produção - PROD01"),
        "2": (Config.SSH_HOST_PROD02, "Produção - PROD02"),
    }

    if option not in ("1", "2", "3"):
        return "❌ Opção inválida. Escolha 1, 2 ou 3."

    if option == "3":
        selected_servers = [
            servers["1"],
            servers["2"],
        ]
    else:
        selected_servers = [servers[option]]

    try:
        key = paramiko.RSAKey.from_private_key_file(
            Config.SSH_KEY_PATH
        )

        results = []

        def execute_on_host(hostname, label):
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )

            try:
                print(f"🔐 Conectando em {label}...")

                ssh.connect(
                    hostname=hostname,
                    port=Config.SSH_PORT,
                    username=Config.SSH_USER,
                    pkey=key,
                    timeout=15,
                    banner_timeout=15,
                    auth_timeout=15,
                )

                command = (
                    f"bash {Config.RESTART_PATH_PROD} "
                    f"{ENVIRONMENT}"
                )

                print(
                    f"🚀 Executando em {label}: {command}"
                )

                stdin, stdout, stderr = ssh.exec_command(
                    command,
                    timeout=120
                )

                stdout_msg = stdout.read().decode().strip()
                stderr_msg = stderr.read().decode().strip()
                exit_code = stdout.channel.recv_exit_status()

                return {
                    "label": label,
                    "stdout": stdout_msg,
                    "stderr": stderr_msg,
                    "exit_code": exit_code,
                }

            finally:
                ssh.close()

        for hostname, label in selected_servers:
            try:
                result = execute_on_host(hostname, label)
                results.append(result)

            except Exception as e:
                results.append({
                    "label": label,
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                })

        final_log = []

        for result in results:
            final_log.append(
                f"--- {result['label']} ---\n"
                f"📄 STDOUT:\n"
                f"{result['stdout'] or '(vazio)'}\n\n"
                f"⚠️ STDERR:\n"
                f"{result['stderr'] or '(vazio)'}\n\n"
                f"Exit Code: {result['exit_code']}"
            )

        report = "\n\n".join(final_log)

        failed = any(
            result["exit_code"] != 0
            for result in results
        )

        if failed:
            return (
                "❌ Erro durante o restart da produção!\n\n"
                f"{report}"
            )

        server_names = ", ".join(
            result["label"] for result in results
        )

        return (
            f"✅ Restart concluído com sucesso!\n"
            f"Servidores: {server_names}\n\n"
            f"{report}"
        )

    except Exception as e:
        return f"❌ Erro ao preparar o restart: {e}"


def restart_stage():
    ENVIRONMENT = "stage"
    
    try:
        print("🔐 Iniciando conexão SSH...")
        key = paramiko.RSAKey.from_private_key_file(Config.SSH_KEY_PATH)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=Config.SSH_HOST_STAGE,
            port=Config.SSH_PORT,
            username=Config.SSH_USER,
            pkey=key,
        )

        command = f"bash {Config.RESTART_PATH_STAGE} {ENVIRONMENT}"
        print(f"🚀 Executando comando: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)
        
        print("Reiniciando o servidor em Stage...")
        
        stdout_msg = stdout.read().decode().strip()
        stderr_msg = stderr.read().decode().strip()
        exit_code = stdout.channel.recv_exit_status()
        
        print("📄 STDOUT:")
        print(stdout_msg)
        
        print("⚠️ STDERR:")
        print(stderr_msg)

        ssh.close()
        print("🔌 Conexão encerrada.")

        if exit_code != 0:
            return f"❌ Erro durante o restart do servidor em Stage:\n{stderr_msg}"

        return f"✅ Restart em Stage concluído."

    except Exception as e:
        return f"❌ Ocorreu um erro: {e}"
