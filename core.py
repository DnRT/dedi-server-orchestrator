import subprocess
import json
import os

class OrchestratorError(Exception):
    pass

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
        raise OrchestratorError(error_msg or "Error desconocido ejecutando comando")

def get_allowed_images():
    images = set()
    if os.path.exists("templates"):
        for f in os.listdir("templates"):
            if f.endswith(".json"):
                try:
                    with open(os.path.join("templates", f), 'r') as fp:
                        config = json.load(fp)
                        if "image" in config:
                            images.add(config["image"])
                except:
                    pass
    return images

def deploy_server(name, template_name):
    template_path = os.path.join("templates", f"{template_name}.json")
    if not os.path.exists(template_path):
        raise OrchestratorError(f"La plantilla '{template_path}' no existe.")
        
    with open(template_path, 'r') as f:
        config = json.load(f)
        
    docker_cmd = ["docker", "run", "-d", "--name", name]
    
    for k, v in config.get("environment", {}).items():
        docker_cmd.extend(["-e", f"{k}={v}"])
    for k, v in config.get("ports", {}).items():
        docker_cmd.extend(["-p", f"{k}:{v}"])
    for internal_path, vol_suffix in config.get("volumes", {}).items():
        volume_name = f"{name}_{vol_suffix}"
        docker_cmd.extend(["-v", f"{volume_name}:{internal_path}"])
        
    docker_cmd.append(config.get("image"))
    
    output = run_cmd(docker_cmd)
    return {"status": "success", "container_id": output[:12]}

def list_servers():
    try:
        allowed_images = get_allowed_images()
        output = run_cmd(["docker", "ps", "-a", "--format", "{{json .}}"])
        servers = []
        if output:
            for line in output.split('\n'):
                if line.strip():
                    data = json.loads(line)
                    # Filtramos por las imágenes definidas en las plantillas (ignorando los tags extra si los hay)
                    image = data.get("Image", "")
                    if any(image.startswith(allowed) for allowed in allowed_images):
                        servers.append(data)
        return servers
    except OrchestratorError:
        return []

def get_stats(server_names=None):
    if server_names is not None and len(server_names) == 0:
        return {}
    try:
        cmd = ["docker", "stats", "--no-stream", "--format", '{{json .}}']
        if server_names:
            cmd.extend(server_names)
        output = run_cmd(cmd)
        stats = {}
        if output:
            for line in output.split('\n'):
                if line.strip():
                    data = json.loads(line)
                    stats[data['Name']] = data
        return stats
    except OrchestratorError:
        return {}

def start_server(name):
    run_cmd(["docker", "start", name])

def stop_server(name):
    run_cmd(["docker", "stop", name])

def pause_server(name):
    run_cmd(["docker", "pause", name])

def unpause_server(name):
    run_cmd(["docker", "unpause", name])

def destroy_server(name):
    run_cmd(["docker", "rm", "-f", name])

def get_templates():
    templates = []
    if os.path.exists("templates"):
        for f in os.listdir("templates"):
            if f.endswith(".json"):
                templates.append(f.replace(".json", ""))
    return templates

def get_logs(name):
    try:
        # Obtenemos las últimas 100 líneas del contenedor (stdout y stderr combinados) y -t para timestamps
        result = subprocess.run(["docker", "logs", "--tail", "100", "-t", name], check=True, text=True, capture_output=True)
        return result.stdout + result.stderr
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
        raise OrchestratorError(error_msg or "Error obteniendo logs")
