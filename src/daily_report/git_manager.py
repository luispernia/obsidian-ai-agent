import git
import os
from src import config

class GitManager:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path if repo_path else config.VAULT_ABS_PATH
        try:
            self.repo = git.Repo(self.repo_path, search_parent_directories=True)
        except git.exc.InvalidGitRepositoryError:
            # Try to initialize if not a repo, or raise error? 
            # User said "using git tracking", implies it might be a repo or we should make it one.
            # Choosing to just raise for now, users usually have their vault as a git repo.
            print(f"Error: {self.repo_path} is not a valid git repository.")
            raise

    def get_current_changes(self):
        """Returns the diff of current changes (staged and unstaged)."""
        # Staged changes
        try:
            diff_staged = self.repo.git.diff("--cached")
        except: 
            diff_staged = ""
            
        # Unstaged changes
        try:
            diff_unstaged = self.repo.git.diff()
        except:
             diff_unstaged = ""
        
        # New untracked files
        untracked = self.repo.untracked_files
        
        full_diff = ""
        if diff_staged:
            full_diff += "STAGED CHANGES:\n" + diff_staged + "\n\n"
        if diff_unstaged:
            full_diff += "UNSTAGED CHANGES:\n" + diff_unstaged + "\n\n"
        if untracked:
            full_diff += "UNTRACKED FILES:\n"
            for file_path in untracked:
                full_diff += f"\n--- NEW FILE: {file_path} ---\n"
                try:
                    full_path_abs = os.path.join(self.repo.working_dir, file_path)
                    if file_path.endswith(('.md', '.txt', '.py', '.json', '.yaml', '.yml')):
                        with open(full_path_abs, 'r', encoding='utf-8') as f:
                            content = f.read()
                            full_diff += content + "\n"
                    else:
                        full_diff += "(Skipped non-text file)\n"
                except Exception as e:
                    full_diff += f"(Error reading file: {e})\n"
            
        return full_diff

    def commit_all(self, message):
        """Adds all changes and commits them."""
        # Add all, including untracked
        self.repo.git.add(A=True)
        return self.repo.index.commit(message)
