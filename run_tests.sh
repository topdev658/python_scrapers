rm logs/tests*

# '*' mask not allowed for graceful shutdown of each test
python3 -m unittest tests/kutxa_scraper_tests.py >> logs/tests.out.log 2>> logs/tests.err.log
python3 -m unittest tests/santander_scraper_tests.py >> logs/tests.out.log 2>> logs/tests.err.log