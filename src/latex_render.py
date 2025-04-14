import os
import subprocess
import uuid
import tempfile
import shutil
import re
from pdf2image import convert_from_path

class LatexError(Exception):
    """Custom exception for LaTeX-related errors"""
    pass

def clean_latex_string(latex_string):
    """
    Clean the LaTeX string by handling markdown code blocks and ensuring proper equation environment.
    
    Args:
        latex_string (str): The raw LaTeX string that might contain markdown code blocks
        
    Returns:
        str: Cleaned LaTeX string
    """
    # Split the string into lines
    lines = latex_string.split('\n')
    cleaned_lines = []
    
    # Track if we're in a markdown code block
    in_code_block = False
    code_block_content = []
    
    for line in lines:
        # Check for start of markdown code block
        if line.strip().startswith('```latex'):
            in_code_block = True
            continue
        # Check for end of markdown code block
        elif line.strip() == '```' and in_code_block:
            in_code_block = False
            # Process the code block content
            content = '\n'.join(code_block_content)
            # Check if it already has an equation environment
            if not re.search(r'\\begin\{equation\}|\$', content):
                content = f"\\begin{{equation}}\n{content}\n\\end{{equation}}"
            cleaned_lines.append(content)
            code_block_content = []
            continue
        
        if in_code_block:
            code_block_content.append(line)
        else:
            # Convert markdown bold and italic to LaTeX
            line = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', line)  # Bold text
            cleaned_lines.append(line)
    
    # Join the lines back together
    cleaned_string = '\n'.join(cleaned_lines)
    
    return cleaned_string.strip()

def check_latex_installation():
    """Check if pdflatex is installed and accessible"""
    try:
        subprocess.run(['pdflatex', '--version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def render_latex(latex_string, output_dir):
    """
    Renders LaTeX content to a PDF file.
    
    Args:
        latex_string (str): The LaTeX content to render
        output_dir (str): Directory to save the output files
        
    Returns:
        str: Path to the generated PDF file
    
    Raises:
        LatexError: If LaTeX compilation fails
    """
    if not check_latex_installation():
        raise LatexError("pdflatex is not installed or not accessible")

    # Clean the LaTeX string
    latex_string = clean_latex_string(latex_string)

    # Ensure the output folder exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate a unique filename
    filename = str(uuid.uuid4())
    
    # Use a temporary directory for compilation
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file_path = os.path.join(temp_dir, filename + '.tex')
        
        # Create a complete LaTeX document
        document = f"""\\documentclass[preview,border=5pt]{{standalone}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{physics}}
\\begin{{document}}
{latex_string}
\\end{{document}}
"""
        
        try:
            # Write LaTeX content to file
            with open(tex_file_path, 'w') as f:
                f.write(document)
            
            # Run pdflatex
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', tex_file_path],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            temp_pdf_path = os.path.join(temp_dir, filename + '.pdf')
            if not os.path.exists(temp_pdf_path):
                raise LatexError("PDF file was not generated")
            
            # Copy the PDF to output directory
            output_pdf_path = os.path.join(output_dir, filename + '.pdf')
            shutil.copy2(temp_pdf_path, output_pdf_path)
            
            return output_pdf_path
            
        except subprocess.CalledProcessError as e:
            raise LatexError(f"LaTeX compilation failed: {e.stdout}\n{e.stderr}")
        except Exception as e:
            raise LatexError(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    # Example usage
    latex_string = r"""Consider the mean-field Hamiltonian: $H = H_{\text{Kinetic}} + H_{\text{Hartree}} +H_{\text{Fock}}$, with each term defined below:

$H_{\text{Kinetic}} = \sum_{s, k} E_s(k) c^\dagger_s(k) c_s(k)$, where $E_s(k)=\sum_{n} t_s(n) e^{-i k \cdot n}$

$H_{\text{Hartree}} = \frac{1}{N} \sum_{s, s'} \sum_{k_1, k_2} U(0) \langle c_s^\dagger(k_1) c_s(k_1) \rangle c_{s'}^\dagger(k_2) c_{s'}(k_2)$"""
    render_latex(latex_string, "output")