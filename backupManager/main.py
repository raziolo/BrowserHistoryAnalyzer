import sqlite3
import platform
from pathlib import Path
from typing import List, Dict, Optional
import json





class BrowserHistoryReader:
    def __init__(self):
        self.system = platform.system()
        self.home = Path.home()
        from HistoryApp import app_settings
        self.app_settings = app_settings

        self.logger = app_settings.LOGGER

    def _create_backup_dir(self) -> bool:
        """Create backup directory if it doesn't exist"""
        try:
            self.app_settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create backup directory: {e}")
            return False

    def _get_chrome_path(self) -> Optional[Path]:
        """Get Chrome history file path for current OS"""
        paths = {
            'Windows': self.home / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'History',
            'Darwin': self.home / 'Library' / 'Application Support' / 'Google' / 'Chrome' / 'Default' / 'History',
            'Linux': self.home / '.config' / 'google-chrome' / 'Default' / 'History'
        }

        path = paths.get(self.system)
        if not path or not path.exists():
            self.logger.error(f"Chrome history path not found: {path}")
            return None
        return path

    def _get_firefox_profile(self) -> Optional[Path]:
        """Handle UTF-16 encoded profiles.ini files"""
        base_path = self.home / 'AppData' / 'Roaming' / 'Mozilla' / 'Firefox'
        profiles_ini = base_path / 'profiles.ini'

        if not profiles_ini.exists():
            return None

        try:
            # Detect encoding using BOM
            with open(profiles_ini, 'rb') as f:
                bom = f.read(2)
                encoding = 'utf-16-le' if bom == b'\xff\xfe' else 'utf-8'

            # Read with detected encoding
            with open(profiles_ini, 'r', encoding=encoding) as f:
                lines = f.readlines()

            current_section = None
            profile_data = {}

            for line in lines:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    profile_data[current_section] = {}
                elif current_section and current_section.startswith('Profile'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        profile_data[current_section][key.strip()] = value.strip()

            # Find default profile
            for section, data in profile_data.items():
                if data.get('Name').__contains__('default-release') and 'Path' in data:
                    profile_path = base_path / data['Path']
                    if (profile_path / 'places.sqlite').exists():
                        self.logger.debug(f"Found Firefox profile: {profile_path}")
                        return profile_path
            return None

        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error in {profiles_ini}: {e}")
            return None

    def _read_sqlite(self, path: Path, query: str) -> List[Dict]:
        """Generic SQLite reader with error handling"""
        try:
            with sqlite3.connect(str(path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            self.logger.error(f"Database error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error reading {path}: {e}")
            return []

    def get_chrome_history(self, max_results: int = 99999) -> List[Dict]:
        """Get Chrome browsing history"""
        path = self._get_chrome_path()
        if not path:
            return []

        query = f"""
            SELECT url, title, visit_count, 
                   datetime((last_visit_time/1000000) - 11644473600, 'unixepoch') as last_visit
            FROM urls
            ORDER BY last_visit_time DESC
            LIMIT {max_results}
        """

        return self._read_sqlite(path, query)

    def get_firefox_history(self, max_results: int = 99999) -> List[Dict]:
        """Get Firefox browsing history"""
        profile_dir = self._get_firefox_profile()
        if not profile_dir:
            return []

        path = profile_dir / 'places.sqlite' if profile_dir.is_dir() else profile_dir
        if not path.exists():
            self.logger.error(f"Firefox history file not found: {path}")
            return []

        query = f"""
            SELECT url, title, visit_count, 
                   datetime(last_visit_date/1000000, 'unixepoch') as last_visit
            FROM moz_places
            ORDER BY last_visit_date DESC
            LIMIT {max_results}
        """

        return self._read_sqlite(path, query)

    def _clean_old_backups(self, browser_name: str) -> None:
        """Delete previous backups for the specified browser"""
        try:
            pattern = f"{browser_name.lower()}_history.*"
            for old_file in self.app_settings.BACKUP_DIR.glob(pattern):
                if old_file.is_file():
                    old_file.unlink()
                    self.logger.debug(f"Deleted old backup: {old_file}")
        except Exception as e:
            self.logger.error(f"Failed to clean old backups: {e}")

    def backup_history(self, history_data: List[Dict], browser_name: str) -> Optional[Path]:
        """
        Save history data to JSON and CSV files, deleting previous backups
        Returns path to backup directory if successful
        """
        if not history_data:
            self.logger.warning(f"No {browser_name} history to backup")
            return None

        if not self._create_backup_dir():
            return None

        try:
            # Clean previous backups first
            self._clean_old_backups(browser_name)

            # Create fixed filename without timestamp
            base_name = f"{browser_name.lower()}_history"

            if browser_name.lower() == "chrome":
                # pprint(history_data)
                pass

            # JSON Backup
            json_path = self.app_settings.BACKUP_DIR / f"{base_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            '''
            # CSV Backup
            csv_path = self.backup_dir / f"{base_name}.csv"
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=history_data[0].keys())
                writer.writeheader()
                writer.writerows(history_data)
            '''

            self.logger.info(f"Backup created at {self.backup_dir}\n")
            return self.backup_dir

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None


# Usage example
if __name__ == "__main__":
    reader = BrowserHistoryReader()

    print("Chrome History:")
    chrome_history = reader.get_chrome_history(10000)
    if chrome_history:
        reader.backup_history(chrome_history, "Chrome")

    print("\nFirefox History:")
    firefox_history = reader.get_firefox_history(10000)
    if firefox_history:
        reader.backup_history(firefox_history, "Firefox")
