import time
import random

def human_type_string(element, text_string):
    """
    Simulates realistic human typing text entry loops with variable keystroke delay parameters.
    Bypasses standard React client-side form value truncation safeguards.
    """
    element.click()
    element.press("Control+A")
    element.press("Delete")
    time.sleep(0.2)
    
    for character in text_string:
        element.type(character)
        # Inject a randomized delay step to mimic human hands (50ms - 180ms)
        time.sleep(random.uniform(0.05, 0.18))
