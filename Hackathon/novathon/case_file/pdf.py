import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os

class CaseFilePDFGenerator:
    def __init__(self, csv_path='case_files_data.csv'):
        """
        Initialize the PDF generator with case files data
        
        :param csv_path: Path to the CSV file containing case files
        """
        self.case_files_df = pd.read_csv(csv_path)
    
    def generate_pdf(self, case_file_id, output_dir=None):
        """
        Generate a PDF for a specific case file
        
        :param case_file_id: Unique identifier for the case file
        :param output_dir: Optional directory to save the PDF (defaults to current directory)
        :return: Path to the generated PDF
        """
        # Find the specific case file
        case_file = self.case_files_df[self.case_files_df['case_file_id'] == case_file_id]
        
        if case_file.empty:
            raise ValueError(f"No case file found with ID {case_file_id}")
        
        # Extract case file details
        case_data = case_file.iloc[0]
        
        # Determine output directory
        if output_dir is None:
            output_dir = os.getcwd()
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output path
        output_path = os.path.join(output_dir, f'case_file_{case_file_id}.pdf')
        
        # Create PDF
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = styles['Title']
        story.append(Paragraph(f"Case File #{case_file_id}", title_style))
        story.append(Spacer(1, 12))
        
        # Heading styles
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Add case details (excluding keywords)
        details = [
            ('Year', case_data['year']),
            ('Criminal Name', case_data['criminal_name']),
            ('Police Station', case_data['police_station']),
            ('Crime Type', case_data['crime_type']),
            ('Case Details', case_data['case_details'])
        ]
        
        for label, value in details:
            story.append(Paragraph(f"{label}:", heading_style))
            story.append(Paragraph(str(value), normal_style))
            story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        
        return output_path

def main():
    # Example usage
    pdf_generator = CaseFilePDFGenerator()
    
    # Loop through all case files and generate PDF for each
    for case_file_id in pdf_generator.case_files_df['case_file_id']:
        try:
            # Generate PDF for each case file
            pdf_path = pdf_generator.generate_pdf(case_file_id)
            print(f"PDF generated successfully for Case File ID {case_file_id}: {pdf_path}")
        
        except ValueError as e:
            print(f"Error for Case File ID {case_file_id}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for Case File ID {case_file_id}: {e}")

if __name__ == "__main__":
    main()
