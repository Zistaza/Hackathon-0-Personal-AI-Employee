#!/usr/bin/env python3
"""
Process Needs Action Skill - Enhanced v2.0
Processes files in /Needs_Action with comprehensive planning, risk analysis, and approval workflow
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ProcessNeedsActionSkill:
    def __init__(self, base_dir: str = "../.."):
        self.base_dir = Path(base_dir)
        self.needs_action_dir = self.base_dir / "Needs_Action"
        self.plans_dir = self.base_dir / "Plans"
        self.pending_approval_dir = self.base_dir / "Pending_Approval"
        self.done_dir = self.base_dir / "Done"
        self.logs_dir = self.base_dir / "Logs"

        # Ensure directories exist
        for directory in [self.plans_dir, self.pending_approval_dir, self.done_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        """Log message to console and file"""
        timestamp = datetime.utcnow().isoformat() + "Z"
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)

        # Append to daily log file
        log_file = self.logs_dir / "process_needs_action.log"
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")

    def read_file_content(self, filepath: Path) -> Optional[str]:
        """Read file content safely"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.log(f"Error reading file {filepath.name}: {str(e)}")
            return None

    def parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Parse YAML frontmatter from markdown content"""
        metadata = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                body = parts[2].strip()

                # Simple YAML parsing
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()

        return metadata, body

    def analyze_content(self, content: str, metadata: Dict) -> Dict:
        """Analyze file content and determine priority, complexity, risks"""
        analysis = {
            "priority": "medium",
            "complexity": "moderate",
            "approval_required": False,
            "risk_level": "Medium",
            "risks": [],
            "steps": [],
            "objective": ""
        }

        # Determine priority based on keywords
        content_lower = content.lower()
        if any(word in content_lower for word in ["urgent", "critical", "asap", "immediately"]):
            analysis["priority"] = "high"
        elif any(word in content_lower for word in ["invoice", "payment", "proposal"]):
            analysis["priority"] = "high"

        # Determine if approval required
        if any(word in content_lower for word in ["payment", "invoice", "contract", "proposal"]):
            analysis["approval_required"] = True
            analysis["risk_level"] = "Medium"

        # Generate objective
        source_type = metadata.get("type", "unknown")
        sender = metadata.get("sender", "Unknown")

        if source_type == "whatsapp":
            analysis["objective"] = f"Process WhatsApp message from {sender}. {content[:100]}..."
        elif source_type == "gmail":
            analysis["objective"] = f"Process email from {sender}. {content[:100]}..."
        else:
            analysis["objective"] = f"Process request: {content[:100]}..."

        # Identify risks
        analysis["risks"] = [
            {
                "category": "Technical",
                "risk": "Data validation failure",
                "likelihood": "Low",
                "mitigation": "Implement input validation and error handling"
            },
            {
                "category": "Business",
                "risk": "Misinterpretation of requirements",
                "likelihood": "Medium",
                "mitigation": "Confirm understanding with stakeholder before execution"
            },
            {
                "category": "Operational",
                "risk": "Resource availability constraints",
                "likelihood": "Low",
                "mitigation": "Verify resource availability before starting"
            }
        ]

        # Generate steps
        analysis["steps"] = [
            "Review and validate the request details",
            "Identify required resources and dependencies",
            "Execute the primary action items",
            "Verify completion against success criteria",
            "Document results and notify stakeholders"
        ]

        return analysis

    def create_plan(self, filename: str, content: str, metadata: Dict, analysis: Dict) -> Optional[str]:
        """Create enhanced plan file"""
        plan_filename = f"PLAN_{filename}"
        plan_path = self.plans_dir / plan_filename

        # Check if plan already exists
        if plan_path.exists():
            self.log(f"Plan already exists: {plan_filename}")
            return None

        timestamp = datetime.utcnow().isoformat() + "Z"

        # Build plan content
        plan_content = f"""---
created: {timestamp}
status: pending_review
source_file: {filename}
priority: {analysis['priority']}
estimated_complexity: {analysis['complexity']}
---

## Objective

{analysis['objective']}

## Step-by-Step Checklist

"""

        # Add steps
        for i, step in enumerate(analysis['steps'], 1):
            plan_content += f"- [ ] Step {i}: {step}\n"

        plan_content += """
**Success Criteria**:
- All action items completed successfully
- Stakeholder requirements met
- Documentation updated and archived

## Risk Analysis

### Identified Risks

"""

        # Add risks
        for risk in analysis['risks']:
            plan_content += f"""**{risk['category']} Risks**:
- {risk['risk']}: {risk['likelihood']} likelihood - {risk['mitigation']}

"""

        plan_content += f"""### Mitigation Strategies

1. **For Technical Risks**: Implement validation and error handling at each step
2. **For Business Risks**: Confirm requirements and maintain clear communication
3. **For Operational Risks**: Verify resource availability and prepare contingencies
4. **Contingency Plan**: If primary approach fails, escalate to manual review and alternative execution path

### Risk Level Assessment

**Overall Risk**: {analysis['risk_level']}

**Justification**: Based on content analysis and identified risk factors, this task requires standard oversight and follows established procedures.

## Approval Required

**Approval Status**: {"Required" if analysis['approval_required'] else "Not Required"}

**Reason**: {"Financial or sensitive operation requiring management approval" if analysis['approval_required'] else "Standard operational task within normal workflow"}

"""

        if analysis['approval_required']:
            plan_content += """**If Approval Required**:

**Approver**: Department Manager or Designated Approver

**Approval Criteria**:
- [ ] Budget allocation confirmed (if applicable)
- [ ] Technical approach validated
- [ ] Timeline is acceptable
- [ ] Risk mitigation plan is adequate
- [ ] Resource availability confirmed

**Estimated Impact**:
- **Time**: 2-4 hours for complete processing
- **Resources**: Team member availability, system access
- **Cost**: Standard operational costs
- **Dependencies**: Approver availability, system access

**Approval Deadline**: Within 24 hours of plan creation

**If Not Approved**: Escalate to senior management or defer to next review cycle

"""

        plan_content += """## Implementation Notes

**Key Considerations**:
- Follow established procedures and guidelines
- Maintain clear documentation throughout process
- Communicate progress to relevant stakeholders

**Dependencies**:
- System access and availability
- Stakeholder availability for clarifications
- Required tools and resources

**Assumptions**:
- Request details are accurate and complete
- Standard procedures apply unless otherwise specified
- Resources are available within normal timeframes

**Recommendations**:
- Begin execution promptly upon approval
- Monitor progress against success criteria
- Document any deviations or issues encountered
"""

        try:
            with open(plan_path, "w", encoding="utf-8") as f:
                f.write(plan_content)
            self.log(f"Plan created: {plan_filename}")
            return plan_filename
        except Exception as e:
            self.log(f"Error creating plan {plan_filename}: {str(e)}")
            return None

    def copy_to_pending_approval(self, plan_filename: str) -> bool:
        """Copy plan to Pending_Approval directory"""
        try:
            source = self.plans_dir / plan_filename
            destination = self.pending_approval_dir / plan_filename
            shutil.copy2(source, destination)
            self.log(f"Plan copied to Pending_Approval: {plan_filename}")
            return True
        except Exception as e:
            self.log(f"Error copying plan to Pending_Approval: {str(e)}")
            return False

    def create_log_entry(self, filename: str, plan_filename: str, analysis: Dict) -> bool:
        """Create JSON log entry"""
        try:
            log_date = datetime.utcnow().strftime("%Y-%m-%d")
            log_file = self.logs_dir / f"{log_date}.json"

            # Read existing log or create new
            if log_file.exists():
                with open(log_file, "r") as f:
                    log_data = json.load(f)
            else:
                log_data = []

            # Create new entry
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "action_type": "plan_created",
                "source_file": filename,
                "plan_file": plan_filename,
                "result": "success",
                "plan_metadata": {
                    "priority": analysis['priority'],
                    "complexity": analysis['complexity'],
                    "approval_required": analysis['approval_required'],
                    "risk_level": analysis['risk_level'],
                    "objective_summary": analysis['objective'][:100]
                },
                "details": {
                    "source_folder": "/Needs_Action",
                    "plan_location": "/Plans",
                    "pending_approval_location": "/Pending_Approval",
                    "risks_identified": len(analysis['risks']),
                    "steps_count": len(analysis['steps'])
                }
            }

            log_data.append(entry)

            # Write back
            with open(log_file, "w") as f:
                json.dump(log_data, f, indent=2)

            self.log(f"Log entry created for {filename}")
            return True
        except Exception as e:
            self.log(f"Error creating log entry: {str(e)}")
            return False

    def move_to_done(self, filename: str) -> bool:
        """Move processed file to Done directory"""
        try:
            source = self.needs_action_dir / filename
            destination = self.done_dir / filename
            shutil.move(str(source), str(destination))
            self.log(f"File moved to Done: {filename}")
            return True
        except Exception as e:
            self.log(f"Error moving file to Done: {str(e)}")
            return False

    def validate_prerequisites(self, filename: str, plan_filename: str) -> bool:
        """Validate all prerequisites before moving file"""
        checks = {
            "Plan exists in /Plans": (self.plans_dir / plan_filename).exists(),
            "Plan exists in /Pending_Approval": (self.pending_approval_dir / plan_filename).exists(),
            "Log entry created": True  # Already validated in create_log_entry
        }

        all_passed = all(checks.values())

        if not all_passed:
            self.log(f"Pre-move validation failed for {filename}:")
            for check, passed in checks.items():
                if not passed:
                    self.log(f"  ✗ {check}")

        return all_passed

    def process_file(self, filepath: Path) -> bool:
        """Process a single file through the enhanced workflow"""
        filename = filepath.name
        self.log(f"Processing file: {filename}")

        # Step 1: Read file content
        content = self.read_file_content(filepath)
        if content is None:
            return False

        # Step 2: Parse metadata and analyze
        metadata, body = self.parse_frontmatter(content)
        analysis = self.analyze_content(body, metadata)

        # Step 3: Create plan (MUST SUCCEED)
        plan_filename = self.create_plan(filename, body, metadata, analysis)
        if plan_filename is None:
            self.log(f"Plan creation failed for {filename} - keeping in Needs_Action")
            return False

        # Step 4: Copy to Pending_Approval (MUST SUCCEED)
        if not self.copy_to_pending_approval(plan_filename):
            self.log(f"Copy to Pending_Approval failed for {filename} - keeping in Needs_Action")
            return False

        # Step 5: Create log entry (MUST SUCCEED)
        if not self.create_log_entry(filename, plan_filename, analysis):
            self.log(f"Log entry creation failed for {filename} - keeping in Needs_Action")
            return False

        # Step 6: Validate prerequisites
        if not self.validate_prerequisites(filename, plan_filename):
            self.log(f"Prerequisite validation failed for {filename} - keeping in Needs_Action")
            return False

        # Step 7: Move to Done (ONLY IF ALL ABOVE SUCCEED)
        if not self.move_to_done(filename):
            return False

        self.log(f"Successfully processed: {filename}")
        return True

    def run(self):
        """Main execution method"""
        self.log("=== Process Needs Action Skill v2.0 Started ===")

        # Find all markdown files in Needs_Action
        if not self.needs_action_dir.exists():
            self.log("Needs_Action directory does not exist")
            return

        files = list(self.needs_action_dir.glob("*.md"))

        if not files:
            self.log("No files to process in Needs_Action")
            return

        self.log(f"Found {len(files)} file(s) to process")

        # Process each file
        success_count = 0
        failure_count = 0

        for filepath in files:
            if self.process_file(filepath):
                success_count += 1
            else:
                failure_count += 1

        self.log(f"=== Processing Complete ===")
        self.log(f"Success: {success_count}, Failures: {failure_count}")

if __name__ == "__main__":
    skill = ProcessNeedsActionSkill()
    skill.run()
