# novathon/management/commands/stored_name_pdfs.py

from django.core.management.base import BaseCommand
import os
from novathon.models import RenamedCaseFile

class Command(BaseCommand):
    help = 'Store renamed PDFs and their file paths into the database'

    def handle(self, *args, **kwargs):
        renamed_folder = 'novathon/renamed_case_files'  # Folder with renamed PDFs
        renamed_files = os.listdir(renamed_folder)  # Get all the files in the folder

        for file_name in renamed_files:
            # Construct the full path to the renamed file
            file_path = os.path.join(renamed_folder, file_name)

            # Normalize the path to use forward slashes
            file_path = file_path.replace(os.sep, '/')

            # Extract the case_id from the file name (assuming it's the first part before '_')
            case_id = file_name.split('_')[0]

            try:
                # Store the case_id and file_path in the database
                RenamedCaseFile.objects.create(case_id=case_id, file_path=file_path)
                self.stdout.write(self.style.SUCCESS(f'Stored {file_name} with case_id {case_id} and path {file_path}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {file_name}: {e}'))
