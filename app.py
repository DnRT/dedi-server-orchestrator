from flask import Flask, request, jsonify
import core
import os

app = Flask(__name__, static_url_path='', static_folder='static')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/servers', methods=['GET'])
def get_servers():
    try:
        servers = core.list_servers()
        # Solo pedir stats para los que están corriendo, ahorrando mucho tiempo
        active_names = [s.get("Names") for s in servers if s.get("State") == "running"]
        stats = core.get_stats(active_names) if active_names else {}
        
        # Mezclar stats en los servidores
        for s in servers:
            name = s.get("Names")
            if name in stats:
                s["Stats"] = stats[name]
            else:
                s["Stats"] = None
                
        return jsonify({"status": "success", "data": servers})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/templates', methods=['GET'])
def get_templates():
    return jsonify({"status": "success", "data": core.get_templates()})

@app.route('/api/deploy', methods=['POST'])
def deploy():
    data = request.json
    name = data.get("name")
    template = data.get("template")
    if not name or not template:
         return jsonify({"status": "error", "message": "Nombre y plantilla son requeridos."}), 400
    try:
         result = core.deploy_server(name, template)
         return jsonify(result)
    except core.OrchestratorError as e:
         return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/action', methods=['POST'])
def action():
    data = request.json
    name = data.get("name")
    action_type = data.get("action")
    try:
        if action_type == "start":
            core.start_server(name)
        elif action_type == "stop":
            core.stop_server(name)
        elif action_type == "pause":
            core.pause_server(name)
        elif action_type == "unpause":
            core.unpause_server(name)
        elif action_type == "destroy":
            core.destroy_server(name)
        else:
            return jsonify({"status": "error", "message": "Acción inválida"}), 400
            
        return jsonify({"status": "success"})
    except core.OrchestratorError as e:
         return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/logs/<name>', methods=['GET'])
def get_logs(name):
    try:
        logs_output = core.get_logs(name)
        return jsonify({"status": "success", "data": logs_output})
    except core.OrchestratorError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    print("Iniciando el Servidor Web del Orquestador Ligero...")
    app.run(host='0.0.0.0', port=5000, debug=True)
