#!/usr/bin/env python3
"""
Fix wheel metadata by removing License-File entries that cause PyPI upload failures.

This script modifies wheel files to remove the License-File metadata field that
setuptools 70+ automatically adds, which PyPI currently rejects as unrecognized.
"""

import os
import sys
import zipfile
import tempfile
import shutil
import argparse
from pathlib import Path
import re


def fix_metadata_in_wheel(wheel_path: Path, verbose: bool = False) -> bool:
    """
    Remove License-File entries from wheel METADATA.
    
    Args:
        wheel_path: Path to the wheel file
        verbose: Print detailed output
        
    Returns:
        True if modifications were made, False otherwise
    """
    if verbose:
        print(f"Processing: {wheel_path}")
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract wheel
        with zipfile.ZipFile(wheel_path, 'r') as zf:
            zf.extractall(temp_path)
        
        # Find METADATA file
        metadata_files = list(temp_path.glob("*.dist-info/METADATA"))
        if not metadata_files:
            print(f"Warning: No METADATA file found in {wheel_path}")
            return False
        
        metadata_path = metadata_files[0]
        if verbose:
            print(f"  Found METADATA: {metadata_path.relative_to(temp_path)}")
        
        # Read and process METADATA
        with open(metadata_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Remove License-File lines and fix dynamic fields
        original_lines = len(lines)
        new_lines = []
        removed_count = 0
        fixed_dynamic = False
        
        for line in lines:
            # Check if this is a License-File line
            if line.startswith('License-File:'):
                removed_count += 1
                if verbose:
                    print(f"  Removing: {line.strip()}")
            # Check for problematic dynamic field
            elif line.startswith('Dynamic:') and 'license-file' in line.lower():
                # Remove license-file from dynamic fields
                parts = line.split(':', 1)
                if len(parts) == 2:
                    fields = [f.strip() for f in parts[1].split(',')]
                    # Remove any variation of license-file
                    cleaned_fields = [f for f in fields if f.lower() not in ['license-file', 'license-files', 'license_file', 'license_files']]
                    if cleaned_fields:
                        new_lines.append(f"Dynamic: {', '.join(cleaned_fields)}\n")
                    # If no other dynamic fields, skip the line entirely
                    fixed_dynamic = True
                    if verbose:
                        print(f"  Fixed dynamic field: {line.strip()}")
            else:
                new_lines.append(line)
        
        if removed_count == 0 and not fixed_dynamic:
            if verbose:
                print(f"  No License-File entries or dynamic fields to fix in {wheel_path}")
            return False
        
        # Write modified METADATA
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        if verbose:
            if removed_count > 0:
                print(f"  Removed {removed_count} License-File entries")
            if fixed_dynamic:
                print(f"  Fixed Dynamic field containing license-file")
        
        # Create new wheel with modified metadata
        # First, create a backup
        backup_path = wheel_path.with_suffix('.whl.bak')
        shutil.copy2(wheel_path, backup_path)
        if verbose:
            print(f"  Created backup: {backup_path}")
        
        # Remove original wheel
        os.remove(wheel_path)
        
        # Create new wheel
        with zipfile.ZipFile(wheel_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_path)
                    zf.write(file_path, arcname)
        
        if verbose:
            print(f"  Rebuilt wheel: {wheel_path}")
        
        # Verify the wheel is valid
        try:
            with zipfile.ZipFile(wheel_path, 'r') as zf:
                if zf.testzip() is not None:
                    print(f"Error: Rebuilt wheel {wheel_path} is corrupted")
                    # Restore backup
                    shutil.move(backup_path, wheel_path)
                    return False
        except Exception as e:
            print(f"Error validating rebuilt wheel: {e}")
            # Restore backup
            shutil.move(backup_path, wheel_path)
            return False
        
        # Remove backup if successful
        os.remove(backup_path)
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Fix wheel metadata by removing License-File entries")
    parser.add_argument('wheels', nargs='+', help='Wheel files to process')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without modifying files')
    
    args = parser.parse_args()
    
    processed = 0
    modified = 0
    
    for wheel_pattern in args.wheels:
        # Handle glob patterns
        wheel_paths = list(Path().glob(wheel_pattern))
        
        if not wheel_paths:
            # Try as direct path
            wheel_path = Path(wheel_pattern)
            if wheel_path.exists():
                wheel_paths = [wheel_path]
            else:
                print(f"Warning: No files found matching {wheel_pattern}")
                continue
        
        for wheel_path in wheel_paths:
            if not wheel_path.suffix == '.whl':
                print(f"Skipping non-wheel file: {wheel_path}")
                continue
            
            processed += 1
            
            if args.dry_run:
                print(f"Would process: {wheel_path}")
                # Check if it needs modification
                with zipfile.ZipFile(wheel_path, 'r') as zf:
                    for name in zf.namelist():
                        if name.endswith('/METADATA'):
                            content = zf.read(name).decode('utf-8')
                            if 'License-File:' in content:
                                print(f"  Would remove License-File entries from {name}")
                                modified += 1
                                break
            else:
                if fix_metadata_in_wheel(wheel_path, args.verbose):
                    modified += 1
                    print(f"✓ Fixed: {wheel_path}")
                elif args.verbose:
                    print(f"✓ No changes needed: {wheel_path}")
    
    print(f"\nSummary: Processed {processed} wheels, modified {modified}")
    
    if modified > 0 and not args.dry_run:
        print("\nWheels have been modified. You can now upload them with twine.")
    
    return 0 if processed > 0 else 1


if __name__ == '__main__':
    sys.exit(main())