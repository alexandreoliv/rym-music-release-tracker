# Music Release Tracker

A simple Python tool to track and display new music releases from RateYourMusic lists and charts. This tool processes saved HTML and MHTML files from RateYourMusic to extract album information, tracks new releases, and generates an organized HTML report.

## Features

-   Extracts album information from locally saved `.html` and `.mhtml` files (both release lists and charts)
-   Processes chart pages with ratings and genres information
-   Highlights highly-rated releases (3.60+) with green styling
-   Identifies new releases by comparing with previous data
-   Generates an alphabetically organized HTML report of new releases
-   Removes duplicate entries
-   Stores all data in JSON format for future reference
-   Automatically opens the generated HTML report in the default web browser upon completion

## Installation

1.  Clone this repository or download the source code:

    ```bash
    git clone https://github.com/alexandreoliv/rym-music-release-tracker.git
    cd music-release-tracker
    ```

2.  Create a virtual environment (recommended):

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Saving HTML/MHTML Pages

1.  Navigate to the RateYourMusic list or chart page you want to track
    -   For lists: e.g., `https://rateyourmusic.com/list/Goltzman/lancamentos-nacionais-2025/`
    -   For charts: e.g., `https://rateyourmusic.com/charts/top/album/2025/`
2.  Save the *complete* web page.
    -   In most browsers (like Chrome, Firefox, Edge), use `Ctrl+S` (or `Cmd+S`) and choose "Webpage, Complete" or "Web Page, Single File (.mhtml)".
    -   Save the file (either `.html` with its associated folder, or a single `.mhtml` file) into the `saved_pages` directory.
3.  If there are multiple pages for a list or chart, repeat this process for each page, giving the files unique names (e.g., `chart_page_1.mhtml`, `chart_page_2.mhtml`).

### Processing Files

Run the script to process the saved files:

```bash
python3 process_saved_html.py
```

### Viewing Results

After running the script:

1.  The combined, deduplicated JSON data will be saved to `files/albums-YYYY-MM-DD.json`.
2.  An HTML report of new releases will be generated at `files/new_releases-YYYY-MM-DD.html`.
3.  The script will attempt to automatically open the HTML report in your default web browser.
4.  Open the HTML file manually if needed to view the alphabetically organized list of new releases.
    -   Chart releases will show ratings and genres information.
    -   Albums with ratings of 3.60 or higher will be highlighted in green.

## Directory Structure

-   `saved_pages/`: Store `.html` / `.mhtml` files (and associated folders if saving as "Webpage, Complete") from RateYourMusic here.
-   `files/`: Output directory for JSON data and HTML reports.
-   `process_saved_html.py`: Main script for processing files.
-   `requirements.txt`: List of Python dependencies.

## Dependencies

-   `beautifulsoup4`: For parsing HTML files
-   `soupsieve`: Required by `beautifulsoup4`

## Why Manual HTML/MHTML Saving?

RateYourMusic has strong anti-scraping measures that make direct web scraping difficult and unreliable. This approach of manually saving web pages and then processing them offers several advantages:

1.  **Reliability**: Avoids being blocked by anti-scraping measures.
2.  **Simplicity**: Fewer dependencies and simpler core processing logic.
3.  **Completeness**: Saving as "Webpage, Complete" or MHTML ensures all necessary page elements are captured locally for parsing.

## License

MIT

## Contributing

Contributions are welcome! Feel free to submit a Pull Request.
