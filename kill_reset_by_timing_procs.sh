ps aux | grep "[p]ython3 fix_scraping_state__reset_by_timing.py" | awk '{print $2}' | xargs kill
