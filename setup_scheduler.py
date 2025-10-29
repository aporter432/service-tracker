#!/usr/bin/env python3
"""
Scheduler Setup Script
Install/uninstall daily ORBCOMM sync scheduler for macOS
"""

import subprocess
import shutil
from pathlib import Path
import argparse


class SchedulerSetup:
    """Manages launchd scheduler installation"""

    def __init__(self):
        self.project_dir = Path(__file__).parent.absolute()
        self.python_path = self.project_dir / 'venv' / 'bin' / 'python3'
        self.scheduler_path = self.project_dir / 'orbcomm_scheduler.py'
        self.template_path = self.project_dir / 'com.orbcomm.tracker.plist.template'

        # User's LaunchAgents directory
        self.launch_agents_dir = Path.home() / 'Library' / 'LaunchAgents'
        self.plist_name = 'com.orbcomm.tracker.daily.plist'
        self.plist_path = self.launch_agents_dir / self.plist_name

        # Log directory
        self.log_dir = Path.home() / '.orbcomm' / 'logs'

    def check_requirements(self):
        """Check if all requirements are met"""
        issues = []

        if not self.python_path.exists():
            issues.append(f"Virtual environment not found: {self.python_path}")

        if not self.scheduler_path.exists():
            issues.append(f"Scheduler script not found: {self.scheduler_path}")

        if not self.template_path.exists():
            issues.append(f"Template not found: {self.template_path}")

        return issues

    def generate_plist(self):
        """Generate plist file from template"""
        # Read template
        with open(self.template_path, 'r') as f:
            content = f.read()

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Replace placeholders
        content = content.replace('{{PYTHON_PATH}}', str(self.python_path))
        content = content.replace('{{SCHEDULER_PATH}}', str(self.scheduler_path))
        content = content.replace('{{PROJECT_DIR}}', str(self.project_dir))
        content = content.replace('{{LOG_DIR}}', str(self.log_dir))

        # Ensure LaunchAgents directory exists
        self.launch_agents_dir.mkdir(parents=True, exist_ok=True)

        # Write plist file
        with open(self.plist_path, 'w') as f:
            f.write(content)

        print(f"✅ Generated plist file: {self.plist_path}")

    def install(self):
        """Install the scheduler"""
        print("=" * 70)
        print("  Installing ORBCOMM Daily Scheduler")
        print("=" * 70)
        print()

        # Check requirements
        issues = self.check_requirements()
        if issues:
            print("❌ Cannot install - requirements not met:")
            for issue in issues:
                print(f"   - {issue}")
            return False

        # Generate plist file
        print("📝 Generating launchd configuration...")
        self.generate_plist()
        print()

        # Make scheduler executable
        print("🔧 Making scheduler executable...")
        self.scheduler_path.chmod(0o755)
        print(f"✅ Made executable: {self.scheduler_path}")
        print()

        # Load into launchd
        print("🚀 Loading scheduler into launchd...")
        try:
            subprocess.run(
                ['launchctl', 'load', str(self.plist_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Scheduler loaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to load scheduler: {e.stderr}")
            return False

        print()
        print("=" * 70)
        print("✅ Scheduler installed successfully!")
        print("=" * 70)
        print()
        print("Configuration:")
        print(f"  Schedule:      Daily at 9:00 AM")
        print(f"  Inbox:         2 (continuous monitoring)")
        print(f"  Log location:  {self.log_dir}")
        print()
        print("Commands:")
        print(f"  Check status:  launchctl list | grep orbcomm")
        print(f"  View logs:     tail -f {self.log_dir}/scheduler_stdout.log")
        print(f"  Uninstall:     ./venv/bin/python3 setup_scheduler.py --uninstall")
        print()

        return True

    def uninstall(self):
        """Uninstall the scheduler"""
        print("=" * 70)
        print("  Uninstalling ORBCOMM Daily Scheduler")
        print("=" * 70)
        print()

        if not self.plist_path.exists():
            print("❌ Scheduler not installed (plist file not found)")
            return False

        # Unload from launchd
        print("🛑 Unloading scheduler from launchd...")
        try:
            subprocess.run(
                ['launchctl', 'unload', str(self.plist_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print("✅ Scheduler unloaded")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: {e.stderr}")

        # Remove plist file
        print("🗑️  Removing plist file...")
        self.plist_path.unlink()
        print(f"✅ Removed: {self.plist_path}")

        print()
        print("=" * 70)
        print("✅ Scheduler uninstalled successfully")
        print("=" * 70)
        print()

        return True

    def status(self):
        """Check scheduler status"""
        print("=" * 70)
        print("  ORBCOMM Scheduler Status")
        print("=" * 70)
        print()

        # Check if plist exists
        if self.plist_path.exists():
            print(f"✅ Configuration file: {self.plist_path}")
        else:
            print("❌ Configuration file not found (scheduler not installed)")
            print()
            print(f"To install: ./venv/bin/python3 setup_scheduler.py --install")
            return

        # Check launchd status
        try:
            result = subprocess.run(
                ['launchctl', 'list'],
                check=True,
                capture_output=True,
                text=True
            )

            if 'com.orbcomm.tracker.daily' in result.stdout:
                print("✅ Scheduler is loaded in launchd")

                # Extract status from launchctl list
                for line in result.stdout.split('\n'):
                    if 'com.orbcomm.tracker.daily' in line:
                        print(f"   Status: {line}")
            else:
                print("❌ Scheduler not loaded in launchd")
                print()
                print(f"To load: launchctl load {self.plist_path}")

        except subprocess.CalledProcessError as e:
            print(f"❌ Error checking status: {e.stderr}")

        print()

        # Check log files
        print("Log files:")
        stdout_log = self.log_dir / 'scheduler_stdout.log'
        stderr_log = self.log_dir / 'scheduler_stderr.log'

        if stdout_log.exists():
            print(f"  ✅ Standard output: {stdout_log}")
            # Show last few lines
            try:
                with open(stdout_log, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print(f"     Last line: {lines[-1].strip()}")
            except Exception:
                pass
        else:
            print(f"  📝 Standard output: {stdout_log} (not created yet)")

        if stderr_log.exists():
            print(f"  ✅ Error log: {stderr_log}")
        else:
            print(f"  📝 Error log: {stderr_log} (not created yet)")

        print()
        print("Next scheduled run: Tomorrow at 9:00 AM")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Setup ORBCOMM daily sync scheduler'
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--install', action='store_true', help='Install the scheduler')
    group.add_argument('--uninstall', action='store_true', help='Uninstall the scheduler')
    group.add_argument('--status', action='store_true', help='Check scheduler status')

    args = parser.parse_args()

    setup = SchedulerSetup()

    if args.install:
        success = setup.install()
        return 0 if success else 1
    elif args.uninstall:
        success = setup.uninstall()
        return 0 if success else 1
    elif args.status:
        setup.status()
        return 0


if __name__ == '__main__':
    exit(main())
