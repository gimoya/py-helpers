#!/usr/bin/env python3
"""
Generic script to generate an index.html file listing all files and directories
in the current folder, matching the existing style with responsive font sizing.
"""

import os
import sys
from pathlib import Path
from datetime import datetime


def format_file_size(size_bytes):
    """
    Format file size in bytes to human-readable format.
    
    Args:
        size_bytes (int): File size in bytes
        
    Returns:
        str: Formatted file size (e.g., "1.2 MB", "456 KB")
    """
    if size_bytes == 0:
        return "0 B"
    
    # Define size units and their byte equivalents
    size_units = [
        ("B", 1),
        ("KB", 1024),
        ("MB", 1024**2),
        ("GB", 1024**3),
        ("TB", 1024**4)
    ]
    
    # Find the appropriate unit
    for unit, unit_size in reversed(size_units):
        if size_bytes >= unit_size:
            # Calculate the size in the current unit
            size_in_unit = size_bytes / unit_size
            # Format with appropriate decimal places
            if unit == "B":
                return f"{int(size_in_unit)} {unit}"
            elif size_in_unit >= 100:
                return f"{int(size_in_unit)} {unit}"
            else:
                return f"{size_in_unit:.1f} {unit}"
    
    return f"{size_bytes} B"


def format_modification_time(timestamp):
    """
    Format modification timestamp to human-readable format.
    
    Args:
        timestamp (float): Unix timestamp
        
    Returns:
        str: Formatted date and time with parentheses (e.g., "(2024-01-15 14:30)")
    """
    try:
        dt = datetime.fromtimestamp(timestamp)
        return f"({dt.strftime('%Y-%m-%d %H:%M')})"
    except (ValueError, OSError):
        return "(-)"


def generate_index_html(folder_path=".", output_file="index.html"):
    """
    Generate an index.html file listing all files and directories in the specified folder.
    
    Args:
        folder_path (str): Path to the folder to index (default: current directory)
        output_file (str): Name of the output HTML file (default: index.html)
    """
    folder = Path(folder_path).resolve()
    
    if not folder.exists() or not folder.is_dir():
        print(f"Error: '{folder_path}' is not a valid directory")
        return False
    
    # Get all items in the directory, sorted alphabetically
    items = []
    try:
        for item in sorted(folder.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            if item.name.startswith("."):
                continue
            if item.name == output_file or item.name == "generate_index.py":
                continue
            if item.is_file() and item.suffix.lower() == ".bat":
                continue
            items.append(item)
    except PermissionError:
        print(f"Error: Permission denied accessing '{folder_path}'")
        return False
    
    # Get the folder name for the title
    folder_name = folder.name if folder.name else "Root"
    
    # Generate HTML content
    html_content = f"""<!doctype html>
<meta charset="utf-8">
<title>Index of /{folder_name}</title>
<style>
  html {{ font-family: Consolas, "Courier New", monospace; font-size: clamp(20px, 4vw, 20px); }}
  body {{ margin: clamp(12px, 3vw, 24px); color: #0f172a; background: #f8fafc; }}
  h1 {{ font-size: clamp(24px, 5vw, 28px); margin: 0 0 clamp(12px, 2.5vw, 16px); font-weight: 600; }}
  ul {{
    list-style: none;
    padding: 0;
    margin: 0;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
  }}
  li + li {{ border-top: 1px solid #e2e8f0; }}
  a {{ display: flex; justify-content: space-between; align-items: center; padding: clamp(14px, 3vw, 18px); color: #0f172a; text-decoration: none; }}
  a:hover {{ background: #f1f5f9; }}
  .file-info {{ display: flex; gap: 20px; color: #64748b; font-size: clamp(0.8em, 2.5vw, 0.9em); }}
  .file-info span:first-child {{ min-width: 140px; text-align: left; }}
  .file-info span:last-child {{ min-width: 80px; text-align: left; }}
</style>
<h1>Index of /{folder_name}</h1>
<ul>
"""
    
    # Add each item to the list
    for item in items:
        # Determine if it's a directory (add trailing slash)
        display_name = item.name + "/" if item.is_dir() else item.name
        
        # Get file info (size and modification time)
        try:
            stat_info = item.stat()
            file_size = stat_info.st_size if item.is_file() else 0
            mod_time = stat_info.st_mtime
            
            if item.is_file():
                size_display = format_file_size(file_size)
            else:
                size_display = "-"
            
            time_display = format_modification_time(mod_time)
            
        except (OSError, PermissionError):
            size_display = "-"
            time_display = "-"
        
        file_info = f'<span class="file-info"><span>{time_display}</span><span>{size_display}</span></span>'
        
        html_content += f'  <li><a href="{item.name}">{display_name}{file_info}</a></li>\n'
    
    html_content += "</ul>\n"
    
    # Write the HTML file
    output_path = folder / output_file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Successfully generated '{output_file}' in '{folder_path}'")
        print(f"Indexed {len(items)} items")
        return True
    except PermissionError:
        print(f"Error: Permission denied writing to '{output_path}'")
        return False
    except Exception as e:
        print(f"Error writing file: {e}")
        return False


def main():
    """Main function to handle command line arguments and generate the index."""
    # Check for help flag first
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("Usage: python generate_index.py [folder_path] [output_file]")
        print("")
        print("Arguments:")
        print("  folder_path  Path to folder to index (default: current directory)")
        print("  output_file  Name of output HTML file (default: index.html)")
        print("")
        print("Examples:")
        print("  python generate_index.py                    # Index current directory")
        print("  python generate_index.py /path/to/folder    # Index specific folder")
        print("  python generate_index.py . index.html       # Custom output filename")
        return
    
    # Parse command line arguments
    folder_path = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "index.html"
    
    # Generate the index
    success = generate_index_html(folder_path, output_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
