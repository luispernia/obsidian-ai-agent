import os
import json
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from src import config

DATA_DIR = Path(".data")
CHATS_DIR = DATA_DIR / "chats"
REPORTS_META_FILE = DATA_DIR / "reports_meta.json"

class ChatManager:
    def __init__(self):
        CHATS_DIR.mkdir(parents=True, exist_ok=True)
        
    def save_chat(self, session_id: str, messages: List[Dict], title: str = None):
        """Saves a chat session."""
        file_path = CHATS_DIR / f"{session_id}.json"
        
        # Load existing to preserve creation time/title if not provided
        data = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "title": title or "New Chat",
            "pinned": False,
            "messages": messages
        }
        
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    existing = json.load(f)
                data['created_at'] = existing.get('created_at', data['created_at'])
                data['pinned'] = existing.get('pinned', False)
                if not title: 
                    data['title'] = existing.get('title', "New Chat")
            except:
                pass
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_chat(self, session_id: str) -> Optional[Dict]:
        file_path = CHATS_DIR / f"{session_id}.json"
        if not file_path.exists():
            return None
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return None

    def list_chats(self) -> List[Dict]:
        """Returns metadata for all chats, sorted by Pinned > Updated."""
        chats = []
        for f in CHATS_DIR.glob("*.json"):
            try:
                with open(f, 'r') as file:
                    data = json.load(file)
                    # Minimal metadata for list
                    chats.append({
                        "id": data["id"],
                        "title": data.get("title", "Untitled"),
                        "updated_at": data.get("updated_at", ""),
                        "pinned": data.get("pinned", False),
                        "preview": data["messages"][-1]["content"][:50] if data.get("messages") else ""
                    })
            except:
                continue
                
        # Sort: Pinned (True > False), then Updated (Newest > Oldest)
        chats.sort(key=lambda x: (not x["pinned"], x["updated_at"]), reverse=True)
        return chats

    def delete_chat(self, session_id: str):
        file_path = CHATS_DIR / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()

    def toggle_pin(self, session_id: str):
        data = self.load_chat(session_id)
        if data:
            data['pinned'] = not data.get('pinned', False)
            with open(CHATS_DIR / f"{session_id}.json", 'w') as f:
                json.dump(data, f, indent=2)

class ReportManager:
    def __init__(self):
        self.reports_dir = Path(config.REPORTS_ABS_PATH)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Load metadata (pins)
        self.meta = {}
        if REPORTS_META_FILE.exists():
            try:
                with open(REPORTS_META_FILE, 'r') as f:
                    self.meta = json.load(f)
            except:
                self.meta = {}

    def _save_meta(self):
        REPORTS_META_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REPORTS_META_FILE, 'w') as f:
            json.dump(self.meta, f, indent=2)

    def list_reports(self) -> List[Dict]:
        files = list(self.reports_dir.glob("*.md"))
        reports = []
        for f in files:
            stat = f.stat()
            is_pinned = self.meta.get(f.name, {}).get('pinned', False)
            reports.append({
                "filename": f.name,
                "path": str(f),
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "pinned": is_pinned
            })
            
        # Sort: Pinned > Modified
        reports.sort(key=lambda x: (not x["pinned"], x["modified"]), reverse=True)
        return reports

    def get_report_content(self, filename: str) -> str:
        path = self.reports_dir / filename
        if path.exists():
            with open(path, 'r') as f:
                return f.read()
        return ""

    def toggle_pin(self, filename: str):
        if filename not in self.meta:
            self.meta[filename] = {}
        self.meta[filename]['pinned'] = not self.meta[filename].get('pinned', False)
        self._save_meta()

    def delete_report(self, filename: str):
        path = self.reports_dir / filename
        if path.exists():
            path.unlink()
        if filename in self.meta:
            del self.meta[filename]
            self._save_meta()
