#!/usr/bin/env python3
"""
SkillDispatcher - Core Skill Execution
=======================================

Executes skills and manages skill processes.
Supports multiple execution methods (index.js, index.py, process_needs_action.py, run.sh).
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional


class SkillDispatcher:
    """Dispatches and executes skills"""

    def __init__(self, skills_dir: Path, logger: logging.Logger):
        self.skills_dir = skills_dir
        self.logger = logger

    def execute_skill(self, skill_name: str, args: List[str] = None) -> Dict:
        """Execute a skill by name"""
        skill_path = self.skills_dir / skill_name

        if not skill_path.exists():
            return {
                'success': False,
                'returncode': 1,
                'stdout': '',
                'stderr': f"Skill not found: {skill_name}"
            }

        # Determine execution method
        if (skill_path / "index.js").exists():
            return self._execute_node_skill(skill_path / "index.js", args)
        elif (skill_path / "index.py").exists():
            return self._execute_python_skill(skill_path / "index.py", args)
        elif (skill_path / "process_needs_action.py").exists():
            return self._execute_python_skill(skill_path / "process_needs_action.py", args)
        elif (skill_path / "run.sh").exists():
            return self._execute_shell_skill(skill_path / "run.sh", args)
        else:
            return {
                'success': False,
                'returncode': 1,
                'stdout': '',
                'stderr': f"No executable found for skill: {skill_name}"
            }

    def _execute_node_skill(self, script_path: Path, args: List[str] = None) -> Dict:
        """Execute Node.js skill"""
        try:
            cmd = ["node", str(script_path)]
            if args:
                cmd.extend(args)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=script_path.parent
            )

            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Skill execution timed out (300s)'
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }

    def _execute_python_skill(self, script_path: Path, args: List[str] = None) -> Dict:
        """Execute Python skill"""
        try:
            cmd = ["python3", str(script_path)]
            if args:
                cmd.extend(args)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=script_path.parent
            )

            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Skill execution timed out (300s)'
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }

    def _execute_shell_skill(self, script_path: Path, args: List[str] = None) -> Dict:
        """Execute shell skill"""
        try:
            cmd = ["bash", str(script_path)]
            if args:
                cmd.extend(args)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=script_path.parent
            )

            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Skill execution timed out (300s)'
            }
        except Exception as e:
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
