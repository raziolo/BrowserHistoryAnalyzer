import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from HistoryApp import app_settings # Assuming this module exists and has BACKUP_DIR defined


def check_backup_existence(backup_dir: Path) -> list[Path] | None:
    """
    Ensures the backup directory exists and returns a list of backup files.

    Args:
        backup_dir: The Path object representing the backup directory.

    Returns:
        A list of Path objects for existing backup files (*_history.json),
        or None if an error occurs during directory creation or listing.
        Returns an empty list if the directory exists but contains no backups.
    """
    try:
        # Create backup directory if needed
        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"Checked/created backup directory: {backup_dir}")

        # Find backup files
        backups = list(backup_dir.glob("*_history.json"))

        if not backups:
            print("No backup files found.")
            # Return empty list to signify no backups found, but no error occurred
            return []
        else:
            print(f"Found {len(backups)} backup file(s).")
            return backups

    except OSError as e:
        logging.error(f"Failed to create or access backup directory {backup_dir}: {e}")
        return None # Indicate an error occurred
    except Exception as e:
        logging.error(f"An unexpected error occurred checking backup existence: {e}")
        return None # Indicate an error occurred


def check_backup_freshness(
    backup_files: list[Path],
    max_age: timedelta = timedelta(days=1)
) -> tuple[bool, Path | None]:
    """
    Checks if the latest backup file in the list is within the maximum allowed age.

    Args:
        backup_files: A list of Path objects for backup files.
        max_age: A timedelta object representing the maximum allowed age
                 for the latest backup (defaults to 1 day).

    Returns:
        A tuple containing:
        - bool: True if a fresh backup exists, False otherwise.
        - Path | None: The path to the latest backup file, or None if no backups
                       were provided or an error occurred during stat.
    """
    if not backup_files:
        # If the input list is empty, there's no backup to check freshness for.
        return False, None

    try:
        # Find the most recent backup file
        latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)

        # Calculate its age
        backup_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
        current_time = datetime.now()
        backup_age = current_time - backup_time

        print(f"Latest backup: {latest_backup.name} - Timestamp: {backup_time} - Age: {backup_age}")

        # Check if the age is within the allowed limit
        is_fresh = backup_age <= max_age
        if not is_fresh:
            print(f"Latest backup is older than the maximum allowed age ({max_age}).")

        return is_fresh, latest_backup

    except FileNotFoundError as e:
        # This could happen if a file is deleted between globbing and stat-ing
        logging.error(f"Error accessing latest backup file {getattr(latest_backup, 'name', 'N/A')}: {e}")
        return False, None
    except Exception as e:
        logging.error(f"Failed to determine backup freshness: {e}")
        return False, None


# Example Usage (replaces the old setup_backup logic):
def setup_and_validate_backup():
    """Checks backup existence and freshness."""
    backup_files = check_backup_existence(app_settings.BACKUP_DIR)

    if backup_files is None:
        print("Backup setup failed due to directory/access error.")
        return False # Indicate failure

    if not backup_files:
        print("Backup check complete: No backups exist.")
        # Depending on requirements, you might want to return False or trigger a backup
        return False # Indicate no usable backup

    # Backups exist, now check freshness
    is_fresh, latest_file = check_backup_freshness(backup_files, max_age=timedelta(days=1))

    if is_fresh:
        print(f"Backup check complete: Recent backup found ({latest_file.name}).")
        return True # Indicate success, backup is ready/recent
    else:
        print("Backup check complete: Backups exist but are too old.")
        return False # Indicate backup is not fresh enough

# Define the suspicious date constant (naive datetime for comparison)
SUSPICIOUS_EPOCH_DATE = datetime(1601, 1, 1, 0, 0, 0)

def get_oldest_entry_in_backups() -> Optional[datetime]:
    """
    Retrieves the oldest valid entry timestamp ('last_visit') across all backup
    JSON files, ignoring the suspicious 1601-01-01 epoch date.

    Scans all .json files in the configured BACKUP_DIR, reads each entry,
    parses the 'last_visit' field, finds the earliest datetime object,
    explicitly skipping entries dated exactly 1601-01-01 00:00:00.

    Returns:
        Optional[datetime]: The datetime object of the oldest valid entry found,
                            or None if no backups or valid non-epoch entries are found.
    """
    backup_files = check_backup_existence(app_settings.BACKUP_DIR)

    if not backup_files:
        logging.warning(f"No backup files found in directory: {app_settings.BACKUP_DIR}")
        return None

    oldest_valid_entry_date: Optional[datetime] = None # Initialize with type hint

    for backup_file_path in backup_files:
        try:
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as json_err:
                    logging.error(f"Error decoding JSON from file {backup_file_path}: {json_err}")
                    continue

                if not isinstance(data, list):
                    logging.warning(f"Backup file {backup_file_path} does not contain a JSON list. Skipping.")
                    continue

                for entry in data:
                    if not isinstance(entry, dict):
                        logging.warning(f"Skipping non-dictionary item in {backup_file_path}: {type(entry)}")
                        continue
                    if 'last_visit' not in entry:
                        logging.warning(f"Skipping entry without 'last_visit' key in {backup_file_path}. Entry: {entry.get('url', 'N/A')}")
                        continue

                    try:
                        entry_date_str = entry['last_visit']
                        # DEBUG: Log the string being parsed if issues persist
                        # logging.debug(f"Attempting to parse date string: '{entry_date_str}' from {backup_file_path}")

                        current_entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d %H:%M:%S')

                        # *** Filter out the suspicious 1601 date ***
                        if current_entry_date == SUSPICIOUS_EPOCH_DATE:
                            logging.debug(f"Ignoring suspicious epoch date ({SUSPICIOUS_EPOCH_DATE}) found in {backup_file_path}. Entry: {entry.get('url', 'N/A')}")
                            continue # Skip this entry

                        # Compare valid dates to find the oldest
                        if oldest_valid_entry_date is None or current_entry_date < oldest_valid_entry_date:
                            oldest_valid_entry_date = current_entry_date

                    except ValueError:
                        logging.warning(f"Could not parse date format for 'last_visit' ('{entry.get('last_visit', '')}') in {backup_file_path}. Entry: {entry.get('url', 'N/A')}")
                        continue
                    except TypeError:
                         logging.warning(f"'last_visit' field is not a string ('{entry.get('last_visit', '')}') in {backup_file_path}. Entry: {entry.get('url', 'N/A')}")
                         continue

        except FileNotFoundError:
             logging.error(f"Backup file {backup_file_path} was not found during processing (unexpected).")
             continue
        except IOError as io_err:
            logging.error(f"IOError reading backup file {backup_file_path}: {io_err}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error processing file {backup_file_path}: {e}", exc_info=True)
            continue

    if oldest_valid_entry_date is None:
        logging.info(f"No valid, non-epoch entries with parsable 'last_visit' dates found in {app_settings.BACKUP_DIR}.")

    return oldest_valid_entry_date

