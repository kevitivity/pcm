#!/usr/bin/env python3

import os
import shutil
import argparse
from pathlib import Path
import re
from typing import List, Dict
import sys

class PAMManager:
    def __init__(self, pam_dir: str = "/etc/pam.d"):
        self.pam_dir = Path(pam_dir)
        self.backup_dir = Path("/etc/pam.d.backup")
        
    def backup_config(self) -> None:
        """Create a backup of the entire pam.d directory"""
        if not os.path.exists(self.backup_dir):
            shutil.copytree(self.pam_dir, self.backup_dir)
            print(f"Backup created at {self.backup_dir}")
        else:
            print("Backup already exists")

    def restore_backup(self) -> None:
        """Restore PAM configuration from backup"""
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.pam_dir)
            shutil.copytree(self.backup_dir, self.pam_dir)
            print("Configuration restored from backup")
        else:
            print("No backup found")

    def parse_pam_line(self, line: str) -> Dict:
        """Parse a PAM configuration line into components"""
        parts = line.strip().split()
        if len(parts) < 3 or parts[0].startswith('#'):
            return None
            
        return {
            'type': parts[0],
            'control': parts[1],
            'module': parts[2],
            'args': ' '.join(parts[3:]) if len(parts) > 3 else ''
        }

    def get_service_rules(self, service: str) -> List[Dict]:
        """Get all rules for a specific PAM service"""
        service_path = self.pam_dir / service
        if not service_path.exists():
            print(f"Service {service} not found")
            return []

        rules = []
        with open(service_path, 'r') as f:
            for line in f:
                parsed = self.parse_pam_line(line)
                if parsed:
                    rules.append(parsed)
        return rules

    def add_rule(self, service: str, rule_type: str, control: str, 
                 module: str, args: str = "", position: str = "end") -> None:
        """Add a new rule to a PAM service configuration"""
        service_path = self.pam_dir / service
        if not service_path.exists():
            print(f"Service {service} not found")
            return

        new_rule = f"{rule_type}\t{control}\t{module}"
        if args:
            new_rule += f"\t{args}"
        new_rule += "\n"

        with open(service_path, 'r') as f:
            lines = f.readlines()

        if position == "start":
            lines.insert(0, new_rule)
        else:
            lines.append(new_rule)

        with open(service_path, 'w') as f:
            f.writelines(lines)
        print(f"Rule added to {service}")

    def remove_rule(self, service: str, module: str) -> None:
        """Remove rules containing specific module from a PAM service"""
        service_path = self.pam_dir / service
        if not service_path.exists():
            print(f"Service {service} not found")
            return

        with open(service_path, 'r') as f:
            lines = f.readlines()

        new_lines = [l for l in lines if module not in l]
        
        if len(new_lines) == len(lines):
            print(f"No rules found with module {module}")
            return

        with open(service_path, 'w') as f:
            f.writelines(new_lines)
        print(f"Rules containing module {module} removed from {service}")

    def list_services(self) -> List[str]:
        """List all PAM services"""
        return [f.name for f in self.pam_dir.iterdir() 
                if f.is_file() and not f.name.startswith('.')]

def main():
    parser = argparse.ArgumentParser(description='PAM Configuration Manager')
    parser.add_argument('--action', required=True, 
                       choices=['backup', 'restore', 'list', 'show', 'add', 'remove'])
    parser.add_argument('--service', help='PAM service name')
    parser.add_argument('--type', help='Rule type (auth, account, session, password)')
    parser.add_argument('--control', help='Control flag (required, requisite, sufficient, etc)')
    parser.add_argument('--module', help='PAM module name')
    parser.add_argument('--args', help='Module arguments')
    parser.add_argument('--position', choices=['start', 'end'], default='end',
                       help='Position to add new rule')

    args = parser.parse_args()
    
    # Initialize with test directory if not running as root
    pam_dir = "/etc/pam.d" if os.geteuid() == 0 else "./pam.d"
    manager = PAMManager(pam_dir)

    try:
        if args.action == 'backup':
            manager.backup_config()
        elif args.action == 'restore':
            manager.restore_backup()
        elif args.action == 'list':
            services = manager.list_services()
            print("\nAvailable PAM services:")
            for service in sorted(services):
                print(f"  - {service}")
        elif args.action == 'show':
            if not args.service:
                parser.error("--service is required for show action")
            rules = manager.get_service_rules(args.service)
            print(f"\nRules for {args.service}:")
            for rule in rules:
                print(f"  {rule['type']} {rule['control']} {rule['module']} {rule['args']}")
        elif args.action == 'add':
            if not all([args.service, args.type, args.control, args.module]):
                parser.error("--service, --type, --control, and --module are required for add action")
            manager.add_rule(args.service, args.type, args.control, 
                           args.module, args.args or "", args.position)
        elif args.action == 'remove':
            if not all([args.service, args.module]):
                parser.error("--service and --module are required for remove action")
            manager.remove_rule(args.service, args.module)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
