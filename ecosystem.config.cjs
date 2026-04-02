module.exports = {
  apps: [
    {
      name: "quantum-api",
      cwd: "/home/deployer/quantum-api",
      script: ".venv/bin/python",
      args: "-m uvicorn quantum_api.main:app --host 127.0.0.1 --port 8000",
      interpreter: "none",
      env: {
        PYTHONPATH: "/home/deployer/quantum-api/src",
      },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 3000,
    },
  ],
};
