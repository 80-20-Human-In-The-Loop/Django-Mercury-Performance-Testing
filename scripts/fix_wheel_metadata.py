#!/usr/bin/env python3
"""
Fix wheel and source distribution metadata by removing License-File entries that cause PyPI upload failures.

This script modifies wheel (.whl) and source distribution (.tar.gz) files to remove 
the License-File metadata field that setuptools 70+ automatically adds, which PyPI 
currently rejects as unrecognized.
"""

import os
import sys
import zipfile
import tarfile
import tempfile
import shutil
import argparse
from pathlib import Path
import re


def fix_metadata_lines(lines: list, verbose: bool = False) -> tuple:
    """
    Fix metadata lines by removing License-File and fixing Dynamic fields.
    
    Returns:
        tuple: (new_lines, removed_count, fixed_dynamic)
    """
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
    
    return new_lines, removed_count, fixed_dynamic


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
        
        # Fix metadata using shared function
        new_lines, removed_count, fixed_dynamic = fix_metadata_lines(lines, verbose)
        
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


def fix_metadata_in_sdist(sdist_path: Path, verbose: bool = False) -> bool:
    """
    Remove License-File entries from source distribution PKG-INFO.
    
    Args:
        sdist_path: Path to the .tar.gz file
        verbose: Print detailed output
        
    Returns:
        True if modifications were made, False otherwise
    """
    if verbose:
        print(f"Processing source distribution: {sdist_path}")
    
    # Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract tar.gz
        with tarfile.open(sdist_path, 'r:gz') as tar:
            tar.extractall(temp_path)
        
        # Find PKG-INFO files (there are usually two: root and in .egg-info)
        pkg_info_files = list(temp_path.glob("*/PKG-INFO")) + list(temp_path.glob("*/*.egg-info/PKG-INFO"))
        
        if not pkg_info_files:
            print(f"Warning: No PKG-INFO files found in {sdist_path}")
            return False
        
        total_removed = 0
        total_fixed = 0
        
        for pkg_info_path in pkg_info_files:
            if verbose:
                print(f"  Found PKG-INFO: {pkg_info_path.relative_to(temp_path)}")
            
            # Read and process PKG-INFO
            with open(pkg_info_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Fix metadata
            new_lines, removed_count, fixed_dynamic = fix_metadata_lines(lines, verbose)
            
            if removed_count > 0 or fixed_dynamic:
                # Write modified PKG-INFO
                with open(pkg_info_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                total_removed += removed_count
                if fixed_dynamic:
                    total_fixed += 1
        
        if total_removed == 0 and total_fixed == 0:
            if verbose:
                print(f"  No License-File entries or dynamic fields to fix in {sdist_path}")
            return False
        
        if verbose:
            if total_removed > 0:
                print(f"  Removed {total_removed} License-File entries across all PKG-INFO files")
            if total_fixed > 0:
                print(f"  Fixed {total_fixed} Dynamic fields containing license-file")
        
        # Create new tar.gz with modified metadata
        # First, create a backup
        backup_path = sdist_path.with_suffix('.tar.gz.bak')
        shutil.copy2(sdist_path, backup_path)
        if verbose:
            print(f"  Created backup: {backup_path}")
        
        # Get the base directory name (should be single directory in temp_path)
        base_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
        if len(base_dirs) != 1:
            print(f"Error: Expected single directory in archive, found {len(base_dirs)}")
            shutil.move(backup_path, sdist_path)
            return False
        
        base_dir = base_dirs[0]
        
        # Create new tar.gz
        with tarfile.open(sdist_path, 'w:gz') as tar:
            tar.add(base_dir, arcname=base_dir.name)
        
        if verbose:
            print(f"  Rebuilt source distribution: {sdist_path}")
        
        # Remove backup if successful
        os.remove(backup_path)
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Fix wheel and source distribution metadata by removing License-File entries")
    parser.add_argument('files', nargs='+', help='Distribution files to process (.whl or .tar.gz)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without modifying files')
    
    args = parser.parse_args()
    
    processed = 0
    modified = 0
    wheels_processed = 0
    sdists_processed = 0
    
    for file_pattern in args.files:
        # Handle glob patterns
        file_paths = list(Path().glob(file_pattern))
        
        if not file_paths:
            # Try as direct path
            file_path = Path(file_pattern)
            if file_path.exists():
                file_paths = [file_path]
            else:
                print(f"Warning: No files found matching {file_pattern}")
                continue
        
        for file_path in file_paths:
            # Determine file type and process accordingly
            if file_path.suffix == '.whl':
                processed += 1
                wheels_processed += 1
                
                if args.dry_run:
                    print(f"Would process wheel: {file_path}")
                    # Check if it needs modification
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        for name in zf.namelist():
                            if name.endswith('/METADATA'):
                                content = zf.read(name).decode('utf-8')
                                if 'License-File:' in content or 'Dynamic: license-file' in content:
                                    print(f"  Would remove License-File entries from {name}")
                                    modified += 1
                                    break
                else:
                    if fix_metadata_in_wheel(file_path, args.verbose):
                        modified += 1
                        print(f"✓ Fixed wheel: {file_path}")
                    elif args.verbose:
                        print(f"✓ No changes needed for wheel: {file_path}")
            
            elif file_path.name.endswith('.tar.gz'):
                processed += 1
                sdists_processed += 1
                
                if args.dry_run:
                    print(f"Would process source distribution: {file_path}")
                    # Check if it needs modification
                    with tarfile.open(file_path, 'r:gz') as tar:
                        for member in tar.getmembers():
                            if 'PKG-INFO' in member.name:
                                f = tar.extractfile(member)
                                if f:
                                    content = f.read().decode('utf-8')
                                    if 'License-File:' in content or 'Dynamic: license-file' in content:
                                        print(f"  Would remove License-File entries from {member.name}")
                                        modified += 1
                                        break
                else:
                    if fix_metadata_in_sdist(file_path, args.verbose):
                        modified += 1
                        print(f"✓ Fixed source distribution: {file_path}")
                    elif args.verbose:
                        print(f"✓ No changes needed for source distribution: {file_path}")
            
            else:
                print(f"Skipping unsupported file type: {file_path}")
                continue
    
    print(f"\nSummary: Processed {processed} files ({wheels_processed} wheels, {sdists_processed} source distributions), modified {modified}")
    
    if modified > 0 and not args.dry_run:
        print("\nDistributions have been modified. You can now upload them with twine.")
    
    return 0 if processed > 0 else 1


if __name__ == '__main__':
    sys.exit(main())