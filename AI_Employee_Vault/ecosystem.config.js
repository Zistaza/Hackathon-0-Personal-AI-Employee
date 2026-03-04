module.exports = {
  apps: [
    {
      name: 'orchestrator',
      script: 'Skills/integration_orchestrator/index.py',
      interpreter: 'venv/bin/python3',
      cwd: '/mnt/c/Users/Tesla Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: 'logs/orchestrator-error.log',
      out_file: 'logs/orchestrator-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'watchers',
      script: 'Automation/watchers/run_all_watchers.py',
      interpreter: 'venv/bin/python3',
      cwd: '/mnt/c/Users/Tesla Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault',
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: 'logs/watchers-error.log',
      out_file: 'logs/watchers-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};
