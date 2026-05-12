"""Bridge between ML/indicators and React Dashboard static JSON."""

import logging
from pathlib import Path
from nepsense.processors.dashboard import generate_dashboard_artifacts
from nepsense.config import DATA_DIR

logger = logging.getLogger(__name__)

def generate_static_json(output_dir: Path = Path("web/dist/data")):
    """Entry point to generate all JSON files for the GitHub Pages dashboard."""
    logger.info(f"Generating static dashboard JSON in {output_dir}...")
    
    # We use the existing dashboard processor but ensure it maps to the user's expected path
    generate_dashboard_artifacts(output_dir)
    
    # We can add more specific 'screener.json' or 'regime.json' if needed here
    logger.info("Static JSON generation complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_static_json()
