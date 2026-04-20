Face Recognition Matching System (Consent-Based)

Run:
uvicorn main:app --reload

Endpoints:
- POST /add (person_id + image)
- POST /search (image)

Note:
This system assumes consent-based datasets only.
Do not use on unauthorized or public scraping sources.