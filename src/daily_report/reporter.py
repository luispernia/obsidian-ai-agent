import os
import json
from datetime import datetime
from typing import Optional, Dict, List

try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
except ImportError:
    from langchain.prompts import ChatPromptTemplate
    from langchain.output_parsers import JsonOutputParser

from pydantic import BaseModel, Field
from src.ai_provider import AIProvider
from src.daily_report.git_manager import GitManager
from src import config

class ReportStructure(BaseModel):
    summary: str = Field(description="The markdown summary content of the report. Use ## for section headers.")
    topic: str = Field(description="A short, relevant topic title for the report (3-5 words), e.g. 'Refactored Auth Logic'")
    tags: List[str] = Field(description="A list of relevant tags for the report, e.g. ['refactor', 'auth', 'bugfix']")

def generate_report_content() -> Optional[Dict]:
    print("Generating Summary Report...")
    
    try:
        manager = GitManager()
    except Exception as e:
        print(f"Failed to initialize GitManager: {e}")
        return None
    
    # Get Changes
    diff_text = manager.get_current_changes()
    if not diff_text.strip():
        print("No current changes found. Checking last commit...")
        diff_text = manager.get_last_commit_diff()
        source = "Last Commit"
    else:
        source = "Current Working Directory"

    if not diff_text.strip():
        print("No changes found in git history to summarize.")
        return None

    # Summarize with LLM
    try:
        llm = AIProvider.get_llm()
        parser = JsonOutputParser(pydantic_object=ReportStructure)
        
        prompt = ChatPromptTemplate.from_template(
            "You are a helpful assistant for a developer. "
            "Analyze the following git changes ({source}) and generate a structured report.\n\n"
            "CHANGES:\n{diff}\n\n"
            "{format_instructions}\n"
            "Focus on the content and meaning of the changes. The summary should be concise but informative."
        )
        
        chain = prompt | llm | parser
        
        # Truncate diff if too large to avoid context window issues
        safe_diff = diff_text[:15000]
        
        result = chain.invoke({
            "diff": safe_diff, 
            "source": source,
            "format_instructions": parser.get_format_instructions()
        })
        
        # Result should be a dict matching ReportStructure
        return result
        
    except Exception as e:
        print(f"Error generating summary with LLM: {e}")
        return None

if __name__ == "__main__":
    report_data = generate_report_content()
    if report_data:
        print(json.dumps(report_data, indent=2))
