#!/usr/bin/env python3
"""
Plex Missing Subtitles Downloader

Downloads missing subtitles for media in your Plex library using OpenSubtitles API.
Supports both direct file writing and Plex's built-in subtitle download.
"""

import os
import sys
import argparse
import logging
import time
import requests
from pathlib import Path
from typing import List, Set, Optional, Dict, Tuple
from plexapi.server import PlexServer
from plexapi.video import Movie, Episode
from dotenv import load_dotenv
from dataclasses import dataclass, field
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DownloadedSubtitle:
    """Record of a downloaded subtitle."""
    media_title: str
    media_type: str  # 'movie' or 'episode'
    language: str
    subtitle_file: str
    rating: float
    download_count: int
    release_name: str
    uploader: str
    method: str  # 'local' or 'plex'
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class StatusChecker:
    """Checks system status and configuration."""

    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []

    def check_all(
            self,
            plex_url: str,
            plex_token: str,
            opensubtitles_api_key: str,
            opensubtitles_username: str,
            opensubtitles_password: str,
            languages: List[str],
            method: str = 'local'
    ) -> bool:
        """
        Run all status checks.

        Returns:
            True if all critical checks pass, False otherwise
        """
        print("\n" + "=" * 80)
        print("PLEX SUBTITLE DOWNLOADER - STATUS CHECK")
        print("=" * 80 + "\n")

        # Check environment variables
        self._check_env_variables(
            plex_url,
            plex_token,
            opensubtitles_api_key,
            opensubtitles_username,
            opensubtitles_password,
            languages,
            method
        )

        # Check Plex connection
        if plex_url and plex_token:
            self._check_plex_connection(plex_url, plex_token, method)

        # Check OpenSubtitles API (only needed for local method)
        if method == 'local':
            if opensubtitles_api_key:
                self._check_opensubtitles_api(opensubtitles_api_key)

            # Check OpenSubtitles login
            if opensubtitles_api_key and opensubtitles_username and opensubtitles_password:
                self._check_opensubtitles_login(
                    opensubtitles_api_key,
                    opensubtitles_username,
                    opensubtitles_password
                )
        else:
            self.info.append("ℹ Using Plex's built-in subtitle download (OpenSubtitles credentials not required)")

        # Print results
        self._print_results()

        return len(self.issues) == 0

    def _check_env_variables(
            self,
            plex_url: str,
            plex_token: str,
            opensubtitles_api_key: str,
            opensubtitles_username: str,
            opensubtitles_password: str,
            languages: List[str],
            method: str
    ):
        """Check that all required environment variables are set."""
        print("Checking Environment Variables...")
        print("-" * 80)

        # Check .env file existence
        env_file = Path('.env')
        if env_file.exists():
            self.info.append(f"✓ .env file found at: {env_file.absolute()}")
        else:
            self.warnings.append("⚠ .env file not found (using command-line args or system env vars)")

        # Check download method
        self.info.append(f"✓ Download method: {method}")

        # Check Plex settings
        if plex_url:
            self.info.append(f"✓ PLEX_URL: {plex_url}")
        else:
            self.issues.append("✗ PLEX_URL is not set")

        if plex_token:
            self.info.append(f"✓ PLEX_TOKEN: {'*' * 20}...{plex_token[-4:]}")
        else:
            self.issues.append("✗ PLEX_TOKEN is not set")

        # Check OpenSubtitles settings (only for local method)
        if method == 'local':
            if opensubtitles_api_key:
                self.info.append(f"✓ OPENSUBTITLES_API_KEY: {'*' * 20}...{opensubtitles_api_key[-4:]}")
            else:
                self.issues.append("✗ OPENSUBTITLES_API_KEY is not set (required for local method)")

            if opensubtitles_username:
                self.info.append(f"✓ OPENSUBTITLES_USERNAME: {opensubtitles_username}")
            else:
                self.issues.append("✗ OPENSUBTITLES_USERNAME is not set (required for local method)")

            if opensubtitles_password:
                self.info.append(f"✓ OPENSUBTITLES_PASSWORD: {'*' * len(opensubtitles_password)}")
            else:
                self.issues.append("✗ OPENSUBTITLES_PASSWORD is not set (required for local method)")

        # Check languages
        if languages:
            self.info.append(f"✓ SUBTITLE_LANGUAGES: {', '.join(languages)}")
            # Validate language codes
            valid_codes = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ar', 'ja', 'ko', 'zh']
            for lang in languages:
                if len(lang) != 2:
                    self.warnings.append(f"⚠ Language code '{lang}' should be 2 letters (ISO 639-1)")
        else:
            self.warnings.append("⚠ SUBTITLE_LANGUAGES not set, defaulting to 'en'")

        print()

    def _check_plex_connection(self, plex_url: str, plex_token: str, method: str):
        """Check connection to Plex server."""
        print("Checking Plex Connection...")
        print("-" * 80)

        try:
            plex = PlexServer(plex_url, plex_token)
            self.info.append(f"✓ Connected to Plex server: {plex.friendlyName}")
            self.info.append(f"  Version: {plex.version}")
            self.info.append(f"  Platform: {plex.platform}")

            # Check libraries
            libraries = plex.library.sections()
            movie_libs = [lib for lib in libraries if lib.type == 'movie']
            show_libs = [lib for lib in libraries if lib.type == 'show']

            if movie_libs or show_libs:
                self.info.append(f"✓ Found {len(movie_libs)} movie and {len(show_libs)} TV show libraries:")
                for lib in movie_libs:
                    item_count = len(lib.all())
                    self.info.append(f"  - {lib.title} (Movies): {item_count} items")
                for lib in show_libs:
                    show_count = len(lib.all())
                    self.info.append(f"  - {lib.title} (TV Shows): {show_count} shows")
            else:
                self.warnings.append("⚠ No movie or TV show libraries found")

            # Check write permissions only if using local method
            if method == 'local':
                if movie_libs or show_libs:
                    test_lib = movie_libs[0] if movie_libs else show_libs[0]
                    items = test_lib.all()
                    if items:
                        sample_item = items[0]
                        if hasattr(sample_item, 'media') and sample_item.media:
                            if sample_item.media[0].parts:
                                media_path = Path(sample_item.media[0].parts[0].file)
                                media_dir = media_path.parent

                                if media_dir.exists():
                                    # Test write permissions
                                    test_file = media_dir / '.plex_subtitle_test'
                                    try:
                                        test_file.touch()
                                        test_file.unlink()
                                        self.info.append(f"✓ Write permissions OK in: {media_dir}")
                                    except PermissionError:
                                        self.issues.append(f"✗ No write permission in: {media_dir}")
                                    except Exception as e:
                                        self.warnings.append(f"⚠ Could not test write permissions: {e}")
                                else:
                                    self.warnings.append(f"⚠ Media directory not accessible: {media_dir}")
                                    self.info.append("  → Consider using --method plex for remote downloads")
            else:
                self.info.append("ℹ Skipping filesystem write check (using Plex download method)")

        except Exception as e:
            self.issues.append(f"✗ Failed to connect to Plex: {e}")

        print()

    def _check_opensubtitles_api(self, api_key: str):
        """Check OpenSubtitles API key validity."""
        print("Checking OpenSubtitles API Key...")
        print("-" * 80)

        try:
            headers = {
                "Api-Key": api_key,
                "User-Agent": "PlexSubDownloader v1.0",
                "Content-Type": "application/json"
            }

            # Try a simple search to validate API key
            response = requests.get(
                "https://api.opensubtitles.com/api/v1/subtitles",
                headers=headers,
                params={"query": "test", "languages": "en"},
                timeout=10
            )

            if response.status_code == 200:
                self.info.append("✓ OpenSubtitles API key is valid")

                # Check rate limit headers
                if 'X-RateLimit-Remaining' in response.headers:
                    remaining = response.headers['X-RateLimit-Remaining']
                    limit = response.headers.get('X-RateLimit-Limit', 'unknown')
                    self.info.append(f"  Rate limit: {remaining}/{limit} requests remaining")
            elif response.status_code == 401:
                self.issues.append("✗ OpenSubtitles API key is invalid")
            elif response.status_code == 429:
                self.warnings.append("⚠ Rate limit exceeded - wait before making more requests")
            else:
                self.warnings.append(f"⚠ Unexpected API response: {response.status_code}")

        except requests.exceptions.Timeout:
            self.warnings.append("⚠ OpenSubtitles API request timed out")
        except requests.exceptions.RequestException as e:
            self.issues.append(f"✗ Failed to connect to OpenSubtitles API: {e}")

        print()

    def _check_opensubtitles_login(self, api_key: str, username: str, password: str):
        """Check OpenSubtitles login credentials."""
        print("Checking OpenSubtitles Login...")
        print("-" * 80)

        try:
            headers = {
                "Api-Key": api_key,
                "User-Agent": "PlexSubDownloader v1.0",
                "Content-Type": "application/json"
            }

            response = requests.post(
                "https://api.opensubtitles.com/api/v1/login",
                headers=headers,
                json={"username": username, "password": password},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                user_info = data.get('user', {})

                self.info.append(f"✓ Successfully logged in as: {username}")

                if user_info:
                    allowed_downloads = user_info.get('allowed_downloads', 'unknown')
                    level = user_info.get('level', 'unknown')
                    self.info.append(f"  Account level: {level}")
                    self.info.append(f"  Daily download limit: {allowed_downloads}")

                # Try to get current download quota
                if token:
                    quota_headers = headers.copy()
                    quota_headers["Authorization"] = f"Bearer {token}"

                    # Make a test download request to see quota
                    quota_response = requests.post(
                        "https://api.opensubtitles.com/api/v1/download",
                        headers=quota_headers,
                        json={"file_id": 0},  # Invalid ID, just to get quota info
                        timeout=10
                    )

                    if quota_response.status_code in [200, 406]:  # 406 = not found, but still returns quota
                        try:
                            quota_data = quota_response.json()
                            remaining = quota_data.get('remaining')
                            reset_time = quota_data.get('reset_time')
                            if remaining is not None:
                                self.info.append(f"  Downloads remaining today: {remaining}")
                            if reset_time:
                                self.info.append(f"  Quota resets in: {reset_time}")
                        except:
                            pass

            elif response.status_code == 401:
                self.issues.append("✗ Invalid username or password")
            elif response.status_code == 429:
                self.warnings.append("⚠ Rate limit exceeded for login attempts")
            else:
                self.warnings.append(f"⚠ Login failed with status code: {response.status_code}")

        except requests.exceptions.Timeout:
            self.warnings.append("⚠ Login request timed out")
        except requests.exceptions.RequestException as e:
            self.issues.append(f"✗ Failed to login: {e}")

        print()

    def _print_results(self):
        """Print the status check results."""
        print("=" * 80)
        print("STATUS CHECK RESULTS")
        print("=" * 80 + "\n")

        # Print info
        if self.info:
            print("Information:")
            for item in self.info:
                print(f"  {item}")
            print()

        # Print warnings
        if self.warnings:
            print("Warnings:")
            for item in self.warnings:
                print(f"  {item}")
            print()

        # Print issues
        if self.issues:
            print("Issues (must be resolved):")
            for item in self.issues:
                print(f"  {item}")
            print()

        # Print summary
        print("=" * 80)
        if not self.issues:
            print("✓ STATUS: READY TO DOWNLOAD SUBTITLES")
            print("=" * 80 + "\n")
            print("Run without --status flag to start downloading subtitles.")
        else:
            print("✗ STATUS: CONFIGURATION ISSUES FOUND")
            print("=" * 80 + "\n")
            print("Please fix the issues above before running the script.")
            print("Check your .env file or command-line arguments.")
        print()


class OpenSubtitlesAPI:
    """OpenSubtitles API v1 client with rate limiting."""

    BASE_URL = "https://api.opensubtitles.com/api/v1"

    def __init__(
            self,
            api_key: str,
            username: str = None,
            password: str = None,
            user_agent: str = "PlexSubDownloader v1.0"
    ):
        """
        Initialize OpenSubtitles API client.

        Args:
            api_key: OpenSubtitles API key
            username: OpenSubtitles username (for downloads)
            password: OpenSubtitles password (for downloads)
            user_agent: User agent string (required by API)
        """
        self.api_key = api_key
        self.username = username
        self.password = password
        self.user_agent = user_agent
        self.jwt_token = None
        self.token_expiry = None
        self.headers = {
            "Api-Key": api_key,
            "User-Agent": user_agent,
            "Content-Type": "application/json"
        }
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        self.remaining_downloads = None

    def _wait_for_rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _handle_rate_limit_error(self, response: requests.Response) -> bool:
        """
        Handle rate limit errors from API.

        Returns:
            True if should retry, False otherwise
        """
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                wait_time = int(retry_after)
                logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                return True
            else:
                logger.error("Rate limit exceeded with no Retry-After header")
                return False
        return False

    def login(self) -> bool:
        """
        Authenticate and obtain JWT token for downloads.

        Returns:
            True if login successful, False otherwise
        """
        if not self.username or not self.password:
            logger.warning("No username/password provided. Downloads will not be available.")
            return False

        logger.info("Logging in to OpenSubtitles...")
        self._wait_for_rate_limit()

        try:
            response = requests.post(
                f"{self.BASE_URL}/login",
                headers=self.headers,
                json={
                    "username": self.username,
                    "password": self.password
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get('token')
                logger.info("Successfully logged in")
                return True
            elif response.status_code == 401:
                logger.error("Invalid username or password")
                return False
            else:
                logger.error(f"Login failed: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {e}")
            return False

    def search_subtitles(
            self,
            query: str = None,
            imdb_id: str = None,
            tmdb_id: str = None,
            languages: str = "en",
            movie_hash: str = None,
            file_size: int = None,
            season_number: int = None,
            episode_number: int = None
    ) -> Optional[List[Dict]]:
        """
        Search for subtitles.

        Args:
            query: Movie or TV show name
            imdb_id: IMDB ID (without 'tt' prefix)
            tmdb_id: TMDB ID
            languages: Comma-separated language codes (e.g., "en,es")
            movie_hash: OpenSubtitles movie hash
            file_size: File size in bytes
            season_number: Season number for TV shows
            episode_number: Episode number for TV shows

        Returns:
            List of subtitle results or None on error
        """
        self._wait_for_rate_limit()

        params = {
            "languages": languages,
        }

        if query:
            params["query"] = query
        if imdb_id:
            params["imdb_id"] = imdb_id
        if tmdb_id:
            params["tmdb_id"] = tmdb_id
        if movie_hash:
            params["moviehash"] = movie_hash
        if file_size:
            params["moviebytesize"] = file_size
        if season_number is not None:
            params["season_number"] = season_number
        if episode_number is not None:
            params["episode_number"] = episode_number

        try:
            response = requests.get(
                f"{self.BASE_URL}/subtitles",
                headers=self.headers,
                params=params,
                timeout=30
            )

            if self._handle_rate_limit_error(response):
                # Retry once after rate limit wait
                response = requests.get(
                    f"{self.BASE_URL}/subtitles",
                    headers=self.headers,
                    params=params,
                    timeout=30
                )

            if response.status_code == 200:
                data = response.json()
                return data.get('data', [])
            elif response.status_code == 401:
                logger.error("Invalid API key")
                return None
            elif response.status_code == 406:
                logger.debug("No subtitles found")
                return []
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None

    def download_subtitle(self, file_id: int) -> Optional[bytes]:
        """
        Download a subtitle file.

        Args:
            file_id: OpenSubtitles file ID

        Returns:
            Subtitle content as bytes or None on error
        """
        # Ensure we're logged in
        if not self.jwt_token:
            if not self.login():
                logger.error("Cannot download - not logged in")
                return None

        # Check daily download limit
        if self.remaining_downloads is not None and self.remaining_downloads <= 0:
            logger.error("Daily download limit reached")
            return None

        self._wait_for_rate_limit()

        # Create headers with JWT token
        download_headers = self.headers.copy()
        download_headers["Authorization"] = f"Bearer {self.jwt_token}"

        try:
            # Request download link
            response = requests.post(
                f"{self.BASE_URL}/download",
                headers=download_headers,
                json={"file_id": file_id},
                timeout=30
            )

            if self._handle_rate_limit_error(response):
                # Retry once after rate limit wait
                response = requests.post(
                    f"{self.BASE_URL}/download",
                    headers=download_headers,
                    json={"file_id": file_id},
                    timeout=30
                )

            if response.status_code == 200:
                data = response.json()
                download_link = data.get('link')
                self.remaining_downloads = data.get('remaining', self.remaining_downloads)

                if download_link:
                    # Download the actual subtitle file
                    sub_response = requests.get(download_link, timeout=30)
                    if sub_response.status_code == 200:
                        logger.debug(f"Remaining downloads: {self.remaining_downloads}")
                        return sub_response.content
                    else:
                        logger.error(f"Failed to download subtitle file: {sub_response.status_code}")
                        return None
            elif response.status_code == 401:
                logger.error("Invalid token - trying to re-login")
                self.jwt_token = None
                if self.login():
                    # Retry download with new token
                    return self.download_subtitle(file_id)
                return None
            elif response.status_code == 406:
                logger.error("Download limit reached or subtitle unavailable")
                return None
            else:
                logger.error(f"Download API error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Download request failed: {e}")
            return None

        return None


class PlexSubtitleDownloader:
    """Downloads missing subtitles for Plex media items."""

    def __init__(
            self,
            plex_url: str,
            plex_token: str,
            languages: List[str] = None,
            method: str = 'local',
            opensubtitles_api_key: str = None,
            opensubtitles_username: str = None,
            opensubtitles_password: str = None
    ):
        """
        Initialize the subtitle downloader.

        Args:
            plex_url: Plex server URL
            plex_token: Plex authentication token
            languages: List of language codes (e.g., ['en', 'es'])
            method: 'local' or 'plex' download method
            opensubtitles_api_key: OpenSubtitles API key (required for local method)
            opensubtitles_username: OpenSubtitles username (required for local method)
            opensubtitles_password: OpenSubtitles password (required for local method)
        """
        self.plex = PlexServer(plex_url, plex_token)
        self.languages = languages or ['en']
        self.method = method
        self.download_report: List[DownloadedSubtitle] = []

        logger.info(f"Connected to Plex server: {self.plex.friendlyName}")
        logger.info(f"Download method: {method}")
        logger.info(f"Target languages: {', '.join(self.languages)}")

        # Initialize OpenSubtitles API only for local method
        if method == 'local':
            if not opensubtitles_api_key or not opensubtitles_username or not opensubtitles_password:
                logger.error("OpenSubtitles credentials required for local method")
                sys.exit(1)

            self.api = OpenSubtitlesAPI(
                opensubtitles_api_key,
                opensubtitles_username,
                opensubtitles_password
            )
            self.api.login()
        else:
            self.api = None
            logger.info("Using Plex's built-in subtitle download")

    def get_existing_subtitle_languages(self, item) -> Set[str]:
        """Get language codes of existing subtitles for a media item."""
        existing_langs = set()

        for stream in item.subtitleStreams():
            if stream.languageCode:
                # Normalize to 2-letter codes
                lang_code = stream.languageCode.lower()
                if len(lang_code) == 3:
                    # Convert common 3-letter codes to 2-letter
                    conversions = {'eng': 'en', 'spa': 'es', 'fra': 'fr', 'deu': 'de', 'ita': 'it', 'por': 'pt'}
                    lang_code = conversions.get(lang_code, lang_code[:2])
                existing_langs.add(lang_code)

        return existing_langs

    def needs_subtitles(self, item) -> Set[str]:
        """
        Check which target languages are missing subtitles.

        Returns:
            Set of missing language codes
        """
        existing = self.get_existing_subtitle_languages(item)
        missing = set(self.languages) - existing
        return missing

    def get_media_path(self, item) -> Optional[Path]:
        """Get the file path for a media item."""
        try:
            if hasattr(item, 'media') and item.media:
                if item.media[0].parts:
                    file_path = item.media[0].parts[0].file
                    return Path(file_path)
        except Exception as e:
            logger.error(f"Error getting media path: {e}")
        return None

    def get_subtitle_path(self, media_path: Path, language: str, forced: bool = False) -> Path:
        """Generate subtitle file path."""
        suffix = f".{language}"
        if forced:
            suffix += ".forced"
        suffix += ".srt"
        return media_path.with_suffix(suffix)

    def subtitle_exists(self, media_path: Path, language: str) -> bool:
        """Check if subtitle file already exists on disk."""
        subtitle_path = self.get_subtitle_path(media_path, language)
        return subtitle_path.exists()

    def download_via_plex(self, item, language: str) -> bool:
        """
        Download subtitle using Plex's built-in search.

        Args:
            item: Plex media item
            language: 2-letter language code

        Returns:
            True if download triggered successfully
        """
        try:
            logger.info(f"  Searching via Plex for {language} subtitles...")

            # Trigger Plex to search for subtitles
            # This uses Plex's OpenSubtitles agent
            item.searchSubtitles(language=language)

            # Wait a moment for Plex to process
            time.sleep(2)

            # Refresh the item to see if subtitle was added
            item.reload()

            # Check if subtitle was added
            current_langs = self.get_existing_subtitle_languages(item)
            if language in current_langs:
                logger.info(f"  ✓ Plex downloaded {language} subtitle")
                return True
            else:
                logger.warning(f"  ✗ Plex did not find {language} subtitle")
                return False

        except Exception as e:
            logger.error(f"  ✗ Failed to download via Plex: {e}")
            return False

    def download_subtitles_for_item(self, item) -> int:
        """
        Download missing subtitles for a single item.

        Returns:
            Number of subtitles downloaded
        """
        # Get missing languages (not in Plex metadata)
        missing = self.needs_subtitles(item)

        # For local method, also check filesystem
        if self.method == 'local':
            media_path = self.get_media_path(item)
            if not media_path:
                logger.warning(f"Could not get path for: {item.title}")
                return 0

            if not media_path.exists():
                logger.warning(f"File not found: {media_path}")
                return 0

            # Check if subtitle files exist on disk
            missing = {lang for lang in missing if not self.subtitle_exists(media_path, lang)}

        if not missing:
            return 0

        item_name = f"{item.title}"
        media_type = "movie"
        if isinstance(item, Episode):
            item_name = f"{item.grandparentTitle} - S{item.seasonNumber:02d}E{item.index:02d} - {item.title}"
            media_type = "episode"

        logger.info(f"Downloading subtitles for: {item_name}")
        logger.info(f"  Missing languages: {', '.join(missing)}")

        downloaded_count = 0

        if self.method == 'plex':
            # Use Plex's built-in subtitle download
            for lang in missing:
                if self.download_via_plex(item, lang):
                    downloaded_count += 1
                    self.download_report.append(DownloadedSubtitle(
                        media_title=item_name,
                        media_type=media_type,
                        language=lang,
                        subtitle_file="Downloaded by Plex",
                        rating=0.0,
                        download_count=0,
                        release_name="Plex OpenSubtitles Agent",
                        uploader="Plex",
                        method="plex"
                    ))
        else:
            # Use direct OpenSubtitles API download (local method)
            downloaded_count = self._download_local(item, missing, item_name, media_type, media_path)

        return downloaded_count

    def _download_local(self, item, missing: Set[str], item_name: str, media_type: str, media_path: Path) -> int:
        """Download subtitles using local method (OpenSubtitles API)."""
        downloaded_count = 0

        # Prepare search parameters
        search_params = {
            "languages": ",".join(missing),
            "file_size": media_path.stat().st_size
        }

        # Add IMDB ID if available (preferred)
        try:
            for guid in item.guids:
                if guid.id.startswith('imdb://'):
                    imdb_id = guid.id.replace('imdb://tt', '')
                    search_params["imdb_id"] = imdb_id
                    break
                elif guid.id.startswith('tmdb://'):
                    tmdb_id = guid.id.replace('tmdb://', '')
                    search_params["tmdb_id"] = tmdb_id
                    break
        except:
            pass

        # Add episode info for TV shows
        if isinstance(item, Episode):
            search_params["season_number"] = item.seasonNumber
            search_params["episode_number"] = item.index
            if not search_params.get("imdb_id") and not search_params.get("tmdb_id"):
                search_params["query"] = item.grandparentTitle
        else:
            if not search_params.get("imdb_id") and not search_params.get("tmdb_id"):
                search_params["query"] = item.title

        # Search for subtitles
        logger.info(f"  Searching for subtitles...")
        results = self.api.search_subtitles(**search_params)

        if results is None:
            logger.error(f"  ✗ Search failed")
            return 0

        if not results:
            logger.info(f"  ✗ No subtitles found")
            return 0

        logger.info(f"  Found {len(results)} subtitle option(s)")

        # Download best subtitle for each missing language
        for lang in missing:
            # Find subtitles for this language
            lang_results = [r for r in results if r.get('attributes', {}).get('language') == lang]

            if not lang_results:
                logger.info(f"  ✗ No {lang} subtitles found")
                continue

            # Sort by rating first, then download count
            lang_results.sort(
                key=lambda x: (
                    x.get('attributes', {}).get('ratings', 0),
                    x.get('attributes', {}).get('download_count', 0)
                ),
                reverse=True
            )

            best = lang_results[0]
            attrs = best.get('attributes', {})
            file_id = attrs.get('files', [{}])[0].get('file_id')
            rating = attrs.get('ratings', 0.0)
            download_count = attrs.get('download_count', 0)
            release_name = attrs.get('release', 'Unknown')
            uploader = attrs.get('uploader', {}).get('name', 'Unknown')

            if not file_id:
                logger.warning(f"  ✗ No file ID for {lang} subtitle")
                continue

            logger.info(f"  Downloading {lang} subtitle (Rating: {rating:.1f}, Downloads: {download_count})...")
            content = self.api.download_subtitle(file_id)

            if content:
                # Save subtitle file
                subtitle_path = self.get_subtitle_path(media_path, lang)

                try:
                    with open(subtitle_path, 'wb') as f:
                        f.write(content)
                    logger.info(f"  ✓ Saved: {subtitle_path.name}")
                    downloaded_count += 1

                    # Add to download report
                    self.download_report.append(DownloadedSubtitle(
                        media_title=item_name,
                        media_type=media_type,
                        language=lang,
                        subtitle_file=str(subtitle_path),
                        rating=rating,
                        download_count=download_count,
                        release_name=release_name,
                        uploader=uploader,
                        method="local"
                    ))

                except Exception as e:
                    logger.error(f"  ✗ Failed to save subtitle: {e}")
            else:
                logger.warning(f"  ✗ Failed to download {lang} subtitle")

        return downloaded_count

    def generate_report(self) -> str:
        """Generate a detailed report of downloaded subtitles."""
        if not self.download_report:
            return "No subtitles were downloaded."

        report_lines = [
            "\n" + "=" * 80,
            "SUBTITLE DOWNLOAD REPORT",
            "=" * 80,
            f"Total subtitles downloaded: {len(self.download_report)}",
            f"Download method: {self.method}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            ""
        ]

        # Group by media type
        movies = [s for s in self.download_report if s.media_type == 'movie']
        episodes = [s for s in self.download_report if s.media_type == 'episode']

        if movies:
            report_lines.append(f"\nMOVIES ({len(movies)} subtitles)")
            report_lines.append("-" * 80)
            for sub in movies:
                report_lines.append(f"\n{sub.media_title}")
                report_lines.append(f"  Language: {sub.language.upper()}")
                if sub.method == 'local':
                    report_lines.append(f"  Rating: {sub.rating:.1f}/10")
                    report_lines.append(f"  Downloads: {sub.download_count:,}")
                    report_lines.append(f"  Release: {sub.release_name}")
                    report_lines.append(f"  Uploader: {sub.uploader}")
                    report_lines.append(f"  File: {Path(sub.subtitle_file).name}")
                else:
                    report_lines.append(f"  Method: Plex OpenSubtitles Agent")
                report_lines.append(f"  Timestamp: {sub.timestamp}")

        if episodes:
            report_lines.append(f"\n\nTV EPISODES ({len(episodes)} subtitles)")
            report_lines.append("-" * 80)
            for sub in episodes:
                report_lines.append(f"\n{sub.media_title}")
                report_lines.append(f"  Language: {sub.language.upper()}")
                if sub.method == 'local':
                    report_lines.append(f"  Rating: {sub.rating:.1f}/10")
                    report_lines.append(f"  Downloads: {sub.download_count:,}")
                    report_lines.append(f"  Release: {sub.release_name}")
                    report_lines.append(f"  Uploader: {sub.uploader}")
                    report_lines.append(f"  File: {Path(sub.subtitle_file).name}")
                else:
                    report_lines.append(f"  Method: Plex OpenSubtitles Agent")
                report_lines.append(f"  Timestamp: {sub.timestamp}")

        # Summary statistics
        report_lines.append("\n" + "=" * 80)
        report_lines.append("SUMMARY STATISTICS")
        report_lines.append("=" * 80)

        if self.method == 'local':
            avg_rating = sum(s.rating for s in self.download_report) / len(self.download_report)
            total_downloads = sum(s.download_count for s in self.download_report)
            report_lines.append(f"Average subtitle rating: {avg_rating:.1f}/10")
            report_lines.append(f"Total community downloads: {total_downloads:,}")

        # Language breakdown
        lang_counts = {}
        for sub in self.download_report:
            lang_counts[sub.language] = lang_counts.get(sub.language, 0) + 1

        report_lines.append("\nLanguage breakdown:")
        for lang, count in sorted(lang_counts.items()):
            report_lines.append(f"  {lang.upper()}: {count}")

        report_lines.append("=" * 80)

        return "\n".join(report_lines)

    def save_report(self, output_file: str = "subtitle_download_report.txt"):
        """Save the report to a file."""
        report = self.generate_report()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"\nReport saved to: {output_file}")

    def process_library(
            self,
            library_name: str,
            media_type: str = None,
            max_downloads: int = None
    ) -> dict:
        """
        Process a Plex library and download missing subtitles.

        Args:
            library_name: Name of the Plex library
            media_type: Filter by 'movie' or 'episode', or None for all
            max_downloads: Maximum number of subtitles to download (None = unlimited)

        Returns:
            Dictionary with statistics
        """
        try:
            library = self.plex.library.section(library_name)
        except Exception as e:
            logger.error(f"Could not find library '{library_name}': {e}")
            return {}

        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processing library: {library_name}")
        if max_downloads:
            logger.info(f"Max downloads: {max_downloads}")
        logger.info(f"{'=' * 60}\n")

        stats = {
            'total': 0,
            'needs_subtitles': 0,
            'downloaded': 0,
            'errors': 0,
            'skipped': 0
        }

        # Get all items
        items = []
        if media_type == 'movie' or library.type == 'movie':
            items = library.all()
            stats['total'] = len(items)
        elif media_type == 'episode' or library.type == 'show':
            # Get all episodes from all shows
            for show in library.all():
                for episode in show.episodes():
                    items.append(episode)
            stats['total'] = len(items)
        else:
            logger.warning(f"Unsupported library type: {library.type}")
            return stats

        logger.info(f"Found {len(items)} items to scan")

        # Process each item
        total_downloaded = 0
        for i, item in enumerate(items, 1):
            # Check if we've hit the download limit
            if max_downloads and total_downloaded >= max_downloads:
                stats['skipped'] = len(items) - i + 1
                logger.info(
                    f"\nReached download limit of {max_downloads}. Skipping remaining {stats['skipped']} items.")
                break

            try:
                missing = self.needs_subtitles(item)

                if missing:
                    stats['needs_subtitles'] += 1
                    logger.info(f"\n[{i}/{stats['total']}] Processing item...")

                    downloaded = self.download_subtitles_for_item(item)
                    if downloaded > 0:
                        stats['downloaded'] += downloaded
                        total_downloaded += downloaded
                else:
                    logger.debug(f"[{i}/{stats['total']}] Skipping {item.title} - has all subtitles")
            except Exception as e:
                logger.error(f"Error processing item {i}: {e}")
                stats['errors'] += 1

        # Print summary
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Summary for {library_name}:")
        logger.info(f"  Total items scanned: {stats['total']}")
        logger.info(f"  Items needing subtitles: {stats['needs_subtitles']}")
        logger.info(f"  Subtitles downloaded: {stats['downloaded']}")
        if stats['skipped']:
            logger.info(f"  Items skipped (limit reached): {stats['skipped']}")
        logger.info(f"  Errors: {stats['errors']}")
        logger.info(f"{'=' * 60}\n")

        return stats

    def process_all_libraries(
            self,
            media_type: str = None,
            max_downloads: int = None
    ) -> dict:
        """Process all movie and TV show libraries."""
        total_stats = {
            'total': 0,
            'needs_subtitles': 0,
            'downloaded': 0,
            'errors': 0,
            'skipped': 0
        }

        total_downloaded = 0
        for library in self.plex.library.sections():
            if library.type in ['movie', 'show']:
                # Calculate remaining download budget
                remaining = None
                if max_downloads:
                    remaining = max_downloads - total_downloaded
                    if remaining <= 0:
                        logger.info(f"Skipping library '{library.title}' - download limit reached")
                        continue

                stats = self.process_library(library.title, media_type, remaining)
                for key in total_stats:
                    total_stats[key] += stats.get(key, 0)

                total_downloaded = total_stats['downloaded']

        return total_stats


def main():
    parser = argparse.ArgumentParser(
        description='Download missing subtitles for Plex media'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Check configuration and system status without downloading'
    )
    parser.add_argument(
        '--method',
        choices=['local', 'plex'],
        default='local',
        help='Download method: local (direct file write) or plex (via Plex API)'
    )
    parser.add_argument(
        '--plex-url',
        default=os.getenv('PLEX_URL', 'http://localhost:32400'),
        help='Plex server URL (default: from .env or http://localhost:32400)'
    )
    parser.add_argument(
        '--plex-token',
        default=os.getenv('PLEX_TOKEN'),
        help='Plex authentication token (default: from .env)'
    )
    parser.add_argument(
        '--opensubtitles-api-key',
        default=os.getenv('OPENSUBTITLES_API_KEY'),
        help='OpenSubtitles API key (default: from .env, required for local method)'
    )
    parser.add_argument(
        '--opensubtitles-username',
        default=os.getenv('OPENSUBTITLES_USERNAME'),
        help='OpenSubtitles username (default: from .env, required for local method)'
    )
    parser.add_argument(
        '--opensubtitles-password',
        default=os.getenv('OPENSUBTITLES_PASSWORD'),
        help='OpenSubtitles password (default: from .env, required for local method)'
    )
    parser.add_argument(
        '--languages',
        nargs='+',
        default=os.getenv('SUBTITLE_LANGUAGES', 'en').split(','),
        help='Language codes to download (e.g., en es fr)'
    )
    parser.add_argument(
        '--library',
        help='Specific library name to process (default: all)'
    )
    parser.add_argument(
        '--type',
        choices=['movie', 'episode'],
        help='Filter by media type'
    )
    parser.add_argument(
        '--max-downloads',
        type=int,
        help='Maximum number of subtitles to download (default: unlimited)'
    )
    parser.add_argument(
        '--report',
        default='subtitle_download_report.txt',
        help='Output file for download report (default: subtitle_download_report.txt)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # If --status flag is present, run status check and exit
    if args.status:
        checker = StatusChecker()
        success = checker.check_all(
            plex_url=args.plex_url,
            plex_token=args.plex_token,
            opensubtitles_api_key=args.opensubtitles_api_key,
            opensubtitles_username=args.opensubtitles_username,
            opensubtitles_password=args.opensubtitles_password,
            languages=args.languages,
            method=args.method
        )
        sys.exit(0 if success else 1)

    # Validate required settings based on method
    if not args.plex_token:
        logger.error("PLEX_TOKEN is required. Set it in .env or pass --plex-token")
        sys.exit(1)

    if args.method == 'local':
        if not args.opensubtitles_api_key or not args.opensubtitles_username or not args.opensubtitles_password:
            logger.error("OpenSubtitles credentials required for local method. Use --method plex for remote operation.")
            sys.exit(1)

    # Initialize downloader
    try:
        downloader = PlexSubtitleDownloader(
            plex_url=args.plex_url,
            plex_token=args.plex_token,
            languages=args.languages,
            method=args.method,
            opensubtitles_api_key=args.opensubtitles_api_key,
            opensubtitles_username=args.opensubtitles_username,
            opensubtitles_password=args.opensubtitles_password
        )
    except Exception as e:
        logger.error(f"Failed to initialize downloader: {e}")
        sys.exit(1)

    # Process libraries
    try:
        if args.library:
            downloader.process_library(args.library, args.type, args.max_downloads)
        else:
            downloader.process_all_libraries(args.type, args.max_downloads)

        # Generate and display report
        report = downloader.generate_report()
        print(report)

        # Save report to file
        if downloader.download_report:
            downloader.save_report(args.report)

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        # Still generate report for what was downloaded
        if downloader.download_report:
            print(downloader.generate_report())
            downloader.save_report(args.report)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()