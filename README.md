# Music Release Tracker

A simple Python tool to track and display new music releases from RateYourMusic lists and charts. This tool processes saved HTML files from RateYourMusic to extract album information, tracks new releases, and generates an organized HTML report.

## Features

-   Extracts album information from locally saved HTML files (both release lists and charts)
-   Processes chart pages with ratings and genres information
-   Highlights highly-rated releases (3.60+) with green styling
-   Identifies new releases by comparing with previous data
-   Generates an alphabetically organized HTML report of new releases
-   Handles multiple artists and collaborations
-   Removes duplicate entries
-   Stores all data in JSON format for future reference

## Installation

1. Clone this repository or download the source code:

```bash
git clone https://github.com/yourusername/music-release-tracker.git
cd music-release-tracker
```

2. Create a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Saving HTML Pages

1. Navigate to the RateYourMusic list or chart page you want to track
   - For lists: e.g., https://rateyourmusic.com/list/Goltzman/lancamentos-nacionais-2025/
   - For charts: e.g., https://rateyourmusic.com/charts/top/album/2025/
2. Right-click on the page and select "View Page Source"
3. Save the HTML to a file in the `saved_pages` directory
4. If there are multiple pages, repeat this process for each page, giving the files unique names

### Processing HTML Files

Run the script to process the saved HTML files:

```bash
python3 process_saved_html.py
```

### Viewing Results

After running the script:

1. The JSON data will be saved to `files/albums-YYYY-MM-DD.json`
2. An HTML report of new releases will be generated at `files/new_releases-YYYY-MM-DD.html`
3. Open the HTML file in your browser to view the alphabetically organized list of new releases
   - Chart releases will show ratings and genres information
   - Albums with ratings of 3.60 or higher will be highlighted in green

## Directory Structure

-   `saved_pages/`: Store HTML files from RateYourMusic here
-   `files/`: Output directory for JSON data and HTML reports
-   `process_saved_html.py`: Main script for processing HTML files
-   `requirements.txt`: List of Python dependencies

## Dependencies

-   beautifulsoup4: For parsing HTML files
-   soupsieve: Required by beautifulsoup4

## Why Manual HTML Saving?

RateYourMusic has strong anti-scraping measures that make direct web scraping difficult. This approach of manually saving HTML files and then processing them offers several advantages:

1. Reliability: Avoids being blocked by anti-scraping measures
2. Simplicity: Fewer dependencies and simpler code
3. Control: You can verify the HTML content before processing

## License

MIT

## Contributing

Contributions are welcome! Feel free to submit a Pull Request.
