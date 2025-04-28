def log(msg, file="jank_log.txt"):
    """
    Log a message to a file with a timestamp.

    :param msg: The message to log.
    :param file: The file to log the message to.
    """
    with open(file, "a") as f:
        f.write(f"{msg}\n")


def clear(file="jank_log.txt"):
    """
    Clear the log file.

    :param file: The file to clear.
    """
    with open(file, "w") as f:
        f.write("")
