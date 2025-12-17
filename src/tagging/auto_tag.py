import os
import re
import glob
import json
import collections
import argparse
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import frontmatter # type: ignore
from langchain_core.prompts import ChatPromptTemplate
from src import config
from src.ai_provider import AIProvider

# Regex for inline tags: #tag (alphanumeric, -, _, /)
# Excludes #1 (headers) or # (empty)
TAG_REGEX = re.compile(r'(?:^|[\s])#([a-zA-Z0-9_\-/]+)(?=[\s.,!?)]|$)')

CACHE_FILE = Path(".auto_tag_cache.json")

class TagCache:
    def __init__(self):
        self.cache = {}
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}

    def should_process(self, file_path: Path) -> bool:
        """Returns True if file is new or modified since last check."""
        str_path = str(file_path)
        if str_path not in self.cache:
            return True
        
        last_mtime = self.cache[str_path]
        current_mtime = file_path.stat().st_mtime
        
        # Check if modified time is strictly greater (allowing for some float precision issues)
        return current_mtime > last_mtime

    def update(self, file_path: Path):
        """Updates the cache with current mtime."""
        self.cache[str(file_path)] = file_path.stat().st_mtime
        self._save()

    def _save(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=2)

class TagScanner:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.tag_files: Dict[str, Set[str]] = collections.defaultdict(set)
        self.tag_counts: collections.Counter = collections.Counter()
    
    def get_all_markdown_files(self) -> List[Path]:
        return list(self.vault_path.rglob("*.md"))

    def parse_tags_from_file(self, file_path: Path) -> Set[str]:
        tags = set()
        try:
            post = frontmatter.load(file_path)
            
            # 1. Frontmatter tags
            fm_tags = post.metadata.get('tags')
            if fm_tags is None:
                fm_tags = []
            if isinstance(fm_tags, str):
                # Handle comma separated or space separated string
                fm_tags = [t.strip() for t in fm_tags.replace(',', ' ').split()]
            
            for t in fm_tags:
                tags.add(f"#{t.strip('#')}")

            # 2. Inline tags
            content = post.content
            inline_matches = TAG_REGEX.findall(content)
            for t in inline_matches:
                tags.add(f"#{t}")
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return tags

    def build_index(self):
        print("Indexing vault tags...")
        files = self.get_all_markdown_files()
        for f in files:
            tags = self.parse_tags_from_file(f)
            for t in tags:
                self.tag_files[t].add(str(f))
                self.tag_counts[t] += 1
        print(f"Indexed {len(self.tag_counts)} unique tags across {len(files)} files.")

    def get_top_tags(self, limit=100) -> List[str]:
        return [tag for tag, count in self.tag_counts.most_common(limit)]

class TagSuggester:
    def __init__(self):
        try:
            self.llm = AIProvider.get_llm()
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            self.llm = None
        except Exception as e:
            print(f"Error initializing Ollama: {e}")
            self.llm = None

    def analyze_note(self, content: str, current_tags: Set[str], top_tags: List[str]) -> Optional[Dict]:
        if not self.llm:
            return None

        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert Personal Knowledge Management assistant.
            
            Your task is to analyze a Markdown note and enforce tag consistency.
            
            Context:
            - **Existing Vault Tags** (Prioritize these): {top_tags}
            - **Current Note Tags**: {current_tags}
            
            Instructions:
            1. **Topics**: Suggest 3-5 relevant tags. PREFER existing tags from the list above if they match the concept. Only invent new tags for truly novel topics. Format as #tag.
            2. **Maturity**: Classify the note's status as ONE of:
               - #seed (Draft, short, just a link/thought)
               - #sprout (Developing, has structure but needs work)
               - #evergreen (Polished, complete, authoritative)
               *Update Rule*: Check the content depth. If it's a #seed but has grown, promote it.
            3. **Quality**: If the note is effectively empty or extremely unstructured, add #for-review.
            
            Return a JSON object with this EXACT structure (no markdown formatting around it):
            {{
                "topic_tags": ["#tag1", "#tag2"],
                "maturity_tag": "#seed",
                "maintenance_tag": null or "#for-review"
            }}
            
            NOTE CONTENT:
            {content}
            """
        )
        
        try:
            # truncate content if too long
            truncated_content = content[:4000] 
            chain = prompt | self.llm
            response = chain.invoke({
                "top_tags": ", ".join(top_tags),
                "current_tags": ", ".join(current_tags),
                "content": truncated_content
            })
            
            # Robust JSON extraction
            content = response.content.strip()
            # Find the JSON object using regex (non-greedy match between braces)
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                 # Fallback to naive clean if no braces found (unlikely)
                 if content.startswith("```json"):
                     content = content[7:-3]
                 return json.loads(content)
            
        except Exception as e:
            print(f"LLM Error: {e}")
            return None

def apply_changes(file_path: Path, new_tags: Set[str], original_content: str):
    """
    Re-writes the file. 
    Strategy: 
    1. Parse frontmatter.
    2. Update 'tags' field in frontmatter.
    3. Remove ONLY the maturity/status tags from inline content to avoid duplication, 
       BUT keeping inline topic tags might be tricky.
    
    SIMPLIFIED STRATEGY for safety:
    1. Load frontmatter.
    2. Put ALL tags into frontmatter 'tags' list.
    3. Write back.
    4. (Advanced) We are NOT removing inline tags from text to avoid destroying context. 
       We just ensure the frontmatter represents the 'truth'. 
       Obsidian treats frontmatter + inline as the set of tags.
       If we want to REMOVE a tag, we can only safely remove it if it's in frontmatter.
       removing inline tags is risky without precise location.
       
    Refined Strategy:
    1. We will only ADD/UPDATE tags in Frontmatter.
    2. If we want to 'remove' a tag that is inline... we can't easily do that safely in this V1.
    3. So we will focus on ADDING missing tags and ensuring Status tag is correct in Frontmatter.
       If there is a conflicting inline status tag, it might be an issue, but let's assume usage of frontmatter for status.
    """
    try:
        post = frontmatter.load(file_path)
        
        # specific logic: Ensure only ONE maturity tag is in the list
        maturity_tags = {'seed', 'sprout', 'evergreen'}
        
        # Clean new tags to be purely list of strings without #
        clean_new_tags = {t.strip('#') for t in new_tags}
        
        post.metadata['tags'] = list(clean_new_tags)
        
        with open(file_path, 'wb') as f:
            frontmatter.dump(post, f)
            
    except Exception as e:
        print(f"Error writing {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Auto-tag Obsidian notes.")
    parser.add_argument("--auto", "--yes", action="store_true", help="Automatically apply changes without confirmation.")
    parser.add_argument("--force", action="store_true", help="Ignore cache and re-process all files.")
    parser.add_argument("--folder", help="Specific folder to scan (relative to Vault root).", default=None)
    args = parser.parse_args()

    print(f"Starting Smart Auto-Tagger in {config.VAULT_ABS_PATH}...")
    if args.auto:
        print("AUTONOMOUS MODE ENABLED.")
    
    cache = TagCache()
    scanner = TagScanner(config.VAULT_ABS_PATH)
    scanner.build_index()
    top_tags = scanner.get_top_tags(50)
    
    suggester = TagSuggester()
    if not suggester.llm:
        print("Could not initialize LLM. Exiting.")
        return

    # Filter files if folder argument is present
    if args.folder:
        target_dir = Path(config.VAULT_ABS_PATH) / args.folder
        if not target_dir.exists():
            print(f"Error: Folder '{args.folder}' does not exist in vault.")
            return
        files = list(target_dir.rglob("*.md"))
        print(f"Targeting folder: {args.folder}")
    else:
        files = scanner.get_all_markdown_files()

    print(f"Found {len(files)} notes to process.")
    
    lines_processed = 0
    for i, file_path in enumerate(files):
        if not args.force and not cache.should_process(file_path):
            continue

        lines_processed += 1
        print(f"\n[{i+1}/{len(files)}] Processing {file_path.name}...")
        
        current_tags = scanner.parse_tags_from_file(file_path)
        
        # Load content just for analysis
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            continue

        result = suggester.analyze_note(content, current_tags, top_tags)
        
        if not result:
            continue
            
        suggested_topics = set(result.get('topic_tags', []))
        maturity_tag = result.get('maturity_tag')
        maintenance_tag = result.get('maintenance_tag')
        
        new_tag_set = set(suggested_topics)
        if maturity_tag:
            new_tag_set.add(maturity_tag)
        if maintenance_tag:
            new_tag_set.add(maintenance_tag)
            
        # Diff
        added = new_tag_set - current_tags
        removed = current_tags - new_tag_set
        
        # Filter removals: If a tag is inline, we probably shouldn't "remove" it locally unless we edit text.
        # For V1, we will only prompt if there are ADDITIONS or if Maturity changes (which is an addition/removal pair)
        
        if not added and not removed:
            print("No changes needed.")
            continue
            
        print(f"  Current: {current_tags}")
        print(f"  Suggested: {new_tag_set}")
        print(f"  Changes: +{added} -{removed}")
        
        if args.auto:
            print("  Auto-applying changes...")
            choice = 'y'
        else:
            choice = input("  Apply changes? [y]es / [s]kip / [q]uit: ").lower().strip()
        
        if choice == 'y':
            apply_changes(file_path, new_tag_set, content)
            cache.update(file_path)
            print("  Updated.")
        elif choice == 's':
            # Mark as processed even if skipped, to avoid prompting again immediately
            cache.update(file_path) 
            print("  Skipped (Cached).")
        elif choice == 'q':
            break
        else:
            print("  Skipped.")

    if lines_processed == 0:
        print("\nAll files are up to date! Use --force to re-check.")

if __name__ == "__main__":
    main()
