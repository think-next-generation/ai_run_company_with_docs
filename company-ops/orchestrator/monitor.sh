#!/bin/bash
# Orchestrator Monitoring Script
# This script is called by Claude Code's CronCreate

set -e

LOG_FILE="orchestrator/logs/monitor.log"
REPORT_FILE="orchestrator/reports/latest.md"

echo "=== Orchestrator Monitoring $(date -Iseconds) ===" | tee -a "$LOG_FILE"

# 1. Check system status
echo -e "\n## System Status" | tee -a "$LOG_FILE"
cops status 2>&1 | tee -a "$LOG_FILE" || echo "Error checking status" | tee -a "$LOG_FILE"

# 2. Check unanswered questions
echo -e "\n## Unanswered Questions" | tee -a "$LOG_FILE"
cops question list --unanswered 2>&1 | tee -a "$LOG_FILE" || echo "No unanswered questions" | tee -a "$LOG_FILE"

# 3. Check task board
echo -e "\n## Task Board" | tee -a "$LOG_FILE"
cops board show 2>&1 | tee -a "$LOG_FILE" || echo "Error checking board" | tee -a "$LOG_FILE"

# 4. Check subsystem registry
echo -e "\n## Subsystem Status" | tee -a "$LOG_FILE"
cat subsystems/_registry.json 2>&1 | tee -a "$LOG_FILE" || echo "No registry found" | tee -a "$LOG_FILE"

echo -e "\n=== Monitoring Complete ===" | tee -a "$LOG_FILE"
