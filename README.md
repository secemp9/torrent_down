# tordown - Torrent File Lister and Filter

## Description

`tordown` is a Python script that allows you to list the files within a torrent file, filter them based on a month (and optionally a year), create a new torrent file containing only the filtered files, and optionally download those filtered files.  It supports torrent files from local file paths or URLs.

## Features

*   **Torrent Information Extraction:**  Parses torrent files and extracts information about the contained files, including paths and sizes. Supports local torrent files and torrents hosted at URLs.
*   **Month-Based Filtering:** Filters files based on a month (1-12) found in the filename.  Optionally filters by year as well.
*   **Filtered Torrent Creation:** Creates a new, smaller torrent file containing only the filtered files.
*   **Selective Downloading:** Downloads the filtered files using libtorrent, allowing for partial downloads based on your filter criteria.  Includes progress display during the download.
*   **Human-Readable File Sizes:**  Displays file sizes in a user-friendly format (e.g., KiB, MiB, GiB).
*   **Error Handling:** Includes robust error handling for common issues such as invalid torrent files, network problems, and incorrect user input.
*   **Temporary File Handling:** Properly manages temporary files downloaded from URLs, cleaning them up after use.

## Prerequisites

*   Python 3.6 or higher
*   Required Python packages:
    *   `requests`
    *   `torrentool`
    *   `libtorrent` (via `python-libtorrent`)
*   (Optional)  If you don't have pip installed:
   * `sudo apt install python3-pip` or `sudo yum install python3-pip`
*   (Optional)  If you are running from a virtual environment you may need to install pip with the command `python3 -m ensurepip --upgrade`

## Installation

1.  **Install Dependencies:**
    ```bash
    pip3 install requests torrentool python-libtorrent
    ```
    *   If you are using a system managed python, you may need to use `pip` to install it.  Otherwise, the command should be `pip3`.
2.  **Save the Script:** Save the `tordown.py` script to a directory in your system's PATH (e.g., `/usr/local/bin/`) or any directory you prefer.

## Usage

```bash
tordown.py <torrent_file_or_url> -m <month> [-y <year>] [-o <output_torrent_path>] [-d] [--download-dir <download_directory>]
```

### Arguments

*   `<torrent_file_or_url>`: The path to a local torrent file or the URL of a torrent file (e.g., `mytorrent.torrent` or `http://example.com/mytorrent.torrent`).
*   `-m`, `--month`: The month (1-12) to filter files by (required).
*   `-y`, `--year`: (Optional) The year to filter files by. If not provided, files matching any year will be included.
*   `-o`, `--output`: (Optional) The path for the output filtered torrent file (e.g., `filtered.torrent`). If not provided, a filtered torrent will not be created.  If a path is supplied, but without the `.torrent` suffix, it will be appended.
*   `-d`, `--download`: (Optional) Download the filtered files.  Requires libtorrent.
*   `--download-dir`: (Optional) The directory to save the downloaded files.  Defaults to the current working directory if not provided.

### Examples

1.  **List files in a torrent and filter by month:**

    ```bash
    tordown.py mytorrent.torrent -m 10
    ```

2.  **List files, filter by month and year, and create a filtered torrent:**

    ```bash
    tordown.py http://example.com/torrent.torrent -m 12 -y 2023 -o filtered_2023_12.torrent
    ```

3.  **List files, filter by month, create a filtered torrent, and download the filtered files:**

    ```bash
    tordown.py mytorrent.torrent -m 01 -o january.torrent -d --download-dir /home/user/downloads
    ```

## Output

The script will print the following information to the console:

*   A list of files found in the torrent.
*   The number of files found after filtering.
*   Information about the filtered files (index, path, size).
*   If a filtered torrent is created, a success message indicating the output path.
*   If downloading, a progress indicator and download statistics.

## Error Handling

The script includes error handling for the following situations:

*   Invalid torrent file paths or URLs.
*   Network errors when downloading torrent files from URLs.
*   Incorrect month values (e.g., not between 1 and 12).
*   Errors parsing torrent files.
*   Problems creating or writing to the filtered torrent file.
*   Exceptions during the download process.

Error messages are printed to `stderr`.

## Limitations and Future Improvements

*   **File Matching:** Relies on filename patterns (specifically the `_YYYY-MM.zst` format) to identify files for filtering. This might not be flexible enough for all use cases.  Consider allowing custom regex patterns as an option.
*   **Download Progress Display:** The progress display is basic.  Consider adding features to display the estimated time remaining, downloaded and remaining data, and more granular status information.
*   **Dependency Versions:** Specify exact dependency versions in `requirements.txt` and include `pip install -r requirements.txt` as an install method.
*   **More Flexible Filtering:**  Allow for more complex filtering criteria, such as filtering by file size, file extension, or keywords in the filename.
*   **GUI Interface:** Create a graphical user interface (GUI) for easier interaction.  Libraries like `PyQt` or `Tkinter` could be used.
*   **Torrent Tracker Support:** Add the option to add a torrent tracker or alter the announce URLs.
*   **Testing:** Add comprehensive unit tests to ensure the script functions correctly.

## License

This script is provided under the MIT License. See the `LICENSE` file for details.
