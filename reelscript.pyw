import webview
import os
import json
import subprocess
import sys
from datetime import datetime

if len(sys.argv) > 2 and sys.argv[1] == '--run-dialog':
    exec(sys.argv[2])
    sys.exit(0)

# Ensure the script's directory is in the Python path to find local modules like 'editor.py'
if getattr(sys, 'frozen', False):
    current_dir = sys._MEIPASS
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import editor  # type: ignore

def run_dialog_script(script):
    import tempfile
    fd, temp_path = tempfile.mkstemp(suffix='.txt')
    os.close(fd)
    
    safe_script = f"""
import sys
def print(*args, **kwargs):
    with open(r'''{temp_path}''', 'w', encoding='utf-8') as _temp_f:
        _temp_f.write(" ".join(str(a) for a in args))
""" + script

    python_exe = sys.executable
    if hasattr(sys, 'frozen'):
        cmd = [python_exe, '--run-dialog', safe_script]
    else:
        if python_exe.endswith('pythonw.exe'):
            python_exe = python_exe.replace('pythonw.exe', 'python.exe')
        cmd = [python_exe, '-c', safe_script]
        
    creationflags = 0
    if os.name == 'nt':
        creationflags = 0x08000000  # CREATE_NO_WINDOW
        
    try:
        subprocess.check_call(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        )
        with open(temp_path, 'r', encoding='utf-8') as f:
            result = f.read().strip()
        os.remove(temp_path)
        return result if result and result != "None" and result != "" else None
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except: pass
        return None

class BackendAPI:
    def __init__(self):
        # Set up a default backup directory in the user's Documents folder
        self.backup_dir = os.path.join(os.path.expanduser("~"), "Documents", "ReelScript")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
        self.settings_file = os.path.join(self.backup_dir, "settings.json")
        self.personal_dict = set()
        self.spell = None
        
    def load_settings(self):
        settings = {}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
            except Exception:
                pass
        if settings.get("geminiApiKey"):
            os.environ["GEMINI_API_KEY"] = settings.get("geminiApiKey")
        return settings

    def save_settings(self, settings):
        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=4)
            if settings.get("geminiApiKey"):
                os.environ["GEMINI_API_KEY"] = settings.get("geminiApiKey")
            return True
        except Exception as e:
            return False

    def set_api_key(self, api_key):
        os.environ["GEMINI_API_KEY"] = api_key
        return True

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
title="Save Project As",
initialfile="{safe_name}.rsp",
defaultextension=".rsp",
filetypes=[('ReelScript Project', '*.rsp'), ('Legacy KindredScript Project', '*.ksp')]
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

    def save_project(self, content, filepath):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return filepath
        except Exception as e:
            return f"Error: {str(e)}"
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
    filetypes=[('ReelScript Project', '*.rsp'), ('Legacy KindredScript Project', '*.ksp'), ('All Files', '*.*')]
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

    def _enforce_backup_limit(self, directory, prefix, max_backups):
        if not directory or not os.path.exists(directory) or max_backups <= 0:
            return
        try:
            files = []
            for f in os.listdir(directory):
                if f.startswith(prefix) and f.endswith(".html"):
                    full_path = os.path.join(directory, f)
                    if os.path.isfile(full_path):
                        files.append((full_path, os.path.getmtime(full_path)))
            files.sort(key=lambda x: x[1])
            if len(files) > max_backups:
                for i in range(len(files) - max_backups):
                    os.remove(files[i][0])
        except Exception:
            pass

    def save_backup(self, content, cloud_path=None, local_path=None, project_name="AutoBackup", max_backups=5):
        """This is called directly from JavaScript, bypassing web browser security."""
        try:
            messages = []
            
            project_name = project_name or "AutoBackup"
            safe_name = "".join(c for c in project_name if c not in r'\/:*?"<>|')
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{safe_name}_Backup_{timestamp}.html"
            prefix = f"{safe_name}_Backup_"
            
            # Local Backup
            actual_local = self.backup_dir
            if local_path and os.path.exists(local_path):
                actual_local = local_path
                
            try:
                local_filepath = os.path.join(actual_local, filename)
                with open(local_filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self._enforce_backup_limit(actual_local, prefix, max_backups)
                messages.append("Local")
            except Exception:
                pass
                    
            # Cloud Backup
            if cloud_path and os.path.exists(cloud_path):
                try:
                    project_cloud_dir = os.path.join(cloud_path, safe_name)
                    if not os.path.exists(project_cloud_dir):
                        os.makedirs(project_cloud_dir)
                        
                    cloud_filepath = os.path.join(project_cloud_dir, filename)
                    with open(cloud_filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    self._enforce_backup_limit(project_cloud_dir, prefix, max_backups)
                    messages.append("Cloud")
                except Exception:
                    pass

            if messages:
                return f"Natively Backed Up: {' & '.join(messages)}"
            return "Backup Failed or No Paths Found"
        except Exception as e:
            return f"Error: {str(e)}"

    def export_pdf(self, lines, project_name="Screenplay", export_config=None):
        if export_config is None:
            export_config = {}
            
        """Opens a native save dialog and generates a formatted PDF."""
        filepath = self._safe_save_dialog(f'{project_name}.pdf', '.pdf', [('PDF Files', '*.pdf')])
        if not filepath:
            return "Export cancelled."
        
        try:
            import fpdf
        except ImportError:
            return "Missing library. Please run: pip install fpdf"
            
        try:
            show_numbers = export_config.get("showPageNumbers", False)
            start_page = export_config.get("startPageNumber", 2)
            title_lines = export_config.get("titleLines", [])

            class ScreenplayPDF(fpdf.FPDF):
                def __init__(self, show_page_numbers=False, start_page=2):
                    super().__init__(unit='in', format='Letter')
                    self.show_page_numbers = show_page_numbers
                    self.current_script_page = start_page
                    self.in_title_page = True

                def header(self):
                    if not self.in_title_page and self.show_page_numbers:
                        self.set_font("Courier", size=12)
                        self.set_xy(7.0, 0.5)
                        self.cell(w=0.5, h=0.16, txt=f"{self.current_script_page}.", align='R')  # type: ignore
                        self.current_script_page += 1
                    self.set_margins(left=1.5, top=1.0, right=1.0)
                    self.set_xy(1.5, 1.0)

            pdf = ScreenplayPDF(show_page_numbers=show_numbers, start_page=start_page)
            pdf.set_margins(left=1.5, top=1.0, right=1.0)
            pdf.set_auto_page_break(auto=True, margin=1.0)
            
            def hex_to_rgb(h_color):
                try:
                    h_color = h_color.lstrip('#')
                    return tuple(int(h_color[i:i+2], 16) for i in (0, 2, 4))
                except:
                    return (0, 0, 0)

            def sanitize_text(t):
                t = t.replace('\u2018', "'").replace('\u2019', "'")
                t = t.replace('\u201c', '"').replace('\u201d', '"')
                t = t.replace('\u2013', '-').replace('\u2014', '--')
                t = t.replace('\u2026', '...')
                return t.encode('latin-1', 'replace').decode('latin-1')

            if title_lines:
                pdf.add_page()
                pdf.set_font("Courier", size=12)
                
                # Vertical centering logic
                total_lines = len(title_lines)
                if total_lines > 0:
                    # If user manually added blank lines at the top, trust their spacing
                    first_line_text = title_lines[0].get('text', '').replace('\u200b', '').strip()
                    if first_line_text != '':
                        start_y = max(1.0, (11.0 - (total_lines * 0.16)) / 2.0)
                    else:
                        start_y = 1.0 
                    pdf.set_y(start_y)
                
                for line in title_lines:
                    text = line.get('text', '').replace('\u200b', '').strip()
                    text = sanitize_text(text)
                    align_char = line.get('align', 'C')
                    
                    if not text:
                        pdf.ln(0.16)
                    else:
                        pdf.set_x(1.5)
                    pdf.multi_cell(w=5.5, h=0.16, txt=text, align=align_char)  # type: ignore

            pdf.in_title_page = False
            pdf.add_page()
            pdf.set_font("Courier", size=12)
            
            last_type = None

            for line in lines:
                ltype = line.get('type', 'action')
                text = line.get('text', '').replace('\u200b', '').strip()
                
                text = sanitize_text(text)

                if ltype == 'page-break':
                    pdf.add_page()
                    last_type = None
                    continue

                if not text:
                    # Ignore empty editor lines to enforce strict standard screenplay spacing mathematically
                    continue

                # Smart vertical formatting: 1 blank line before everything except Dialogue & Parentheticals
                needs_space = False
                if last_type is not None:
                    if ltype not in ['dialogue', 'parenthetical']:
                        needs_space = True
                        
                if needs_space and pdf.get_y() > 1.1:
                    pdf.ln(0.16)

                current_y = pdf.get_y()
                if line.get('revision', False):
                    rev_color = line.get('revColor', '#ef4444')
                    r_val, g_val, b_val = hex_to_rgb(rev_color)
                    
                    pdf.set_font("Courier", style='B', size=12)
                    pdf.set_text_color(r_val, g_val, b_val)
                    pdf.set_xy(7.6, current_y)
                    pdf.cell(w=0.2, h=0.16, txt="*")  # type: ignore
                    pdf.set_y(current_y) # reset Y so the main line prints correctly
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Courier", style='', size=12)

                if ltype == 'scene-heading':
                    pdf.set_x(1.5); pdf.multi_cell(w=6.0, h=0.16, txt=text.upper())  # type: ignore
                elif ltype == 'character':
                    pdf.set_x(3.5); pdf.multi_cell(w=4.0, h=0.16, txt=text.upper())  # type: ignore
                elif ltype == 'parenthetical':
                    text = text.replace('(', '').replace(')', '')
                    pdf.set_x(3.1); pdf.multi_cell(w=2.5, h=0.16, text=f"({text})")  # type: ignore
                elif ltype == 'dialogue':
                    pdf.set_x(2.5); pdf.multi_cell(w=3.5, h=0.16, txt=text)  # type: ignore
                elif ltype == 'transition':
                    pdf.set_x(5.5); pdf.multi_cell(w=2.0, h=0.16, txt=text.upper())  # type: ignore
                else: # Action, Shot, etc.
                    pdf.set_x(1.5); pdf.multi_cell(w=6.0, h=0.16, txt=text)  # type: ignore
                
                last_type = ltype

            pdf.output(filepath)
            return f"Exported to: {filepath}"
        except Exception as e:
            return f"Export Error: {str(e)}"

    def export_fdx(self, lines, project_name="Screenplay", export_config=None):
        if export_config is None:
            export_config = {}
            
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

    def export_writersduet(self, lines, project_name="Screenplay", export_config=None):
        if export_config is None:
            export_config = {}
            
        """Opens a native save dialog and generates a WriterDuet-compatible Fountain file."""
        filepath = self._safe_save_dialog(f'{project_name}.fountain', '.fountain', [('WriterDuet/Fountain Files', '*.fountain')])
        if not filepath:
            return "Export cancelled."
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for line in lines:
                    ltype = line.get('type', 'action')
                    text = line.get('text', '').replace('\u200b', '').strip()
                    
                    if not text: 
                        continue
                        
                    if ltype == 'page-break': f.write('===\n\n')
                    elif ltype == 'scene-heading': f.write(text.upper() + '\n\n')
                    elif ltype == 'character': f.write(text.upper() + '\n')
                    elif ltype == 'parenthetical': f.write(f"({text.replace('(', '').replace(')', '')})\n")
                    elif ltype == 'dialogue': f.write(text + '\n\n')
                    elif ltype == 'transition': f.write('> ' + text.upper() + '\n\n')
                    else: f.write(text + '\n\n')
            return f"Exported to: {filepath}"
        except Exception as e:
            return f"Export Error: {str(e)}"

    def get_spell_suggestions(self, word):
        try:
            from spellchecker import SpellChecker  # type: ignore
            from spellchecker import SpellChecker  # type: ignore
        except ImportError:
            return {"error": "Please run: pip install pyspellchecker"}
            
        if self.spell is None:
            self.spell = SpellChecker()
            dict_path = os.path.join(self.backup_dir, "personal_dict.txt")
            if os.path.exists(dict_path):
                with open(dict_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        w = line.strip().lower()
                        if w:
                            self.personal_dict.add(w)
            self.spell.word_frequency.load_words(list(self.personal_dict))

        import re
        word_clean = re.sub(r'[^\w\s]', '', word.lower())
        if not word_clean:
            return {"misspelled": False, "suggestions": []}

        if word_clean in self.personal_dict or word_clean in self.spell:
            return {"misspelled": False, "suggestions": []}
            
        candidates = self.spell.candidates(word_clean)
        cand_list = []
        if candidates:
            cand_list = list(candidates)[:5]
            if word[0].isupper():
                cand_list = [c.capitalize() for c in cand_list]
        return {"misspelled": True, "suggestions": cand_list}

    def check_document_spelling(self, text):
        try:
            from spellchecker import SpellChecker
        except ImportError:
            return {"error": "Please run: pip install pyspellchecker"}
            
        if self.spell is None:
            self.spell = SpellChecker()
            dict_path = os.path.join(self.backup_dir, "personal_dict.txt")
            if os.path.exists(dict_path):
                with open(dict_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        w = line.strip().lower()
                        if w: self.personal_dict.add(w)
            self.spell.word_frequency.load_words(list(self.personal_dict))

        import re
        words = re.findall(r"\b[a-zA-Z\']+\b", text)
        unique_words = list(dict.fromkeys(words)) # Removes duplicates while preserving order
        
        misspelled = []
        for w in unique_words:
            w_clean = re.sub(r'[^\w\s]', '', w.lower())
            if not w_clean or w_clean in self.personal_dict or w_clean in self.spell:
                continue
            
            misspelled.append({"word": w, "suggestions": self.get_spell_suggestions(w).get("suggestions", [])})
        return {"error": None, "misspelled": misspelled}

    def add_to_dictionary(self, word):
        import re
        word_clean = re.sub(r'[^\w\s]', '', word.lower())
        if not word_clean:
            return "Invalid word"
            
        dict_path = os.path.join(self.backup_dir, "personal_dict.txt")
        with open(dict_path, 'a', encoding='utf-8') as f:
            f.write(word_clean + "\n")
            
        if self.spell is not None:
            self.personal_dict.add(word_clean)
            self.spell.word_frequency.load_words([word_clean])
            
        return f"Added '{word}' to dictionary."

    def export_ai_report(self, content, project_name="Untitled Project"):
        filepath = self._safe_save_dialog(f'{project_name}_AI_Report.txt', '.txt', [('Text Files', '*.txt')])
        if not filepath:
            return "Export cancelled."
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Exported to: {filepath}"
        except Exception as e:
            return f"Export Error: {str(e)}"

    def load_latest_cloud(self, cloud_dir, project_name):
        if not cloud_dir or not os.path.exists(cloud_dir):
            return {"error": "Cloud directory not found or not configured. Please set it in 'Manage Backups'."}
        
        safe_name = "".join(c for c in project_name if c not in r'\/:*?"<>|')
        project_cloud_dir = os.path.join(cloud_dir, safe_name)
        target_path = os.path.join(project_cloud_dir, f"{safe_name}.rsp")
        
        if os.path.exists(target_path):
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    return {'filepath': target_path, 'data': f.read()}
            except Exception as e:
                return {'error': f"Error reading file: {str(e)}"}
        else:
            return {'not_found': True, 'message': f"No file named '{safe_name}.rsp' was found in the cloud directory.\n\nChecked Path: {project_cloud_dir}"}

    def save_latest_cloud(self, cloud_dir, project_name, content):
        if not cloud_dir or not os.path.exists(cloud_dir):
            return {"error": "Cloud directory not found or not configured. Please set it in 'Manage Backups'."}
        
        safe_name = "".join(c for c in project_name if c not in r'\/:*?"<>|')
        project_cloud_dir = os.path.join(cloud_dir, safe_name)
        
        try:
            if not os.path.exists(project_cloud_dir):
                os.makedirs(project_cloud_dir)
                
            target_path = os.path.join(project_cloud_dir, f"{safe_name}.rsp")
            
            if os.path.exists(target_path):
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_name = f"{safe_name}_{timestamp}.rsp"
                backup_path = os.path.join(cloud_dir, backup_name)
                os.rename(target_path, os.path.join(project_cloud_dir, backup_name))
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {'success': True, 'filepath': target_path}
        except Exception as e:
            return {'error': f"Error saving file: {str(e)}"}

    def create_project_folder(self, cloud_dir, project_name):
        if not cloud_dir or not os.path.exists(cloud_dir):
            return {"error": "Cloud directory not found or not configured."}
        
        safe_name = "".join(c for c in project_name if c not in r'\/:*?"<>|')
        project_cloud_dir = os.path.join(cloud_dir, safe_name)
        
        try:
            if not os.path.exists(project_cloud_dir):
                os.makedirs(project_cloud_dir)
            return {"success": True, "path": project_cloud_dir}
        except Exception as e:
            return {"error": str(e)}

    def analyze_script(self, paragraphs):
        return editor.analyze_script_context(paragraphs)
        
    def get_ai_suggestions(self, selected_text):
        return editor.get_ai_suggestions(selected_text)

    def get_initial_file(self):
        if len(sys.argv) > 1 and sys.argv[1] != '--run-dialog':
            filepath = sys.argv[1]
            if os.path.exists(filepath) and filepath.lower().endswith(('.rsp', '.ksp')):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        return {'filepath': filepath, 'data': f.read()}
                except Exception as e:
                    return {'error': str(e)}
        return None

if __name__ == '__main__':
    api = BackendAPI()
    
    if getattr(sys, 'frozen', False):
        current_dir = sys._MEIPASS
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
    html_path = os.path.join(current_dir, 'index.html')
    
    webview.create_window('ReelScript 1.0', url=html_path, js_api=api, width=1280, height=800)
    webview.start()