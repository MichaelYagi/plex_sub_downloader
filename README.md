# Plex Info

A comprehensive Python utility for analyzing your Plex library with detailed media information, quality analysis, statistics, and health checks. Features a beautiful web interface for viewing your library data.

## Features

### 🌐 **Web Interface**
- Beautiful, responsive web interface with embedded data
- No server required - just open the HTML file in your browser
- Interactive navigation sidebar
- Filter and search within libraries
- Mobile-friendly design

### 📊 **Comprehensive Overview Dashboard**
- **Plex Server Info** - Server name, version, platform details
- **Library Statistics** - Total items, size, subtitle coverage
- **Quality & Technical** - Top resolutions, video/audio codecs, format distribution
- **Size & Duration** - Average, largest, smallest file sizes

### 📚 **Library Support**
- Movies
- TV Shows  
- Music
- Music Videos
- All other Plex library types

### 🔍 **Detailed Media Information**
- File path and size
- Video quality (4K, 1080p, 720p, SD)
- Video codec (H.264, H.265/HEVC, AV1)
- Audio codec (AAC, DTS, Dolby Digital)
- Watch status and view counts
- Subtitle information (languages, formats, external/embedded)
- Direct Plex web URLs

## Requirements

- Python 3.7+
- Plex Media Server
- Plex authentication token

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Dependencies:
- `plexapi>=4.15.0` - Plex API client
- `python-dotenv>=1.0.0` - Environment variable management
- `psutil>=5.9.0` - System information

3. Create a `.env` file in the same directory:
```env
PLEX_URL=http://192.168.0.199:32400
PLEX_TOKEN=your_plex_token_here
```

### Getting Your Plex Token

1. Open Plex Web App
2. Play any media item
3. Click the "..." menu → "Get Info"
4. Click "View XML"
5. Look in the URL bar for `X-Plex-Token=xxxxx`
6. Copy the token value

## Usage

### Web Interface (Recommended)

Generate a standalone HTML file with all your library data embedded:

```bash
python plex_info.py --export-json plex_data.html
```

This will:
1. Scan **ALL** your Plex libraries (Movies, TV Shows, Music, Music Videos, etc.)
2. Collect complete media information for every item
3. Generate a standalone HTML file with embedded data
4. Automatically open it in your default browser

**To update data:** Simply run the command again to regenerate with fresh data.

The generated HTML file:
- ✅ Works offline - no server needed
- ✅ Contains all your library data embedded
- ✅ Opens directly in any browser (double-click or file://)
- ✅ Mobile-responsive design
- ✅ Interactive filtering and search per library
- ✅ Completely standalone - no external dependencies

### Command Line Interface

#### List All Available Libraries

```bash
python plex_info.py
```

#### List Library Items

```bash
python plex_info.py --library "Movies"
python plex_info.py --library "TV Shows"
python plex_info.py --library "Music"
```

#### Find Items Missing Subtitles

```bash
python plex_info.py --library "Movies" --list-missing
```

#### Quality Analysis

```bash
python plex_info.py --library "Movies" --quality
```

Shows resolution and codec distribution with percentages.

#### Library Statistics

```bash
python plex_info.py --library "Movies" --stats
```

Shows watch stats, top genres, years, content ratings.

#### Health Check

```bash
python plex_info.py --library "Movies" --health
```

Identifies missing metadata, SD content, missing subtitles, large files, never watched items.

## Command Line Flags

| Flag | Description |
|------|-------------|
| `--export-json FILE` | Generate standalone HTML with embedded library data |
| `--library "NAME"` | Library name to analyze |
| `--list-missing` | Show only items missing subtitles |
| `--quality` | Analyze video quality and codec distribution |
| `--stats` | Show general statistics |
| `--health` | Check library health and identify issues |
| `--system` | Display Plex server information |
| `--type {movie\|episode}` | Filter by media type |
| `--output FILE` | Output file for CLI reports |
| `--verbose` | Enable verbose logging |
| `--help` | Show help message |

## Web Interface Features

### Overview Dashboard
- **Plex Server** - Name, version, platform, OS version
- **Library Statistics** - Total libraries, items, size, subtitle coverage
- **Quality & Technical** 
  - Top 3 resolutions with counts
  - Top 3 video codecs with counts
  - Top 3 audio codecs with counts
  - Unique resolution count
- **Size & Duration**
  - Average file size
  - Largest file size
  - Smallest file size
  - Total files count

### Per-Library Views
- Complete item listings with all metadata
- Filter by "missing subtitles only"
- Search functionality
- View counts and watch status
- Quality and codec information
- Direct links to items in Plex web interface

### Navigation
- Sidebar with all libraries
- Click to jump to any library section
- Mobile-responsive hamburger menu

## Example Workflows

### Generate Interactive Web Interface
```bash
# Scan all libraries and generate HTML
python plex_info.py --export-json plex_data.html

# Opens automatically in browser
# Share the HTML file or view it anytime
```

### Update Library Data
```bash
# Just run the export command again
python plex_info.py --export-json plex_data.html

# Regenerates with latest data
# Opens automatically when done
```

### Command Line Analysis
```bash
# List all libraries
python plex_info.py

# Check specific library quality
python plex_info.py --library "Movies" --quality

# Find content missing subtitles
python plex_info.py --library "TV Shows" --list-missing

# Run health check
python plex_info.py --library "Movies" --health
```

## File Structure

```
.
├── plex_info.py           # Main script
├── index.html             # Web interface template  
├── requirements.txt       # Python dependencies
├── .env                   # Your Plex credentials (create this)
├── README.md              # This file
└── plex_data.html         # Generated output (after running --export-json)
```

## Troubleshooting

### "index.html template not found"
- Make sure `index.html` is in the same directory as `plex_info.py`
- Both files are required for web interface generation

### "Could not find library"
- Library names are case-sensitive
- Use quotes: `--library "TV Shows"`
- Run `python plex_info.py` to see all available libraries

### "PLEX_TOKEN is required"
- Create a `.env` file with your Plex token
- Or pass directly: `--plex-token YOUR_TOKEN`

### Connection errors
- Verify Plex server is running
- Check PLEX_URL in `.env` file
- Ensure you can access Plex Web from same machine

### Slow performance
- Large libraries (1000+ items) take a few minutes
- Use `--verbose` to see progress
- Music libraries with many tracks take longer

### Browser not opening automatically (WSL2)
- Script detects WSL2 and converts paths for Windows
- If auto-open fails, manually open `plex_data.html`
- File works the same either way

## Notes

- **Read-only** - Never modifies your Plex library
- Scans **ALL library types** - Movies, TV Shows, Music, Music Videos, etc.
- Music tracks show as: Artist - Album - Title
- File paths are from Plex server's perspective
- URLs open items directly in Plex web interface
- Generated HTML is completely portable - share it, archive it, view offline

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Found a bug or want a feature? Please open an issue or submit a pull request!