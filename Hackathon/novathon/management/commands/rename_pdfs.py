# novathon/management/commands/rename_pdfs.py
import os
import csv
from django.core.management.base import BaseCommand
from novathon.models import RenamedCaseFile  # Import the model

class Command(BaseCommand):
    help = 'Rename PDFs based on a CSV mapping file containing case data'

    def add_arguments(self, parser):
        # Expecting the CSV file path as an argument
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']
        renamed_folder = 'novathon/renamed_case_files'  # Folder for renamed PDFs
        case_files_folder = 'novathon/case_file'  # Folder with original PDFs

        # Ensure the renamed folder exists
        if not os.path.exists(renamed_folder):
            os.makedirs(renamed_folder)

        # Read the CSV file to get the case data
        try:
            with open(csv_file_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    case_id = row[0].strip()  # Case ID (e.g., 827)
                    year = row[1].strip()  # Year of the case (e.g., 2020)
                    name = row[2].strip()  # Name of the person (e.g., Virginia Burton)
                    case_type = row[4].strip()  # Type of the case (e.g., Fraud)

                    # Construct new PDF name from case data
                    new_pdf_name = f"{case_id}_{year}_{name.replace(' ', '_')}_{case_type}.pdf"

                    # Construct the original PDF filename (case_file_<case_id>.pdf)
                    old_pdf_name = f"case_file_{case_id}.pdf"
                    old_pdf_path = os.path.join(case_files_folder, old_pdf_name)
                    new_pdf_path = os.path.join(renamed_folder, new_pdf_name)

                    if os.path.exists(old_pdf_path):
                        # Rename the file and move it to the renamed folder
                        os.rename(old_pdf_path, new_pdf_path)
                        self.stdout.write(self.style.SUCCESS(f'Renamed: {old_pdf_name} -> {new_pdf_name}'))

                        # Save the case_id and file_path to the database
                        RenamedCaseFile.objects.create(
                            case_id=case_id,
                            file_path=new_pdf_path
                        )
                        self.stdout.write(self.style.SUCCESS(f'Stored in DB: Case {case_id} - {new_pdf_path}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'File not found: {old_pdf_name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
