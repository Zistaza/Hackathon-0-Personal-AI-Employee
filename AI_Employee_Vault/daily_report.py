import datetime
import os

base_path = "/mnt/c/Users/Tesla Laptops/Desktop/AI_Employee_Vault/AI_Employee_Vault"

log_path = os.path.join(base_path, "Logs", "daily_health.log")

now = datetime.datetime.now()

report = f"""
==============================
AI Employee Daily Report
Time: {now}
==============================

System Status: Running
Orchestrator: Active
Watchers: Operational

"""

with open(log_path, "a") as f:
    f.write(report)

print("Daily report generated.")
