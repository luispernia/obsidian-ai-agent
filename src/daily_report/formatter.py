import os
import glob
from datetime import datetime
from src import config
from src.ai_provider import AIProvider
from pathlib import Path
try:
    from src.tagging.auto_tag import TagScanner, TagSuggester, apply_changes
except ImportError as e:
    print(f"DEBUG IMPORTERROR: {e}")
    pass

# Handle import differences just like in reporter.py
try:
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    from langchain.prompts import ChatPromptTemplate

class DailyFormatter:
    def __init__(self):
        self.daily_path = os.path.join(config.VAULT_ABS_PATH, "Daily")
        self.formatted_path = os.path.join(config.VAULT_ABS_PATH, "Daily-Formatted")
        self.template_path = os.path.join(config.BASE_DIR, "src", "daily_report", "daily-report-template.md")
        
        # Ensure output directory exists
        os.makedirs(self.formatted_path, exist_ok=True)
        
        # Load template
        with open(self.template_path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()

        # Initialize LLM
        try:
             self.llm = AIProvider.get_llm()
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            self.llm = None

        # Initialize Tagging System
        self.tag_suggester = None
        try:
            print("Initializing Tagging System...")
            self.tag_scanner = TagScanner(config.VAULT_ABS_PATH)
            self.tag_scanner.build_index()
            self.top_tags = self.tag_scanner.get_top_tags(50)
            self.tag_suggester = TagSuggester()
            print("Tagging System ready.")
        except Exception as e:
             print(f"Warning: Tagging system could not be initialized: {e}")

    def get_daily_files(self):
        """Returns a sorted list of daily note filenames (YYYY-MM-DD.md)."""
        all_files = glob.glob(os.path.join(self.daily_path, "*.md"))
        valid_files = []
        for f in all_files:
            basename = os.path.basename(f)
            # Simple validation: matches YYYY-MM-DD.md format check
            try:
                datetime.strptime(basename.replace(".md", ""), "%Y-%m-%d")
                valid_files.append(basename)
            except ValueError:
                continue
        
        return sorted(valid_files)

    def get_smart_links(self, current_file, all_files):
        """
        Determines the Previous and Next available dates from the file list.
        Returns: (yesterday_date_str, tomorrow_date_str)
        """
        try:
            curr_idx = all_files.index(current_file)
        except ValueError:
            return None, None

        prev_file = all_files[curr_idx - 1] if curr_idx > 0 else None
        next_file = all_files[curr_idx + 1] if curr_idx < len(all_files) - 1 else None

        # Helper to strip extension
        fmt = lambda x: x.replace(".md", "") if x else "YYYY-MM-DD"
        
        return fmt(prev_file), fmt(next_file)

    def process_note(self, filename, all_files):
        print(f"Processing {filename}...")
        
        input_path = os.path.join(self.daily_path, filename)
        output_path = os.path.join(self.formatted_path, filename)
        
        # 1. Read Original Content
        with open(input_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # 2. Extract Date info
        date_str = filename.replace(".md", "")
        
        # 3. Calculate Smart Links
        yesterday_str, tomorrow_str = self.get_smart_links(filename, all_files)
        
        # 4. LLM Reformatting
        if self.llm:
            try:
                prompt = ChatPromptTemplate.from_template(
                    "You are a personal knowledge base assistant. "
                    "Your task is to reformulate the following Daily Note content into a structured format.\n"
                    "Do NOT omit any information. Just reorganize it.\n"
                    "If a section (Top Priorities, Tasks, Notes) has no content, leave it blank or omitting, but follow the requested structure.\n"
                    
                    "TARGET STRUCTURE:\n"
                    "{template}\n\n"
                    
                    "ORIGINAL CONTENT:\n"
                    "{content}\n\n"
                    
                    "Output ONLY the markdown content matching the structure. "
                    "Do NOT output the yaml frontmatter or headers if they are handled by the template logic (but here I need you to fill the SECTIONS under the headers).\n"
                    "Actually, to be safe, output the FULL markdown content replacing the body of the template. "
                    "Wait, checking the template... "
                    "It has Templater tags. Please output the content such that it fits into the 'Top Priorities', 'Tasks', and 'Notes' sections. "
                    "Let's make it simpler: \n"
                    "I will give you the user content. You extract and classify bullet points for 'Top Priorities', 'Tasks', and 'Notes'. "
                    "Return a JSON object with keys: 'top_priorities', 'tasks', 'notes'. \n"
                    "Notes: generic thoughts, journal entries, or uncategorized text.\n"
                    "Tasks: todo items.\n"
                    "Top Priorities: specific high importance tasks inferred or explicitly marked.\n"
                )
                
                # I'm deciding to just ask the LLM to rewrite the WHOLE thing filling the template slots is risky due to the templater tags.
                # Better approach: pass the template to LLM, tell it to fill it out, but keep the `<%...%>` tags exactly as is?
                # No, the user wants ME to replacing the tags. 
                # So I should separate the concerns: 
                # 1. Logic replaces tags. 
                # 2. LLM reorganizes body content.
                
                # Let's try to just ask LLM to reorganize the body.
                # We will construct the final string using string formatting.
                
                prompt_simple = ChatPromptTemplate.from_template(
                    "Reorganize the following daily note content into three sections:\n"
                    "1. Top Priorities (Important tasks)\n"
                    "2. Tasks (Todo items)\n"
                    "3. Notes (Journaling, thoughts, misc)\n\n"
                    "Keep the content strictly from the source. Do not invent info.\n"
                    "Return the response in Markdown format with ## Headers.\n\n"
                    "ORIGINAL CONTENT:\n{content}"
                )
                
                chain = prompt_simple | self.llm
                result = chain.invoke({"content": original_content})
                structured_body = result.content
                
            except Exception as e:
                print(f"LLM Error: {e}")
                structured_body = original_content + "\n\n(Formatting failed, original content preserved)"
        else:
            structured_body = original_content

        # 5. Assemble Final content
        # We need to manually inject the Frontmatter and Header from the template, 
        # because the LLM might mess up the Templater tags if we pass them through.
        
        # Let's clean the template:
        # We know the template structure.
        # It's better to construct the "Skeleton" myself and put the LLM content in, 
        # OR ask the LLM to fill the skeletal sections.
        
        # User requirement: "adapt to this daily-report template... all information... in the new formatted version"
        
        # Let's take the user's template and replace the keys manually.
        final_content = self.template_content
        
        # Replace Tags
        # <% tp.date.now("YYYY-MM-DDTHH:mm") %> -> We can just put a static creation date or the current time? 
        # User said: "format Daily Journal files". For old files, creation date is tricky. 
        # Maybe use the file date at 09:00?
        created_date = f"{date_str}T09:00"
        
        final_content = final_content.replace('<% tp.date.now("YYYY-MM-DDTHH:mm") %>', created_date)
        
        # <% tp.file.title %> -> filename date
        final_content = final_content.replace('<% tp.file.title %>', date_str)
        
        # <% tp.date.now("YYYY-MM-DD", -1, tp.file.title) %> -> Yesterday Smart Link
        final_content = final_content.replace(
            '<% tp.date.now("YYYY-MM-DD", -1, tp.file.title) %>', 
            yesterday_str if yesterday_str else "YYYY-MM-DD"
        )
        
        # <% tp.date.now("YYYY-MM-DD", 1, tp.file.title) %> -> Tomorrow Smart Link
        final_content = final_content.replace(
            '<% tp.date.now("YYYY-MM-DD", 1, tp.file.title) %>', 
            tomorrow_str if tomorrow_str else "YYYY-MM-DD"
        )
        
        # Now we have the "Header" part of the template basically ready.
        # But the existing template has empty sections:
        # ## Top Priorities
        # - [ ]
        # ...
        
        # If I simply append the LLM output, I'll duplicate headers if I'm not careful.
        # The prompt above asked for "## Headers".
        # Current template structure:
        # ---
        # FM
        # ---
        # # Title
        # > Links
        #
        # ## Top Priorities
        # ...
        
        # I will remove the "Body" part of the template string (everything after the Links)
        # and replace it with the LLM output which generates those sections.
        
        split_marker = "> [[" 
        # This is a bit brittle, but the template is fixed provided by user.
        # Template line 8: > [[ ...
        
        # Let's find where the body starts. Line 10: "## Top Priorities"
        
        if "##  Top Priorities" in final_content:
            header_part = final_content.split("##  Top Priorities")[0]
        else:
            # Fallback
            header_part = final_content
            
        final_md = header_part + "\n" + structured_body
        
        # Write Result
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_md)
            
        print(f"Saved to {output_path}")

        # 6. Auto-Tagging
        if self.tag_suggester and self.tag_suggester.llm:
            try:
                print(f"Auto-tagging {filename}...")
                out_p = Path(output_path)
                current_tags = self.tag_scanner.parse_tags_from_file(out_p)
                
                # Analyze and get suggestions
                result = self.tag_suggester.analyze_note(final_md, current_tags, self.top_tags)
                
                if result:
                    new_tags = set(result.get('topic_tags', []))
                    if result.get('maturity_tag'):
                        new_tags.add(result.get('maturity_tag'))
                    if result.get('maintenance_tag'):
                        new_tags.add(result.get('maintenance_tag'))
                    
                    if new_tags:
                        apply_changes(out_p, new_tags, final_md)
                        print(f"Applied tags: {new_tags}")
            except Exception as e:
                print(f"Error auto-tagging {filename}: {e}")


    def run(self):
        daily_files = self.get_daily_files()
        print(f"Found {len(daily_files)} daily notes.")
        
        for f in daily_files:
            # Check if file already exists in formatted folder
            formatted_file_path = os.path.join(self.formatted_path, f)
            if os.path.exists(formatted_file_path):
                print(f"Skipping {f} - already formatted.")
                continue

            self.process_note(f, daily_files)

if __name__ == "__main__":
    formatter = DailyFormatter()
    formatter.run()
