#!/usr/bin/env python3
import argparse
import subprocess
import json
import sys
import os

def run_cmd(cmd):
    """Executes a system command via subprocess and returns the output or exits on failure."""
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando comando: {' '.join(cmd)}", file=sys.stderr)
        if e.stderr:
            print(e.stderr.strip(), file=sys.stderr)
        sys.exit(1)

def cmd_deploy(args):
    template_path = os.path.join("templates", f"{args.template}.json")
    if not os.path.exists(template_path):
        print(f"❌ Error: La plantilla '{template_path}' no existe.", file=sys.stderr)
        sys.exit(1)
        
    with open(template_path, 'r') as f:
        config = json.load(f)
        
    docker_cmd = ["docker", "run", "-d", "--name", args.name]
    
    # Agregar variables de entorno
    for k, v in config.get("environment", {}).items():
        docker_cmd.extend(["-e", f"{k}={v}"])
        
    # Agregar puertos
    for k, v in config.get("ports", {}).items():
        docker_cmd.extend(["-p", f"{k}:{v}"])
        
    # Agregar volúmenes (usaremos el formato nombre_contenedor_volumen para aislar)
    for internal_path, vol_suffix in config.get("volumes", {}).items():
        volume_name = f"{args.name}_{vol_suffix}"
        docker_cmd.extend(["-v", f"{volume_name}:{internal_path}"])
        
    docker_cmd.append(config.get("image"))
    
    print(f"🚀 Desplegando servidor '{args.name}' usando plantilla '{args.template}'...")
    output = run_cmd(docker_cmd)
    print(f"✅ Servidor desplegado exitosamente. ID del Contenedor: {output[:12]}")

def cmd_start(args):
    print(f"▶️ Iniciando servidor '{args.name}'...")
    run_cmd(["docker", "start", args.name])
    print(f"✅ Servidor '{args.name}' iniciado.")

def cmd_stop(args):
    print(f"⏹️ Deteniendo servidor '{args.name}'...")
    run_cmd(["docker", "stop", args.name])
    print(f"✅ Servidor '{args.name}' detenido.")

def cmd_pause(args):
    print(f"⏸️ Pausando servidor '{args.name}'...")
    run_cmd(["docker", "pause", args.name])
    print(f"✅ Servidor '{args.name}' en pausa.")

def cmd_unpause(args):
    print(f"⏯️ Reanudando servidor '{args.name}'...")
    run_cmd(["docker", "unpause", args.name])
    print(f"✅ Servidor '{args.name}' reanudado.")

def cmd_destroy(args):
    print(f"🗑️ Destruyendo servidor '{args.name}'...")
    run_cmd(["docker", "rm", "-f", args.name])
    print(f"✅ Servidor '{args.name}' destruido. (Nota: los volúmenes de datos se mantienen intactos)")

def cmd_stats(args):
    print(f"📊 Obteniendo telemetría para '{args.name}'...\n")
    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "CPU: {{.CPUPerc}} | RAM: {{.MemUsage}} ({{.MemPerc}})", args.name],
            check=True, text=True, capture_output=True
        )
        print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"❌ Error obteniendo telemetría. ¿El contenedor está corriendo?", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Orquestador Ligero para Servidores Dedicados")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # deploy
    parser_deploy = subparsers.add_parser("deploy", help="Despliega un nuevo servidor desde una plantilla")
    parser_deploy.add_argument("name", help="Nombre único para la instancia del servidor")
    parser_deploy.add_argument("-t", "--template", required=True, help="Nombre de la plantilla en la carpeta templates/ (ej. minecraft)")
    
    # start
    parser_start = subparsers.add_parser("start", help="Inicia un servidor detenido")
    parser_start.add_argument("name", help="Nombre del servidor")
    
    # stop
    parser_stop = subparsers.add_parser("stop", help="Detiene un servidor en ejecución")
    parser_stop.add_argument("name", help="Nombre del servidor")
    
    # pause
    parser_pause = subparsers.add_parser("pause", help="Pausa un servidor (congela procesos para ahorrar CPU)")
    parser_pause.add_argument("name", help="Nombre del servidor")
    
    # unpause
    parser_unpause = subparsers.add_parser("unpause", help="Reanuda un servidor pausado")
    parser_unpause.add_argument("name", help="Nombre del servidor")
    
    # destroy
    parser_destroy = subparsers.add_parser("destroy", help="Elimina el contenedor del servidor")
    parser_destroy.add_argument("name", help="Nombre del servidor")
    
    # stats
    parser_stats = subparsers.add_parser("stats", help="Muestra el uso de CPU/RAM del servidor")
    parser_stats.add_argument("name", help="Nombre del servidor")
    
    args = parser.parse_args()
    
    globals()[f"cmd_{args.command}"](args)

if __name__ == "__main__":
    main()
