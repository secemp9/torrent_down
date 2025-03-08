#!/usr/bin/env python3
import re
import argparse
import sys
import os
import requests
import time
from pathlib import Path
from torrentool.torrent import Torrent
import tempfile
import libtorrent as lt


def download_torrent(url):
    """Download a torrent file from a URL to a temporary file"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.torrent')
        with os.fdopen(fd, 'wb') as f:
            f.write(response.content)
        
        return temp_path
    except requests.RequestException as e:
        print(f"Error downloading torrent: {e}", file=sys.stderr)
        sys.exit(1)


def get_torrent_file_list(torrent_path):
    """
    Get list of files from a torrent using torrentool
    
    Args:
        torrent_path: Path or URL to the torrent file
        
    Returns:
        Torrent object and list of files with paths and sizes
    """
    # Check if it's a URL
    temp_file = None
    if torrent_path.startswith(('http://', 'https://')):
        temp_file = download_torrent(torrent_path)
        torrent_path = temp_file
    
    try:
        # Parse the torrent file
        torrent = Torrent.from_file(torrent_path)
        
        # Extract file information
        files = []
        for idx, file_info in enumerate(torrent.files, 1):
            path = file_info[0]
            size_bytes = file_info[1]
            
            # Convert bytes to human-readable format
            size = format_size(size_bytes)
            
            files.append({
                'index': idx,
                'path': path,
                'size': size,
                'size_bytes': f"{size_bytes:,}"
            })
        
        return torrent, files, torrent_path
    except Exception as e:
        print(f"Error parsing torrent: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Don't delete the temp file yet if it's needed for download
        pass


def format_size(size_bytes):
    """Convert bytes to human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.0f}KiB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/1024**2:.0f}MiB"
    else:
        return f"{size_bytes/1024**3:.0f}GiB"


def filter_by_month(files, month, year=None):
    """
    Filter files by month (and optionally year)
    
    Args:
        files: List of file dictionaries
        month: Month to filter (1-12)
        year: Optional year to filter
    
    Returns:
        Filtered list of files
    """
    # Ensure month is two digits
    month_str = f"{int(month):02d}"
    
    pattern = rf"_\d{{4}}-{month_str}\.zst$" if year is None else rf"_{year}-{month_str}\.zst$"
    
    return [file for file in files if re.search(pattern, file['path'])]


def save_filtered_torrent(original_torrent, filtered_files, output_path):
    """
    Create a new torrent with only the filtered files
    
    Args:
        original_torrent: Original Torrent object
        filtered_files: List of filtered file dictionaries
        output_path: Path to save the new torrent
    """
    # Get the original file indices
    filtered_indices = [file['index'] - 1 for file in filtered_files]  # Adjust for 0-based indexing
    
    # Create a new torrent with the same properties
    new_torrent = Torrent()
    new_torrent.comment = original_torrent.comment
    new_torrent.created_by = "Torrent Month Filter"
    new_torrent.announce_urls = original_torrent.announce_urls
    
    # Filter files
    new_files = [(original_torrent.files[idx][0], original_torrent.files[idx][1]) 
                for idx in filtered_indices if idx < len(original_torrent.files)]
    
    if not new_files:
        print("No files to include in the filtered torrent", file=sys.stderr)
        sys.exit(1)
    
    # Set the new files and save
    new_torrent.files = new_files
    new_torrent.to_file(output_path)
    
    print(f"Created filtered torrent: {output_path}")
    return output_path


def download_filtered_files(torrent_path, filtered_files, output_dir=None):
    """
    Download the filtered files using libtorrent
    
    Args:
        torrent_path: Path to the torrent file
        filtered_files: List of filtered file dictionaries
        output_dir: Directory to save the downloaded files
    """
    if not output_dir:
        output_dir = os.getcwd()
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get file priorities (1 for files to download, 0 for others)
    file_indices = {file['index'] - 1 for file in filtered_files}  # Convert to 0-based
    
    # Initialize session
    ses = lt.session()
    # Use random ports between 10000 and 65535
    settings = {'listen_interfaces': '0.0.0.0:0'}
    ses.apply_settings(settings)
    
    # Add torrent
    info = lt.torrent_info(torrent_path)
    
    # Create handle
    params = {
        'ti': info,
        'save_path': output_dir
    }
    
    handle = ses.add_torrent(params)
    
    # Set file priorities (0 = don't download, 1 = download)
    file_priorities = [1 if i in file_indices else 0 for i in range(info.num_files())]
    handle.prioritize_files(file_priorities)
    
    print(f"Starting download of {len(filtered_files)} files to {output_dir}")
    print("Press Ctrl+C to stop the download")
    
    try:
        while True:
            s = handle.status()
            
            # Define state strings based on libtorrent states
            state_str = {
                lt.torrent_status.checking_files: 'checking files',
                lt.torrent_status.downloading_metadata: 'downloading metadata',
                lt.torrent_status.downloading: 'downloading',
                lt.torrent_status.finished: 'finished',
                lt.torrent_status.seeding: 'seeding',
                lt.torrent_status.allocating: 'allocating',
                lt.torrent_status.checking_resume_data: 'checking resume data'
            }
            
            # Get the state string or use a default if not found
            current_state = state_str.get(s.state, 'unknown')
            
            # Check if it's seeding (fully downloaded) instead of using deprecated is_seed()
            if s.state == lt.torrent_status.seeding:
                print("\nDownload complete!")
                break
            
            print(f"\rProgress: {s.progress*100:.2f}% | "
                  f"Download: {s.download_rate/1000:.1f} kB/s | "
                  f"Upload: {s.upload_rate/1000:.1f} kB/s | "
                  f"Peers: {s.num_peers} | "
                  f"State: {current_state}", end='')
            
            sys.stdout.flush()
            time.sleep(1)
            
            # Exit if download is finished
            # Alternative check for completion
            if s.progress >= 0.999 and s.state >= lt.torrent_status.finished:
                print("\nDownload complete!")
                break
            
    except KeyboardInterrupt:
        print("\nDownload stopped by user")
    
    # Clean up
    ses.remove_torrent(handle)
    print("Download session ended")


def main():
    parser = argparse.ArgumentParser(description="List and filter torrent files by month")
    parser.add_argument("torrent", help="Path or URL to the torrent file")
    parser.add_argument("-m", "--month", type=int, required=True, help="Month to filter (1-12)")
    parser.add_argument("-y", "--year", type=int, help="Optional year to filter")
    parser.add_argument("-o", "--output", help="Output path for filtered torrent")
    parser.add_argument("-d", "--download", action="store_true", help="Download filtered files")
    parser.add_argument("--download-dir", help="Directory to save downloaded files")
    
    args = parser.parse_args()
    
    # Validate month
    if args.month < 1 or args.month > 12:
        print("Error: Month must be between 1 and 12", file=sys.stderr)
        sys.exit(1)
        
    # Get torrent and file list
    torrent, files, torrent_path = get_torrent_file_list(args.torrent)
    
    # Filter by month (and year if provided)
    filtered_files = filter_by_month(files, args.month, args.year)
    
    # Display results
    if not filtered_files:
        print(f"No files found for month {args.month}" + 
              (f" and year {args.year}" if args.year else ""))
        sys.exit(0)
    
    print(f"Found {len(filtered_files)} files for month {args.month}" + 
          (f" and year {args.year}" if args.year else ""))
    
    for file in filtered_files:
        print(f"{file['index']}|{file['path']}")
        print(f"   |{file['size']} ({file['size_bytes']})")
        print("-" * 75)
    
    # Create filtered torrent if requested
    filtered_torrent_path = None
    if args.output:
        output_path = args.output
        if not output_path.endswith('.torrent'):
            output_path += '.torrent'
        
        filtered_torrent_path = save_filtered_torrent(torrent, filtered_files, output_path)
    
    # Download files if requested
    if args.download:
        download_dir = args.download_dir or os.getcwd()
        
        # If we have a filtered torrent, use that, otherwise use the original
        download_path = filtered_torrent_path or torrent_path
        
        download_filtered_files(download_path, filtered_files, download_dir)
    
    # Clean up temporary file if it exists
    if torrent_path != args.torrent and os.path.exists(torrent_path):
        os.unlink(torrent_path)


if __name__ == "__main__":
    main()
