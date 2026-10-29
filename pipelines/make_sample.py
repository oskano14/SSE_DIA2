"""Génère data/sample/ à partir des données complètes (data/raw/).

Lancement : uv run python pipelines/make_sample.py
"""

from shoppulse.config import SAMPLE_DIR, raw_dir
from shoppulse.etl.sample import make_sample

if __name__ == "__main__":
    print(make_sample(raw_dir(), SAMPLE_DIR))
