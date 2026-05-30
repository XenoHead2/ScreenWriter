import os
import re
import shutil
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from docx import Document
from google import genai

# Check common environment variable names for the API key
api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

try:
    # Initialize the new standard GenAI Client
    client = genai.Client(api_key=api_key) if api_key else genai.Client()
except ValueError:
    client = None

def read_docx_content(file_path):
    """Helper to extract clean text from a isolated .docx chapter file."""
    doc = Document(file_path)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return '\n'.join(full_text)

def generate_analysis_from_text(chapter_text):
    if not client:
        raise ValueError("No API key was provided. Please ensure GEMINI_API_KEY is set in your environment variables.")

    # Load custom rules to prevent repeated AI mistakes
    rules_text = ""
    rules_file = "world_rules.txt"
    if os.path.exists(rules_file):
        with open(rules_file, "r", encoding="utf-8") as f:
            rules_content = f.read().strip()
            if rules_content:
                rules_text = f"\nIMPORTANT WORLDBUILDING RULES & CONTEXT TO FOLLOW (Ignore \"errors\" related to these):\n{rules_content}\n"

    # Create numbered text for the AI to reference easily
    numbered_lines = []
    for i, line in enumerate(chapter_text.split('\n')):
        numbered_lines.append(f"Line#{i+1}: {line}")
    numbered_chapter_text = '\n'.join(numbered_lines)

    # Frame the deep structural editing prompt
    prompt = f"""
    You are an expert line editor and developmental manuscript reviewer. 
    Analyze the following science fiction chapter text for stylistic improvements. 
    Do not rewrite the text for me. Instead, provide a structured report detailing:
    
    1. Word Choice & Redundancy: List overused words, filler phrases, or sticky sentences.
    2. Pacing & Readability: Highlight segments where the narrative flow drags or sentences are too dense.
    3. Passive Voice: Pinpoint specific instances of passive verbs that should be active.
    
    IMPORTANT: You MUST include the exact line reference for EACH and EVERY suggestion using the exact format "Line#X" (e.g., Line#1, Line#45).
    IMPORTANT: Leave a blank line between each individual suggestion for readability.
    IMPORTANT: Do not include any introductory or concluding fluff (like "Here is an analysis..."). Start directly with the structured report.
    {rules_text}
    Text to analyze:
    {numbered_chapter_text}
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
    )
    return response.text

def analyze_chapter_style(chapter_filename):
    if not os.path.exists(chapter_filename):
        print(f"Error: Could not find file '{chapter_filename}'")
        raise FileNotFoundError(f"Could not find file '{chapter_filename}'")

    print(f"Reading content from {chapter_filename}...")
    chapter_text = read_docx_content(chapter_filename)

    print("Sending text to cloud via gemini-3.5-flash for analysis...")
    try:
        suggestions = generate_analysis_from_text(chapter_text)
    except Exception as e:
        print(f"Error during API call: {e}")
        raise e
    
    # Generate report filename matching the chapter source
    base_name = os.path.splitext(os.path.basename(chapter_filename))[0]
    report_filename = os.path.join(os.path.dirname(chapter_filename), f"Review_{base_name}.txt")
    
    with open(report_filename, "w", encoding="utf-8") as out_file:
        out_file.write(suggestions)
        
    print(f"Analysis complete! Style report saved safely to: {report_filename}\n")
    return chapter_text, suggestions

def run_gui():
    def browse_input():
        filepath = filedialog.askopenfilename(
            title="Select Chapter DOCX",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        if filepath:
            input_var.set(filepath)

    def start_analysis():
        input_file = input_var.get()
        if not os.path.exists(input_file):
            messagebox.showerror("Error", "Please select a valid DOCX file.")
            return

        try:
            # Note: The GUI will briefly freeze while waiting for the AI response
            original_text, suggestions_text = analyze_chapter_style(input_file)
            messagebox.showinfo("Success", "Analysis complete! Style report saved safely.")
            show_suggestions_window(input_file, original_text, suggestions_text)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

    def show_suggestions_window(input_file, original_text, suggestions_text):
        result_win = tk.Toplevel(root)
        result_win.title("Analysis & Suggestions Viewer")
        result_win.geometry("1200x800")
        
        paned = tk.PanedWindow(result_win, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side: Original Analyzed File
        left_frame = tk.Frame(paned)
        left_header = tk.Frame(left_frame)
        left_header.pack(fill=tk.X, pady=(0, 5))
        tk.Label(left_header, text="Original Analyzed Content (Editable)", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        def save_and_backup():
            base_dir = os.path.dirname(input_file)
            file_name = os.path.basename(input_file)
            name, ext = os.path.splitext(file_name)
            
            # Find the next available backup number
            counter = 1
            while True:
                backup_name = f"{name}_{counter}{ext}"
                backup_path = os.path.join(base_dir, backup_name)
                if not os.path.exists(backup_path):
                    break
                counter += 1
                
            try:
                shutil.copy2(input_file, backup_path)
                edited_text = left_text.get("1.0", "end-1c")
                new_doc = Document()
                for para in edited_text.split('\n'):
                    new_doc.add_paragraph(para)
                new_doc.save(input_file)
                messagebox.showinfo("Saved", f"Backup created:\n{backup_name}\n\nEdits saved successfully to original file.", parent=result_win)
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save edits: {e}", parent=result_win)
                
        tk.Button(left_header, text="Save Edits & Backup", command=save_and_backup).pack(side=tk.RIGHT)

        def auto_fix_selection():
            try:
                sel_start = left_text.index(tk.SEL_FIRST)
                sel_end = left_text.index(tk.SEL_LAST)
                selected_text = left_text.get(sel_start, sel_end)
            except tk.TclError:
                messagebox.showwarning("Select Text", "Please highlight some text in the left pane first to auto-fix.", parent=result_win)
                return
                
            prompt = f"Fix the grammar, flow, and word choice of the following text. Preserve the original tone and meaning. Output ONLY the fixed text, with no introductory or concluding text, no quotes around it, and no markdown formatting:\n\n{selected_text}"
            
            left_text.config(cursor="watch")
            result_win.update()
            try:
                response = client.models.generate_content(model='gemini-3.5-flash', contents=prompt)
                fixed_text = response.text.strip()
                left_text.delete(sel_start, sel_end)
                left_text.insert(sel_start, fixed_text)
                messagebox.showinfo("Auto-Fix", "Text has been rewritten!", parent=result_win)
            except Exception as e:
                messagebox.showerror("Error", f"Auto-fix failed: {e}", parent=result_win)
            left_text.config(cursor="")

        tk.Button(left_header, text="AI Auto-Fix Selected", command=auto_fix_selection).pack(side=tk.RIGHT, padx=5)
        
        left_scroll = tk.Scrollbar(left_frame)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        left_text = tk.Text(left_frame, wrap=tk.WORD, yscrollcommand=left_scroll.set, padx=15, pady=15, font=("Arial", 11), spacing2=4)
        left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scroll.config(command=left_text.yview)
        left_text.insert(tk.END, original_text)
        paned.add(left_frame)
        
        def scroll_to_line(line_num):
            left_text.see(f"{line_num}.0")
            left_text.tag_remove("highlight", "1.0", tk.END)
            left_text.tag_add("highlight", f"{line_num}.0", f"{line_num}.end")
            left_text.tag_config("highlight", background="yellow")

        # Right side: Suggestions
        right_frame = tk.Frame(paned)
        right_header = tk.Frame(right_frame)
        right_header.pack(fill=tk.X, pady=(0, 5))
        tk.Label(right_header, text="Review / Suggestions", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        tk.Label(right_header, text="(Right-click a suggestion to strike it out)", font=("Arial", 8, "italic"), fg="gray").pack(side=tk.LEFT, padx=5)
        
        def add_world_rule():
            rule = simpledialog.askstring("Teach AI a Rule", "Enter a rule or context the AI should remember:", parent=result_win)
            if rule and rule.strip():
                with open("world_rules.txt", "a", encoding="utf-8") as f:
                    f.write(f"- {rule.strip()}\n")
                messagebox.showinfo("Rule Saved", "Rule added!", parent=result_win)
                
        def edit_world_rules():
            edit_win = tk.Toplevel(result_win)
            edit_win.title("Edit World Rules")
            edit_win.geometry("600x400")
            tk.Label(edit_win, text="Modify or delete rules below:", font=("Arial", 10)).pack(pady=5)
            text_area = tk.Text(edit_win, wrap=tk.WORD)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            rules_file = "world_rules.txt"
            if os.path.exists(rules_file):
                with open(rules_file, "r", encoding="utf-8") as f:
                    text_area.insert(tk.END, f.read())
            def save_rules():
                content = text_area.get("1.0", tk.END).strip()
                with open(rules_file, "w", encoding="utf-8") as f:
                    if content: f.write(content + "\n")
                messagebox.showinfo("Rules Saved", "World rules updated successfully.", parent=edit_win)
                edit_win.destroy()
            tk.Button(edit_win, text="Save Changes", command=save_rules).pack(pady=10)

        def quick_reanalyze():
            right_text.config(state=tk.NORMAL)
            right_text.delete("1.0", tk.END)
            right_text.insert(tk.END, "Re-analyzing text... Please wait (GUI will briefly freeze)...")
            right_text.config(state=tk.DISABLED)
            result_win.update()
            
            current_text = left_text.get("1.0", "end-1c")
            try:
                new_suggestions = generate_analysis_from_text(current_text)
                right_text.config(state=tk.NORMAL)
                right_text.delete("1.0", tk.END)
                right_text.insert(tk.END, new_suggestions)
                apply_hyperlinks()
                right_text.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to re-analyze: {e}", parent=result_win)

        tk.Button(right_header, text="Teach AI a Rule", command=add_world_rule).pack(side=tk.RIGHT)
        tk.Button(right_header, text="Edit Rules", command=edit_world_rules).pack(side=tk.RIGHT, padx=5)
        tk.Button(right_header, text="Quick Re-Analyze", command=quick_reanalyze).pack(side=tk.RIGHT, padx=5)
        
        right_scroll = tk.Scrollbar(right_frame)
        right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        right_text = tk.Text(right_frame, wrap=tk.WORD, yscrollcommand=right_scroll.set, padx=15, pady=15, font=("Arial", 11), spacing2=4)
        right_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_scroll.config(command=right_text.yview)
        right_text.insert(tk.END, suggestions_text)
        
        right_text.tag_config("resolved", overstrike=1, foreground="gray")
        
        def toggle_resolved(event):
            # Toggle strikethrough for the clicked logical line/paragraph
            pos = right_text.index(f"@{event.x},{event.y}")
            line_start = f"{pos} linestart"
            line_end = f"{pos} lineend"
            if "resolved" in right_text.tag_names(pos):
                right_text.tag_remove("resolved", line_start, line_end)
            else:
                right_text.tag_add("resolved", line_start, line_end)
                
        right_text.bind("<Button-3>", toggle_resolved)  # Windows/Linux Right-Click
        right_text.bind("<Button-2>", toggle_resolved)  # Mac OS Right-Click fallback
        
        def apply_hyperlinks():
            right_text.tag_config("hyperlink", foreground="blue", underline=1)
            countVar = tk.StringVar()
            start_pos = "1.0"
            while True:
                pos = right_text.search(r'Line#\d+', start_pos, stopindex=tk.END, count=countVar, regexp=True, nocase=True)
                if not pos: break
                match_len = int(countVar.get())
                end_pos = f"{pos}+{match_len}c"
                match_text = right_text.get(pos, end_pos)
                m = re.search(r'\d+', match_text)
                if m:
                    line_num = m.group(0)
                    tag_name = f"line_{line_num}_{pos}"
                    right_text.tag_add(tag_name, pos, end_pos)
                    right_text.tag_add("hyperlink", pos, end_pos)
                    right_text.tag_bind(tag_name, "<Button-1>", lambda e, p=line_num: scroll_to_line(p))
                    right_text.tag_bind(tag_name, "<Enter>", lambda e: right_text.config(cursor="hand2"))
                    right_text.tag_bind(tag_name, "<Leave>", lambda e: right_text.config(cursor=""))
                start_pos = end_pos

        apply_hyperlinks()

        right_text.config(state=tk.DISABLED)
        paned.add(right_frame)

    root = tk.Tk()
    root.title("AI Chapter Editor")
    root.geometry("500x150")
    root.resizable(False, False)

    input_var = tk.StringVar()

    # Input File Section
    tk.Label(root, text="Chapter DOCX File:").pack(anchor="w", padx=10, pady=(10, 0))
    input_frame = tk.Frame(root)
    input_frame.pack(fill="x", padx=10)
    tk.Entry(input_frame, textvariable=input_var).pack(side="left", fill="x", expand=True, padx=(0, 10))
    tk.Button(input_frame, text="Browse...", command=browse_input).pack(side="right")

    # Analyze Button
    tk.Button(root, text="Analyze Chapter", command=start_analysis).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    run_gui()