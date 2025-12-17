import os
from datetime import datetime
try:
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    from langchain.prompts import ChatPromptTemplate
from src.ai_provider import AIProvider
from src.daily_report.git_manager import GitManager
from src import config

def generate_summary(output_filename: str = "Summary.md"):
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
        
        prompt = ChatPromptTemplate.from_template(
            "You are a helpful assistant for a developer. "
            "Summarize the following git changes ({source}) into a concise report. "
            "The report should list modified files and key changes in bullet points. "
            "Focus on the content and meaning of the changes. "
            "\n\n"
            "CHANGES:\n{diff}"
        )
        
        chain = prompt | llm
        result = chain.invoke({"diff": diff_text, "source": source})
        summary = result.content
    except Exception as e:
        print(f"Error generating summary with LLM: {e}")
        summary = "Error generating summary."

    # Create Report File
    report_path = os.path.join(config.REPORTS_ABS_PATH, output_filename)
    
    report_content = f"# Summary Report ({source})\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n{summary}\n"
    
    try:
        with open(report_path, "w") as f:
            f.write(report_content)
        print(f"Summary report created at {report_path}")
        return report_path
    except Exception as e:
         print(f"Error writing report file: {e}")
         return None

if __name__ == "__main__":
    generate_summary()
