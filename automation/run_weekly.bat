@echo off
cd /d "%~dp0"
python fetch_news.py
python ../research/synthesize_research.py