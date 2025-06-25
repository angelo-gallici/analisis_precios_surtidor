"""
Input/Output classes and methods.
"""
import re
from os.path import exists


class FileName:
    """
    A file name and it's components.
    """

    name: str
    extension: str
    full_name: str

    def __init__(self, file_name: str):
        exp = r"^([\w\.\-]*)(\.)([a-zA-Z0-9]{1,4}$)"
        search = re.search(exp, file_name)
        if search is None:
            self.name = file_name
            self.full_name = file_name
            self.extension = ""
        else:
            self.name = search.group(1)
            self.extension = search.group(3)
            self.full_name = self.name + "." + self.extension

    def __str__(self):
        ext = "" if self.extension in [None, ""] else f".{self.extension}"
        return f"{self.name}{ext}"

    def exists(self):
        """
        Check if the file exists locally.
        """
        return exists(self.full_name)