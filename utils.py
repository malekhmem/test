import re
import psutil
import logging
import os
def clean_output(output):
    # Remove any non-printable characters and unnecessary symbols
    cleaned_output = re.sub(r'[^ -~\n]+', '', output)  # Remove non-printable characters
    #cleaned_output = re.sub(r'\[.*?\]', '', cleaned_output)  # Remove content within square brackets
    cleaned_output = cleaned_output.strip()  # Remove leading and trailing whitespace
    return cleaned_output

def log_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    logging.debug(f"Memory Usage: {mem_info.rss / 1024 ** 2:.2f} MB")  # Log memory usage in MB
