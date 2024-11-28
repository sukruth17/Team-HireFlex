# novathon/models.py
from django.db import models

class RenamedCaseFile(models.Model):
    case_id = models.CharField(max_length=255, unique=True)  # Case ID (e.g., 827)
    file_path = models.CharField(max_length=500)  # Full path to the renamed file

    def __str__(self):
        return f"Case {self.case_id}: {self.file_path}"

