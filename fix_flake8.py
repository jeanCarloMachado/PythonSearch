#!/usr/bin/env python3
"""
Quick script to fix common flake8 issues
"""

import re
import os
import subprocess

def fix_file(filepath):
    """Fix common flake8 issues in a file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix E231: missing whitespace after ':'
    # But be careful not to break URLs or other legitimate uses
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Skip URLs and f-strings with URLs
        if 'http://' in line or 'https://' in line:
            fixed_lines.append(line)
            continue
            
        # Fix dictionary/list syntax issues
        line = re.sub(r':([^\s=])', r': \1', line)
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Only write if content changed
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")

# Get list of Python files with issues
result = subprocess.run(['flake8', '--select=E231', '.'], 
                       capture_output=True, text=True, cwd='/Users/jean.machado@getyourguide.com/prj/PythonSearch')

if result.stdout:
    files_to_fix = set()
    for line in result.stdout.strip().split('\n'):
        if ':' in line:
            filepath = line.split(':')[0]
            files_to_fix.add(filepath)
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            fix_file(filepath)