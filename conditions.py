import functools

def condition(pre_condition=None, post_condition=None):
    def decorator(func):
        @functools.wraps(func) # presever name, docstring, etc
        def wrapper(*args, **kwargs): #NOTE: no self
            if pre_condition is not None:
               if not pre_condition(*args, **kwargs):
                   return None
            retval = func(*args, **kwargs) # call original function or method
            if post_condition is not None:
               assert post_condition(retval)
            return retval
        return wrapper
    return decorator

def pre_condition(check):
    return condition(pre_condition=check)

def post_condition(check):
    return condition(post_condition=check)
