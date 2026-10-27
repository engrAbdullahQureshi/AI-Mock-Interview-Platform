# Storage abstraction package.
# The app uses MongoDB when MONGODB_URL is set and reachable, otherwise it
# transparently falls back to an in-memory store (see memory_db.py) so the
# whole platform runs locally with only a Groq API key.
