import os
import datetime
from src.ai_provider import AIProvider

def generate_daily_report():
    print("Initiating Daily Report...")
    # ... (skipping git parts)
    
    # 2. Summarize with LLM
    try:
        # Use factory to get configured LLM
        llm = AIProvider.get_llm()
        
        prompt = ChatPromptTemplate.from_template(
            "You are a helpful assistant for a developer/writer. "
            "Summarize the following 'git diff' changes into a concise daily report. "
            "The report should list modified files and key changes in bullet points. "
            "Focus on content changes in markdown files. "
            "Be encouraging but professional.\n\n"
            "CHANGES:\n{diff}"
        )
        
        chain = prompt | llm
        result = chain.invoke({"diff": diff_text})
        summary = result.content
    except Exception as e:
        print(f"Error generating summary with LLM: {e}")
        summary = "Error generating summary. Please check API keys and connection."

    # 3. Create Report File
    today = datetime.date.today()
    report_filename = f"{today.strftime('%Y-%m-%d')}.md"
    report_path = os.path.join(config.REPORTS_ABS_PATH, report_filename)
    
    report_content = f"# Daily Report: {today.strftime('%Y-%m-%d')}\n\n{summary}\n"
    
    try:
        with open(report_path, "w") as f:
            f.write(report_content)
        print(f"Report created at {report_path}")
    except Exception as e:
         print(f"Error writing report file: {e}")
         return

    # 4. Commit
    try:
        commit_message = f"Daily update: {today.strftime('%Y-%m-%d')}"
        manager.commit_all(commit_message)
        print(f"Committed changes with message: '{commit_message}'")
    except Exception as e:
        print(f"Error committing changes: {e}")

if __name__ == "__main__":
    generate_daily_report()
