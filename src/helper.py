from threading import Thread, Semaphore
from functools import wraps

def limit(number):
    sem = Semaphore(number)
    def wrapper(func):
        @wraps(func)
        def wrapped(*args):
            with sem:
                return func(*args)
        return wrapped
    return wrapper

def run_in_thread(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    
    return wrapper