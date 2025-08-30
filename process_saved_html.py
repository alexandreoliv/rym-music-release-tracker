import os
import json
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import logging
import webbrowser
import email
import quopri

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SavedHtmlProcessor:
    def __init__(self, html_dir="saved_pages"):
        """Initialize the processor with the directory containing saved HTML files."""
        self.html_dir = html_dir
        self.releases = []
        self.chart_releases = []
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Ensure files directory exists
        Path("files").mkdir(exist_ok=True)
        
        # Ensure saved_pages directory exists
        Path(html_dir).mkdir(exist_ok=True)
    
    def find_html_files(self):
        """Find all HTML and MHTML files in the specified directory."""
        html_files = list(Path(self.html_dir).glob("*.html"))
        mhtml_files = list(Path(self.html_dir).glob("*.mhtml"))
        all_files = html_files + mhtml_files
        logger.info(f"Found {len(all_files)} HTML/MHTML files in {self.html_dir}")
        return all_files
    
    def _get_html_from_mhtml(self, file_path):
        """Extracts HTML content from an MHTML file."""
        try:
            with open(file_path, 'rb') as f:
                msg = email.message_from_binary_file(f)

            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/html':
                    charset = part.get_content_charset() or 'utf-8' # Default to utf-8 if not specified
                    payload = part.get_payload(decode=False)
                    encoding = part.get('Content-Transfer-Encoding')
                    
                    # Decode payload if necessary
                    if isinstance(payload, bytes):
                       html_content = payload # Already bytes, potentially needs decoding based on charset
                    else:
                        # If payload is string, encode it first for consistency before decoding
                        html_content = payload.encode(charset, errors='ignore')

                    if encoding == 'quoted-printable':
                        # quopri.decodestring expects bytes
                        html_content = quopri.decodestring(html_content)
                        # Now decode using the correct charset
                        return html_content.decode(charset, errors='ignore')
                    elif encoding == 'base64':
                         # If base64 encoding is encountered
                         import base64
                         html_content = base64.b64decode(html_content)
                         return html_content.decode(charset, errors='ignore')
                    else:
                        # Assume it's plain text or already decoded correctly by email module
                        # If it's bytes, decode using charset
                        if isinstance(html_content, bytes):
                           return html_content.decode(charset, errors='ignore')
                        else: # It's already a string
                            return html_content 
                                    
            logger.warning(f"No text/html part found in MHTML file: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error processing MHTML file {file_path}: {e}")
            return None
            
    def process_html_file(self, html_file):
        """Process a single HTML or MHTML file and extract release data."""
        logger.info(f"Processing file: {html_file}")
        html_content_str = None
        
        try:
            file_path_obj = Path(html_file)
            if file_path_obj.suffix.lower() == '.mhtml':
                logger.info("Detected MHTML file, extracting HTML content...")
                html_content_str = self._get_html_from_mhtml(html_file)
                if not html_content_str:
                    logger.error(f"Could not extract HTML from MHTML: {html_file}")
                    return 0 # Skip this file
            else:
                # Read standard HTML file
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content_str = f.read()

            if not html_content_str:
                 logger.error(f"Failed to read or extract content from {html_file}")
                 return 0

            soup = BeautifulSoup(html_content_str, 'html.parser')
            
            # Log page title for verification
            page_title = soup.title.string if soup.title else "No title found"
            logger.info(f"Page title: {page_title.strip() if page_title else 'No title found'}")
            
            # Check for specific list titles that need early stopping
            is_death_metal_list = page_title and "Death metal albums of 2025" in page_title 
            is_death_metal_demos_list = page_title and "Death metal demos/EPs of 2025-29 by year" in page_title
            
            should_stop_early = False
            stop_markers = []
            if is_death_metal_list:
                logger.info("Detected Death metal albums of 2025 list - will stop at UPCOMING marker")
                should_stop_early = True
                stop_markers = ["UPCOMING"]
            elif is_death_metal_demos_list:
                logger.info("Detected Death metal demos/EPs list - will stop at UPCOMING or UPCOMING/UNLISTENED marker")
                should_stop_early = True
                stop_markers = ["UPCOMING", "UPCOMING/UNLISTENED"]
            
            # Check if this is a chart page - handle potential MHTML encoding remnants (less likely now)
            chart_section = soup.find('section', id='page_charts_section_charts')
            # No need to check for 3D" anymore as we should have decoded HTML
                 
            if chart_section:
                logger.info("Found chart section, processing as chart page")
                return self.process_chart_page(soup, html_file)
            
            # Find the user_list table - handle potential MHTML encoding remnants (less likely now)
            user_list = soup.find('table', id='user_list')
            # No need to check for 3D" anymore

            if not user_list:
                logger.warning(f"No user_list table found in {html_file}")
                logger.info("Checking alternative table structures...")
                
                # Looking for any table that might contain the data
                all_tables = soup.find_all('table')
                logger.info(f"Found {len(all_tables)} tables in the file")
                
                # Debug info about tables
                for i, table in enumerate(all_tables):
                    table_id = table.get('id', 'No ID')
                    table_class = table.get('class', []) # Ensure class is a list
                    logger.info(f"Table {i+1} - ID: {table_id}, Class: {table_class}")
                    
                    # Check if any table has rows with main_entry
                    rows_with_main_entry = table.find_all('tr')
                    main_entry_count = 0
                    for row in rows_with_main_entry:
                        if row.find('td', class_='main_entry'):
                            main_entry_count += 1
                    if main_entry_count > 0:
                        logger.info(f"Table {i+1} has {main_entry_count} rows with main_entry class")
                

                
                return 0
            
            # Find all the rows
            rows = user_list.find_all('tr')
            logger.info(f"Found {len(rows)} rows in the table")
            
            file_releases = []
            
            for i, row in enumerate(rows):
                # For specific lists, check if we've reached a stop marker
                if should_stop_early:
                    rendered_text_span = row.find('span', class_='rendered_text')
                    if rendered_text_span:
                        marker_text = rendered_text_span.text.strip().upper() # Check in uppercase
                        if marker_text in stop_markers:
                            break
                
                # Skip header row or rows without the main entry
                main_entry = row.find('td', class_='main_entry')
                if not main_entry:
                    continue
                
                # Find the h2 tag which contains the artist
                artist_h2 = main_entry.find('h2')
                # Find the h3 tag which contains the album
                album_h3 = main_entry.find('h3')
                
                if artist_h2 and album_h3:
                    # Extract artist - handle credited artists if present
                    if artist_h2.find('span', class_='credited_name'):
                        # Multiple artists case
                        artists = []
                        for artist_link in artist_h2.find_all('a', class_='list_artist'):
                            artists.append(artist_link.text.strip())
                        artist = " & ".join(artists)
                    else:
                        # Single artist case
                        artist_link = artist_h2.find('a', class_='list_artist')
                        if artist_link:
                            artist = artist_link.text.strip()
                        else:
                            artist = artist_h2.text.strip()
                    
                    # Extract album
                    album_link = album_h3.find('a', class_='list_album')
                    if album_link:
                        album = album_link.text.strip()
                        link = album_link['href']
                        # If link is relative, make it absolute
                        if link and not link.startswith('http'):
                            link = f"https://rateyourmusic.com{link}"
                    else:
                        album = album_h3.text.strip()
                        link = ""
                    
                    release = {
                        "artist": artist,
                        "album": album,
                        "link": link,
                        "new": True,
                        "scraped_on": self.current_date,
                        "source_file": str(html_file),
                        "source_type": "releases"
                    }
                    
                    file_releases.append(release)
            
            logger.info(f"Extracted {len(file_releases)} releases from {html_file}")
            
            # Add to main releases list
            self.releases.extend(file_releases)
            
            return len(file_releases)
        
        except Exception as e:
            logger.error(f"Error processing {html_file}: {e}")
            return 0
    
    def process_chart_page(self, soup, html_file):
        """Process a chart page and extract chart release data."""
        logger.info(f"Processing chart page: {html_file}")
        try:
            # Find all chart items
            chart_items = soup.find_all('div', class_='page_charts_section_charts_item')
            logger.info(f"Found {len(chart_items)} chart items")
            
            file_chart_releases = []
            for item in chart_items:
                try:
                    # Extract album title
                    title_element = item.find('span', class_='ui_name_locale_original')
                    if not title_element:
                        continue
                    album = title_element.text.strip()
                    
                    # Extract artist name
                    artist_container = item.find('div', class_='page_charts_section_charts_item_credited_text')
                    if artist_container:
                        artist_element = artist_container.find('span', class_='ui_name_locale_original')
                        artist = artist_element.text.strip() if artist_element else artist_container.text.strip()
                    else:
                        continue
                    
                    # Extract album URL
                    link_element = item.find('a', class_='page_charts_section_charts_item_link')
                    link = ""
                    if link_element and 'href' in link_element.attrs:
                        link = link_element['href']
                        # If link is relative, make it absolute
                        if link and not link.startswith('http'):
                            link = f"https://rateyourmusic.com{link}"
                    
                    # Extract album rating
                    rating_element = item.find('span', class_='page_charts_section_charts_item_details_average_num')
                    rating = rating_element.text.strip() if rating_element else "N/A"
                    
                    # Extract primary genres
                    genres = []
                    genres_container = item.find('div', class_='page_charts_section_charts_item_genres_primary')
                    if genres_container:
                        for genre_element in genres_container.find_all('a', class_='genre'):
                            genres.append(genre_element.text.strip())
                    
                    chart_release = {
                        "artist": artist,
                        "album": album,
                        "link": link,
                        "rating": rating,
                        "genres": genres,
                        "new": True,
                        "scraped_on": self.current_date,
                        "source_file": str(html_file),
                        "source_type": "chart"
                    }
                    
                    file_chart_releases.append(chart_release)
                except Exception as e:
                    logger.error(f"Error processing chart item: {e}")
                    continue
            
            logger.info(f"Extracted {len(file_chart_releases)} chart releases from {html_file}")
            
            # Add to chart releases list
            self.chart_releases.extend(file_chart_releases)
            
            return len(file_chart_releases)
            
        except Exception as e:
            logger.error(f"Error processing chart page {html_file}: {e}")
            return 0
    
    def load_previous_data(self):
        """Load previous data if it exists."""
        # Check if there's an existing file for today first
        filename = f"files/albums-{self.current_date}.json"
        if os.path.exists(filename):
            logger.info(f"Loading today's data from {filename}")
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Look for most recent file if today's file doesn't exist
        files = list(Path("files").glob("albums-*.json"))
        if not files:
            logger.info("No previous data files found")
            return None
            
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        try:
            logger.info(f"Loading previous data from {latest_file}")
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error loading previous data: {e}")
            return None
    
    def compare_and_update(self):
        """Compare current data with previous data and update 'new' flag."""
        # NOTE: This now runs *after* remove_duplicates, operating on the combined list
        previous_data = self.load_previous_data()
        
        if not previous_data:
            logger.info("No previous data found. All entries marked as new.")
            # Ensure all items in the combined list are marked new by default
            for release in self.releases:
                release['new'] = True
            return
            
        # Create lookup dictionary for previous data
        previous_lookup = {f"{item['artist']}:{item['album']}": item for item in previous_data}
        
        # Update 'new' flag for current combined releases
        # All releases in self.releases are unique at this point
        for release in self.releases:
            key = f"{release['artist']}:{release['album']}"
            if key in previous_lookup:
                release['new'] = False
            else:
                release['new'] = True # Explicitly mark as new if not found
        
        new_count = sum(1 for release in self.releases if release['new'])
        logger.info(f"Found {new_count} new releases out of {len(self.releases)} total releases")
    
    def remove_duplicates(self):
        """Combine chart and regular releases, remove duplicates, prioritizing chart data."""
        all_raw_releases = self.releases + self.chart_releases
        original_total_count = len(all_raw_releases)
        logger.info(f"Starting deduplication for {original_total_count} total raw releases.")
        
        unique_all_releases = {}
        
        for release in all_raw_releases:
            # Basic normalization: lowercasing and stripping whitespace
            # More advanced normalization could be added here if needed
            artist_norm = release.get('artist', '').strip().lower()
            album_norm = release.get('album', '').strip().lower()
            
            if not artist_norm or not album_norm:
                logger.warning(f"Skipping release with missing artist/album during deduplication: {release}")
                continue # Skip entries with missing artist or album for keying
                
            key = f"{artist_norm}:{album_norm}"
            
            if key in unique_all_releases:
                # Key exists, check if current release is 'chart' and existing is not
                existing_release = unique_all_releases[key]
                if release.get('source_type') == 'chart' and existing_release.get('source_type') != 'chart':
                    # Prioritize chart release by replacing the existing one
                    logger.debug(f"Duplicate key '{key}'. Prioritizing chart data over existing release data.")
                    unique_all_releases[key] = release
                # Optionally: could merge data here if needed (e.g., keep genres/rating)
            else:
                # New key, add the release
                unique_all_releases[key] = release
                
        # Update self.releases to be the final deduplicated list
        self.releases = list(unique_all_releases.values())
        self.chart_releases = [] # Clear the separate chart list as it's now merged
        
        final_count = len(self.releases)
        removed_count = original_total_count - final_count
        logger.info(f"Removed {removed_count} duplicate releases. Final count: {final_count}")
    
    def save_data(self):
        """Save the combined, deduplicated release data to JSON file."""
        # Data is already combined and deduplicated in self.releases
        filename = f"files/albums-{self.current_date}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.releases, f, indent=2, ensure_ascii=False) # Save self.releases directly
            logger.info(f"Data saved to {filename}")
            return filename
        except IOError as e:
            logger.error(f"Error saving data to {filename}: {e}")
            return None
    
    def generate_html(self):
        """Generate HTML page showing new releases from the combined list."""
        # Filter new releases from the combined list
        new_releases = [release for release in self.releases if release.get('new', True)] # Use .get for safety
        
        # Sort new releases alphabetically by artist name
        new_releases.sort(key=lambda x: x.get('artist', '').lower())
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Music Releases - {self.current_date}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1, h2 {{ 
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }}
        ul {{ 
            list-style-type: none;
            padding: 0;
        }}
        li {{ 
            margin-bottom: 10px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
        a {{ 
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{ 
            text-decoration: underline;
        }}
        .date {{ 
            color: #666;
            font-size: 0.8em;
        }}
        .letter-heading {{ 
            background-color: #333;
            color: white;
            padding: 5px 10px;
            margin-top: 20px;
            border-radius: 3px;
        }}
        .chart-item {{ 
            display: flex;
            flex-wrap: nowrap;
            align-items: center;
            white-space: nowrap;
        }}
        .item-main {{ 
            margin-right: 10px;
            white-space: normal;
        }}
        .rating {{ 
            display: inline-block;
            margin-left: 10px;
            background-color: #e9e9e9;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        .rating-high {{ 
            background-color: #c8e6c9;
            color: #2e7d32;
            font-weight: bold;
        }}
        .genres {{ 
            font-size: 0.8em;
            color: #555;
            margin-top: 3px;
        }}
        .source-type {{ 
            display: inline-block;
            font-size: 0.8em;
            background-color: #eee;
            border-radius: 3px;
            padding: 1px 5px;
            margin-left: 5px;
        }}
        .unknown {{ 
            color: #999;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <h1>New Music Releases - {self.current_date}</h1>
    <p>Found {len(new_releases)} new releases</p>
"""
        
        if new_releases:
            html_content += "    <ul>\n"
            
            # Group by first letter of artist name for better organization
            current_letter = None
            
            for release in new_releases:
                artist = release.get('artist', '')
                # Use normalized artist name for sorting/grouping if desired, but display original
                first_letter = artist[0].upper() if artist else '#' 
                
                # Add letter heading when first letter changes
                if first_letter != current_letter:
                    current_letter = first_letter
                    html_content += f"""        <li class="letter-heading">
                {current_letter}
            </li>\n"""
                
                # Display logic remains similar, checks source_type if available
                source_type = release.get('source_type', 'release') # Default to 'release' if missing
                artist_display = artist if artist else '<span class="unknown">Unknown Artist</span>'
                album_display = release.get('album', '<span class="unknown">Unknown Album</span>')
                link_display = release.get('link', '#')

                if source_type == 'chart':
                    genres_text = ", ".join(release.get('genres', []))
                    genres_html = f'<div class="genres">Genres: {genres_text}</div>' if genres_text else ''
                    
                    rating_value = release.get('rating', 'N/A')
                    try:
                        # Ensure rating_value is treated as string before float conversion
                        is_high_rating = float(str(rating_value)) >= 3.60 
                        rating_class = "rating rating-high" if is_high_rating else "rating"
                    except (ValueError, TypeError):
                        rating_class = "rating"
                        rating_value = 'N/A' # Ensure N/A if conversion fails
                    
                    html_content += f"""        <li>
                <div>
                    <span class="item-main">{artist_display} - <a href="{link_display}" target="_blank">{album_display}</a></span>
                    <span class="{rating_class}">{rating_value}</span>
                    <span class="source-type">Chart</span>
                </div>
                {genres_html}
            </li>\n"""
                else: # source_type is 'releases' or default
                    html_content += f"""        <li>
                <span class="item-main">{artist_display} - <a href="{link_display}" target="_blank">{album_display}</a></span>
                <span class="source-type">Release</span>
            </li>\n"""
            
            html_content += "    </ul>\n"
        else:
            html_content += "    <p>No new releases found today.</p>\n"
        
        html_content += """</body>
</html>"""
        
        filename = f"files/new_releases-{self.current_date}.html"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML report generated at {filename}")
            return filename
        except IOError as e:
            logger.error(f"Error generating HTML: {e}")
            return None
    
    def run(self):
        """Process all HTML files and generate reports."""
        try:
            html_files = self.find_html_files()
            
            if not html_files:
                logger.warning(f"No HTML files found in '{self.html_dir}' directory")
                return 0
            
            # Process each HTML file to extract releases
            total_processed = 0
            for html_file in html_files:
                try:
                    count = self.process_html_file(html_file)
                    total_processed += count
                except Exception as e:
                    logger.error(f"Failed to process {html_file}: {e}")
                    continue
            
            # Now combine and deduplicate
            self.remove_duplicates()
            
            # Now compare the unique list against previous data
            self.compare_and_update()
            
            # Check if any releases remain after deduplication
            if not self.releases:
                 logger.warning("No valid releases found after processing and deduplication.")
                 return 0
            
            # Save the final deduplicated and updated data
            json_filename = self.save_data()
            if not json_filename:
                logger.error("Failed to save JSON data.")
                # Decide if we should proceed without saving?
            
            # Generate HTML report from the final list
            html_filename = self.generate_html()
            
            logger.info("Music release processing completed successfully")
            if html_filename:
                logger.info(f"View new releases at {html_filename}")
                
                # Open the HTML file in the default web browser
                try:
                    logger.info(f"Opening {html_filename} in web browser...")
                    webbrowser.open(f"file://{os.path.abspath(html_filename)}")
                except Exception as e:
                    logger.error(f"Failed to open HTML file in browser: {e}")
            
            # Count new releases from the final, combined list
            new_count = sum(1 for r in self.releases if r.get('new', True))
            return new_count
        except Exception as e:
            logger.error(f"An error occurred during execution: {e}")
            # Consider re-raising or specific error handling
            import traceback
            logger.error(traceback.format_exc())
            return -1


if __name__ == "__main__":
    processor = SavedHtmlProcessor()
    new_count = processor.run()
    
    print(f"Process completed. Found {new_count if new_count >= 0 else 'unknown'} new releases.") 