#!/usr/bin/env python3
"""Post-uninstall hook: remove SKILL.md from ~/.agents directory"""

import shutil
from pathlib import Path


def main():
    """Remove SKILL.md copy from ~/.agents/skills/jobspy/"""
    home = Path.home()
    target = home / ".agents" / "skills" / "jobspy" / "SKILL.md"
    
    if target.exists():
        target.unlink()
        print(f"✔ Removed: {target}")
    else:
        print(f"⚠ Not found: {target}")
    return 0


if __name__ == "__main__":
    main()
