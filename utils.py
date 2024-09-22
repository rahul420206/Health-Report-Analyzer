import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re

def parse_pdf_with_pdfplumber(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text if text else None
    except Exception as e:
        print(f"Error parsing PDF with pdfplumber: {e}")
        return None

def parse_pdf_with_ocr(pdf_path):
    try:
        images = convert_from_path(pdf_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text.strip()  
    except Exception as e:
        print(f"Error parsing PDF with OCR: {e}")
        return None

def extract_key_points(text):
    """Refined key points extraction with numerical values."""
    sentences = re.split(r'(?<!\b[A-Z])\.(?![A-Z]\b)', text)
    key_points = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:
            
            matches = re.findall(r'\d+\.?\d*', sentence)
            if matches:
               
                key_points.append(sentence.replace(matches[0], f"**{matches[0]}**"))
            else:
               
                key_points.append(sentence)
    return key_points

def extract_test_results(text):
    test_results = []
    pattern = re.compile(r"(?P<test_name>[A-Za-z ]+)\s*(?P<value>[0-9\.]+)\s*(?P<reference_range>[0-9\-\.%]+)")
    matches = pattern.finditer(text)
    for result in matches:  
        test_name = result['test_name']
        value = result['value']
        reference_range = result['reference_range'] 

        if reference_range:
            try:
                low_limit, high_limit = map(float, reference_range.split('-'))
                test_results.append((test_name, value, reference_range, low_limit, high_limit))
            except ValueError:
                print(f"Warning: Invalid reference range '{reference_range}' for test '{test_name}'")
                continue 
        else:
            print(f"Warning: Empty reference range for test '{test_name}'")
    
    return test_results

def extract_text_from_pdf(pdf_path):
    text = parse_pdf_with_pdfplumber(pdf_path)
    
    if text is None or len(text.strip()) == 0:
        print("PDF parsing failed or resulted in empty text. Falling back to OCR...")
        
        text = parse_pdf_with_ocr(pdf_path)

    if text is not None and len(text.strip()) > 0:
        return text
    else:
        print("Failed to extract text from the PDF.")
        return None

def render_test_results_html(test_results):
    html_content = """
    <html>
    <head><title>Test Results</title></head>
    <body>
    <h1>Test Results</h1>
    <table border="1">
    <tr>
        <th>Test Name</th>
        <th>Value</th>
        <th>Reference Range</th>
    </tr>"""

    for test, value, reference_range in test_results:
        html_content += f"""
        <tr>
            <td>{test}</td>
            <td>{value}</td>
            <td>{reference_range}</td>
        </tr>"""

    html_content += """
    </table>
    </body>
    </html>
    """

    return html_content

if __name__ == "__main__":
    pdf_path = "path_to_your_blood_report.pdf"
    
    extracted_text = extract_text_from_pdf(pdf_path)
    
    if extracted_text:
        test_results = extract_test_results(extracted_text)

        if test_results:
            html_output = render_test_results_html(test_results)
        
            with open("test_results.html", "w") as html_file:
                html_file.write(html_output)
            print("Test results have been written to test_results.html")
        else:
            print("No test results found in the extracted text.")
    else:
        print("Failed to extract text from the PDF.")
