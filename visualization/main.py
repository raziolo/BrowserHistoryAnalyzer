# visualization/main.py
import sqlite3
from pathlib import Path
import logging
from datetime import datetime
from typing import List, Dict
import jinja2

logger = logging.getLogger(__name__)


class HistoryVisualizer:
    def __init__(self):
        self.output_dir = Path(__file__).resolve().parent / "output"
        self.template_dir = Path(__file__).resolve().parent / "templates"
        self.classified_db = Path(__file__).resolve().parent.parent / "classifier" / "classified" / "classified_history.db"
        print(self.classified_db)
        self._create_output_dir()

        # Configure Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            autoescape=jinja2.select_autoescape()
        )

    def _create_output_dir(self) -> bool:
        """Create output directory if needed"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")
            return False

    def _get_connection(self):
        """Create database connection"""
        return sqlite3.connect(self.classified_db)

    def get_category_distribution(self, browser: str) -> Dict[str, int]:
        """Get category counts for a browser"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM history 
            WHERE browser = ?
            GROUP BY category
            ORDER BY count DESC
        ''', (browser.lower(),))

        results = cursor.fetchall()
        conn.close()

        return {row[0]: row[1] for row in results}

    def get_daily_visits(self, browser: str) -> List[Dict]:
        """Get visits per day for timeline"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row  # Add this line
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DATE(last_visit) as day, COUNT(*) as count
            FROM history
            WHERE browser = ?
            GROUP BY day
            ORDER BY day
        ''', (browser.lower(),))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_recent_history(self, browser: str, limit: int = 10) -> List[Dict]:
        """Get most recent history entries"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT url, title, category, last_visit, visit_count
            FROM history
            WHERE browser = ?
            ORDER BY last_visit DESC
            LIMIT ?
        ''', (browser.lower(), limit))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def generate_dashboard(self) -> Path:
        """Generate interactive HTML dashboard"""
        # Collect data
        chrome_categories = self.get_category_distribution('chrome')
        firefox_categories = self.get_category_distribution('firefox')

        timeline_data = {
            'chrome': self.get_daily_visits('chrome'),
            'firefox': self.get_daily_visits('firefox'),
        }

        recent_history = {
            'chrome': self.get_recent_history('chrome'),
            'firefox': self.get_recent_history('firefox'),
        }

        # Prepare chart data
        chart_data = {
            'chrome_labels': list(chrome_categories.keys()),
            'chrome_values': list(chrome_categories.values()),
            'firefox_labels': list(firefox_categories.keys()),
            'firefox_values': list(firefox_categories.values()),
            'timeline_labels': sorted(
                list({entry['day'] for entry in timeline_data['chrome'] + timeline_data['firefox']})),
            'chrome_timeline': [entry['count'] for entry in timeline_data['chrome']],
            'firefox_timeline': [entry['count'] for entry in timeline_data['firefox']],
        }

        # Render template
        template = self.env.get_template('dashboard.html')
        html_content = template.render(
            generated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            chart_data=chart_data,
            recent_history=recent_history,
            total_entries={
                'chrome': sum(chrome_categories.values()),
                'firefox': sum(firefox_categories.values())
            }
        )

        # Save output
        output_path = self.output_dir / "browsing_dashboard.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Dashboard generated at: {output_path}")
        return output_path


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    visualizer = HistoryVisualizer()
    visualizer.generate_dashboard()