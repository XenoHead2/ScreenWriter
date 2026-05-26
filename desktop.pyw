import webview
import os
import json
import subprocess
import sys
from datetime import datetime

def run_dialog_script(script):
    # Use python.exe to ensure stdout capture works, but flag it to hide the console window!
    python_exe = sys.executable
    if python_exe.endswith('pythonw.exe'):
        python_exe = python_exe.replace('pythonw.exe', 'python.exe')
        
    creationflags = 0
    if os.name == 'nt':
        creationflags = 0x08000000  # CREATE_NO_WINDOW
        
    try:
        result = subprocess.check_output(
            [python_exe, '-c', script],
            text=True,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        ).strip()
        return result if result and result != "None" else None
    except Exception:
        return None

class BackendAPI:
    def __init__(self):
        # Set up a default backup directory in the user's Documents folder
        self.backup_dir = os.path.join(os.path.expanduser("~"), "Documents", "KindredScript")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
        self.settings_file = os.path.join(self.backup_dir, "settings.json")
        
    def load_settings(self):
        settings = {}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
            except Exception:
                pass
        return settings

    def save_settings(self, settings):
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            return False

    def _safe_save_dialog(self, default_name, ext, filetypes):
        safe_name = "".join(c for c in default_name if c not in r'\/:*?"<>|')
        ft_str = str(filetypes)
        script = f"""
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
file = filedialog.asksaveasfilename(
    parent=root, 
    title="Export Screenplay",
    initialfile="{safe_name}",
    defaultextension="{ext}",
    filetypes={ft_str}
)
print(file)
"""
        return run_dialog_script(script)

    def save_project_dialog(self, content, project_name="Untitled Project"):
        safe_name = "".join(c for c in project_name if c not in r'\/:*?"<>|')
        script = f"""
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
file = filedialog.asksaveasfilename(
    parent=root, 
    title="Save Project",
    initialfile="{safe_name}.ksp",
    defaultextension=".ksp",
    filetypes=[('KindredScript Project', '*.ksp')]
)
print(file)
"""
        filepath = run_dialog_script(script)
        if filepath and filepath != "None":
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                return filepath
            except Exception as e:
                return f"Error: {str(e)}"
        return None

    def open_project_dialog(self):
        script = """
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
file = filedialog.askopenfilename(
    parent=root, 
    title="Open Project",
    filetypes=[('KindredScript Project', '*.ksp')]
)
print(file)
"""
        filepath = run_dialog_script(script)
        if filepath and filepath != "None" and os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return {'filepath': filepath, 'data': f.read()}
            except Exception as e:
                return {'error': str(e)}
        return None

    def open_recent_project(self, filepath):
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return {'filepath': filepath, 'data': f.read()}
            except Exception as e:
                return {'error': str(e)}
        return {'error': 'File not found.'}

    def choose_directory(self):
        script = """
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
folder = filedialog.askdirectory(parent=root, title="Select Backup Folder")
print(folder)
"""
        return run_dialog_script(script)

    def open_file_dialog(self):
        script = """
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
file = filedialog.askopenfilename(
    parent=root, 
    title="Import Screenplay",
    filetypes=[('Supported Documents', '*.txt *.html *.pdf *.fountain *.fdx'), ('All Files', '*.*')]
)
print(file)
"""
        filepath = run_dialog_script(script)
        if filepath and os.path.exists(filepath):
            ext = filepath.split('.')[-1].lower()
            try:
                import base64
                with open(filepath, 'rb') as f:
                    return {'ext': ext, 'data': base64.b64encode(f.read()).decode('utf-8')}
            except Exception as e:
                return {'error': str(e)}
        return None

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)
        return True

    def save_backup(self, content, cloud_path=None, local_path=None, project_name="AutoBackup"):
        """This is called directly from JavaScript, bypassing web browser security."""
        try:
            messages = []
            
            project_name = project_name or "AutoBackup"
            safe_name = "".join(c for c in project_name if c not in r'\/:*?"<>|')
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{safe_name}_Backup_{timestamp}.html"
            
            # Local Backup
            actual_local = self.backup_dir
            if local_path and os.path.exists(local_path):
                actual_local = local_path
                
            try:
                local_filepath = os.path.join(actual_local, filename)
                with open(local_filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                messages.append("Local")
            except Exception:
                pass
                    
            # Cloud Backup
            if cloud_path and os.path.exists(cloud_path):
                try:
                    cloud_filepath = os.path.join(cloud_path, filename)
                    with open(cloud_filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    messages.append("Cloud")
                except Exception:
                    pass

            if messages:
                return f"Natively Backed Up: {' & '.join(messages)}"
            return "Backup Failed or No Paths Found"
        except Exception as e:
            return f"Error: {str(e)}"

    def export_pdf(self, lines, project_name="Screenplay"):
        """Opens a native save dialog and generates a formatted PDF."""
        filepath = self._safe_save_dialog(f'{project_name}.pdf', '.pdf', [('PDF Files', '*.pdf')])
        if not filepath:
            return "Export cancelled."
        
        try:
            import fpdf
        except ImportError:
            return "Missing library. Please run: pip install fpdf"
            
        try:
            pdf = fpdf.FPDF(unit='in', format='Letter')
            pdf.add_page()
            pdf.set_margins(left=1.5, top=1.0, right=1.0)
            pdf.set_auto_page_break(auto=True, margin=1.0)
            pdf.set_font("Courier", size=12)
            
            for line in lines:
                ltype = line.get('type', 'action')
                text = line.get('text', '').replace('\u200b', '').strip()
                
                # Sanitize common unicode characters that break basic FPDF encoding
                text = text.replace('\u2018', "'").replace('\u2019', "'")
                text = text.replace('\u201c', '"').replace('\u201d', '"')
                text = text.replace('\u2013', '-').replace('\u2014', '--')
                text = text.replace('\u2026', '...')
                text = text.encode('latin-1', 'replace').decode('latin-1')
                
                if not text:
                    pdf.ln(0.16)
                    continue

                current_y = pdf.get_y()
                if line.get('revision', False):
                    pdf.set_font("Courier", style='B', size=12)
                    pdf.set_xy(7.6, current_y)
                    pdf.cell(w=0.2, h=0.16, txt="*")
                    pdf.set_y(current_y) # reset Y so the main line prints correctly
                    pdf.set_font("Courier", style='', size=12)

                if ltype == 'page-break':
                    pdf.add_page()
                    continue
                    
                if ltype == 'scene-heading':
                    pdf.set_x(1.5); pdf.multi_cell(w=6.0, h=0.16, txt=text.upper()); pdf.ln(0.16)
                elif ltype == 'character':
                    pdf.set_x(3.5); pdf.multi_cell(w=4.0, h=0.16, txt=text.upper())
                elif ltype == 'parenthetical':
                    text = text.replace('(', '').replace(')', '')
                    pdf.set_x(3.1); pdf.multi_cell(w=2.5, h=0.16, txt=f"({text})")
                elif ltype == 'dialogue':
                    pdf.set_x(2.5); pdf.multi_cell(w=3.5, h=0.16, txt=text); pdf.ln(0.16)
                elif ltype == 'transition':
                    pdf.set_x(5.5); pdf.multi_cell(w=2.0, h=0.16, txt=text.upper()); pdf.ln(0.16)
                else: # Action, Shot, etc.
                    pdf.set_x(1.5); pdf.multi_cell(w=6.0, h=0.16, txt=text); pdf.ln(0.16)
                    
            pdf.output(filepath)
            return f"Exported to: {filepath}"
        except Exception as e:
            return f"Export Error: {str(e)}"

    def export_fdx(self, lines, project_name="Screenplay"):
        """Opens a native save dialog and generates a Final Draft (.fdx) file."""
        filepath = self._safe_save_dialog(f'{project_name}.fdx', '.fdx', [('Final Draft Files', '*.fdx')])
        if not filepath:
            return "Export cancelled."
            
        try:
            import xml.etree.ElementTree as ET
            root = ET.Element("FinalDraft", DocumentType="Script", Template="No", Version="1")
            content = ET.SubElement(root, "Content")
            type_map = {'scene-heading': 'Scene Heading', 'action': 'Action', 'character': 'Character', 'parenthetical': 'Parenthetical', 'dialogue': 'Dialogue', 'transition': 'Transition', 'shot': 'Shot'}
            
            for line in lines:
                ltype = line.get('type', 'action')
                text = line.get('text', '').replace('\u200b', '').strip()
                
                if ltype == 'page-break':
                    p = ET.SubElement(content, "Paragraph", Type="Action")
                    p.set("PageBreak", "Yes")
                    ET.SubElement(p, "Text").text = ""
                    continue

                if not text:
                    ET.SubElement(ET.SubElement(content, "Paragraph", Type="Action"), "Text").text = ""
                    continue
                if ltype == 'parenthetical': text = f"({text.replace('(', '').replace(')', '')})"
                elif ltype in ['scene-heading', 'character', 'transition']: text = text.upper()
                
                ET.SubElement(ET.SubElement(content, "Paragraph", Type=type_map.get(ltype, 'Action')), "Text").text = text
                
            xmlstr = ET.tostring(root, encoding='utf-8', method='xml')
            with open(filepath, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n' + xmlstr)
            return f"Exported to: {filepath}"
        except Exception as e:
            return f"Export Error: {str(e)}"

    def export_writersduet(self, lines, project_name="Screenplay"):
        """Opens a native save dialog and generates a WriterDuet-compatible Fountain file."""
        filepath = self._safe_save_dialog(f'{project_name}.fountain', '.fountain', [('WriterDuet/Fountain Files', '*.fountain')])
        if not filepath:
            return "Export cancelled."
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for line in lines:
                    ltype = line.get('type', 'action')
                    text = line.get('text', '').replace('\u200b', '').strip()
                    if not text: f.write('\n'); continue
                    if ltype == 'page-break': f.write('===\n\n')
                    if ltype == 'scene-heading': f.write(text.upper() + '\n\n')
                    elif ltype == 'character': f.write(text.upper() + '\n')
                    elif ltype == 'parenthetical': f.write(f"({text.replace('(', '').replace(')', '')})\n")
                    elif ltype == 'dialogue': f.write(text + '\n\n')
                    elif ltype == 'transition': f.write('> ' + text.upper() + '\n\n')
                    else: f.write(text + '\n\n')
            return f"Exported to: {filepath}"
        except Exception as e:
            return f"Export Error: {str(e)}"

if __name__ == '__main__':
    api = BackendAPI()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, 'index.html')
    
    webview.create_window('KindredScript Pro', url=html_path, js_api=api, width=1280, height=800)
    webview.start()