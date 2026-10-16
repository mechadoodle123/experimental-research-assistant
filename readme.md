# 1. Clean and validate data
python3 src/clean.py
python3 src/validate.py

# 2. Run unit and pipeline tests
python3 test/test_pipeline.py

# 3. Load database (if not automated in clean)
python3 src/load_db.py

# 4. Launch research assistant
python3 src/assistant.py