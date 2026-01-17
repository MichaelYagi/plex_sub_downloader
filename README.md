# Plex Open Subtitles Downloader

Automatically download missing subtitles for your Plex media library using the OpenSubtitles API.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```bash
# Plex Configuration
PLEX_URL=http://localhost:32400
PLEX_TOKEN=your-plex-token-here

# OpenSubtitles Configuration (required for local method)
OPENSUBTITLES_API_KEY=your-api-key-here
OPENSUBTITLES_USERNAME=your-username
OPENSUBTITLES_PASSWORD=your-password

# Subtitle Languages (comma-separated, 2-letter codes)
SUBTITLE_LANGUAGES=en
```

## Download Methods

### Local Method (default)
✅ Full control over subtitle selection (rating, downloads)  
✅ Best subtitle quality  
✅ Detailed reporting  
❌ Requires filesystem access to media files  
❌ Requires OpenSubtitles API credentials  

### Plex Method
✅ Works remotely (no filesystem access needed)  
✅ No OpenSubtitles credentials required (uses Plex's account)  
✅ Simpler setup  
❌ Less control over which subtitle is selected  
❌ Limited to Plex's OpenSubtitles rate limits  
❌ Less detailed reporting  

## Usage

### Check Status First
Always run a status check before downloading to verify your configuration:

```bash
# Check status with local method (requires OpenSubtitles credentials)
python downloader.py --status

# Check status with plex method (no credentials required)
python downloader.py --status --method plex
```

<details>
<summary>Example Status Output</summary>

```
================================================================================
PLEX SUBTITLE DOWNLOADER - STATUS CHECK
================================================================================

Checking Environment Variables...
--------------------------------------------------------------------------------
  ✓ .env file found at: /home/user/plex-subtitles/.env
  ✓ PLEX_URL: http://192.168.1.100:32400
  ✓ PLEX_TOKEN: ********************abcd
  ✓ OPENSUBTITLES_API_KEY: ********************xyz9
  ✓ OPENSUBTITLES_USERNAME: myusername
  ✓ OPENSUBTITLES_PASSWORD: ************
  ✓ SUBTITLE_LANGUAGES: en, es

Checking Plex Connection...
--------------------------------------------------------------------------------
  ✓ Connected to Plex server: MyPlexServer
    Version: 1.32.8.7639
    Platform: Linux
  ✓ Found 2 movie and 1 TV show libraries:
    - Movies (Movies): 450 items
    - 4K Movies (Movies): 120 items
    - TV Shows (TV Shows): 85 shows
  ✓ Write permissions OK in: /mnt/media/Movies/Inception (2010)

Checking OpenSubtitles API Key...
--------------------------------------------------------------------------------
  ✓ OpenSubtitles API key is valid
    Rate limit: 38/40 requests remaining

Checking OpenSubtitles Login...
--------------------------------------------------------------------------------
  ✓ Successfully logged in as: myusername
    Account level: Sub-user
    Daily download limit: 200
    Downloads remaining today: 195
    Quota resets in: 18 hours and 32 minutes

================================================================================
✓ STATUS: READY TO DOWNLOAD SUBTITLES
================================================================================
```
</details>

### Download Subtitles

```bash
# Download for specific library with limit (local method)
python downloader.py --library "Movies" --max-downloads 10

# Download using Plex method (works remotely)
python downloader.py --method plex --library "Movies" --max-downloads 10

# Download for all libraries with limit
python downloader.py --max-downloads 50

# Download everything in a library (no limit)
python downloader.py --library "Movies"

# Download with multiple languages
python downloader.py --languages en es fr --library "Movies"

# Custom report filename
python downloader.py --max-downloads 20 --report my_report.txt
```

### Download Report

After downloading, a detailed report is generated showing what was downloaded:

<details>
<summary>Example Report Output</summary>

```
================================================================================
SUBTITLE DOWNLOAD REPORT
================================================================================
Total subtitles downloaded: 15
Generated: 2026-01-17 14:30:22
================================================================================

MOVIES (10 subtitles)
--------------------------------------------------------------------------------

Inception
  Language: EN
  Rating: 8.5/10
  Downloads: 45,203
  Release: Inception.2010.1080p.BluRay.x264
  Uploader: john_doe
  File: Inception.en.srt
  Timestamp: 2026-01-17 14:25:10

TV EPISODES (5 subtitles)
--------------------------------------------------------------------------------

Breaking Bad - S01E01 - Pilot
  Language: EN
  Rating: 9.2/10
  Downloads: 12,450
  Release: Breaking.Bad.S01E01.1080p.WEB-DL
  Uploader: subtitle_master
  File: S01E01.en.srt
  Timestamp: 2026-01-17 14:28:33

================================================================================
SUMMARY STATISTICS
================================================================================
Average subtitle rating: 8.7/10
Total community downloads: 234,567

Language breakdown:
  EN: 15
================================================================================
```
</details>

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--status` | Check configuration without downloading |
| `--method` | `local` (default) or `plex` download method |
| `--library` | Specific library name to process |
| `--max-downloads` | Maximum number of subtitles to download |
| `--languages` | Space-separated language codes (e.g., `en es fr`) |
| `--type` | Filter by `movie` or `episode` |
| `--report` | Custom report filename (default: `subtitle_download_report.txt`) |
| `--verbose` | Enable detailed logging |

## Getting API Credentials

1. **Plex Token**: Sign in to Plex Web App → Open browser dev tools (F12) → Network tab → Look for `X-Plex-Token` in request headers
2. **OpenSubtitles API Key**: Sign up at [opensubtitles.com](https://www.opensubtitles.com) → Go to [API Consumers](https://www.opensubtitles.com/en/consumers) → Create new application

## Troubleshooting

**"Media directory not accessible" warning:**
- Use `--method plex` if running script remotely from Plex server
- Or run the script directly on the machine where Plex server is hosted

**Rate limit errors:**
- Script automatically handles rate limits with retry logic
- Check your daily download quota with `--status`