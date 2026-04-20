import time

def log_event(event_type, user):
    print(f"[LOG] {event_type} - {user} - {time.time()}")