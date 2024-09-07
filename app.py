"""
Todo:
- update commands
- authentication
"""

from flask import Flask, Response, request
from subprocess import Popen
from os import chdir

app = Flask(__name__)

SERVERS = {
	"tailsbot": {
		"command": ["python", "./bot.py"],
		"update": ["git", "pull"],
	}
}

class Runner:
	def __init__(self):
		self.procs = {}
	
	def start(self, name, args, dir=None):
		if (name not in self.procs) or not self.is_running(name):
			try:
				chdir(dir or name)
			except:
				print(f"{name} has no dir")
				return None
			
			proc = Popen(args)
			
			chdir("..")
			
			self.procs[name] = proc
			return proc.pid
		else:
			return None
	
	def stop(self, name):
		if name in self.procs:
			self.procs[name].terminate()
			self.procs[name].wait()
			del self.procs[name]
	
	def has_server(self, name):
		return name in self.procs
	
	def is_running(self, name):
		return (name in self.procs) and (self.procs[name].poll() == None)
	
	def wait_for_ret(self, name):
		if name in self.procs:
			self.procs[name].wait()
			x = self.procs[name].returncode
			del self.procs[name]
			return x
		else:
			return None

runner = Runner()

def fail(msg):
	return {"success": False, "error_msg": msg}

def start_server(server):
	if server in SERVERS:
		serv_info = SERVERS[server]
		
		if "command" in serv_info:
			pid = runner.start(server, serv_info['command'])
			
			if pid != None:
				return {"success": True, "pid": pid}
			else:
				return fail("Failed to start process; already running or no dir?")
		else:
			return fail("Server JSON error: no command")
	else:
		return fail("Server does not exist")

@app.put("/v1/start/<server>")
def v1_start(server):
	return start_server(server)

def stop_server(server):
	if server not in SERVERS:
		return fail("Server doesn't exist")
	
	runner.stop(server)
	
	return {"success": True}

@app.put("/v1/stop/<server>")
def v1_stop(server):
	return stop_server(server)

@app.put("/v1/restart/<server>")
def v1_restart(server):
	status = stop_server(server)
	
	if not status["success"]:
		return status
	
	return start_server(server)

@app.get("/v1/running/<server>")
def v1_running(server):
	if server not in SERVERS:
		return fail("No such server")
	
	return {"success": True, "running": runner.is_running(server)}

@app.route("/")
def index():
	return """<html>
	<head>
		<title>Some title</title>
	</head>
	<body>
		<h1>Server runner API</h1>
		<h2>PUT /v1/start/[server name]</h2>
		<h2>PUT /v1/stop/[server name]</h2>
		<h2>PUT /v1/restart/[server name]</h2>
		<h2>GET /v1/running/[server name]</h2>
	</body>
</html>"""

if __name__ == "__main__":
	app.run()
