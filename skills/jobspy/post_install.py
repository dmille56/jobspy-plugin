#!/usr/bin/env python3
"""Post-install hook: copy SKILL.md to user's .agents directory"""

import os
import shutil
from pathlib import Path


def main():
    """Copy SKILL.md to ~/.agents/skills/jobspy/"""
    home = Path.home()
    target = home / ".agents" / "skills" / "jobspy" / "SKILL.md"
    
    # Create parent directories
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"✔ Created directory: {target.parent}")
    
    # Copy SKILL.md from package
    package_dir = Path(__file__).parent
    source = package_dir / "SKILL.md"
    shutil.copy2(str(source), str(target))
    print(f"✔ Copied SKILL.md to: {target}")
    return 0


if __name__ == "__main__":
    main()
