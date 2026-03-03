#!/usr/bin/env python3
"""Quick script to check autonomous executor metrics"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Skills.integration_orchestrator.index import IntegrationOrchestrator

def main():
    """Check metrics from running orchestrator"""
    base_dir = Path(__file__).parent.parent.parent

    print("Initializing orchestrator...")
    orchestrator = IntegrationOrchestrator(base_dir)

    print("\n" + "=" * 60)
    print("AUTONOMOUS EXECUTOR METRICS")
    print("=" * 60)

    metrics = orchestrator.autonomous_executor.get_autonomous_metrics()

    print(f"Success Rate:          {metrics['success_rate']}%")
    print(f"Successful Triggers:   {metrics['auto_trigger_success']}")
    print(f"Failed Triggers:       {metrics['auto_trigger_failures']}")
    print(f"Escalations:           {metrics['escalations']}")
    print(f"Workflows Recovered:   {metrics['workflows_recovered']}")

    total = metrics['auto_trigger_success'] + metrics['auto_trigger_failures']
    print(f"\nTotal Triggers:        {total}")
    print("=" * 60)

if __name__ == "__main__":
    main()
