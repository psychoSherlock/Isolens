import shutil
import os

def sync_docs():
    source = "AGENTS.md"
    targets = [
        "GEMINI.md",
        "AI-INSTRUCTIONS.md",
        ".github/copilot-instructions.md"
    ]
    
    if not os.path.exists(source):
        print(f"Error: {source} not found.")
        return

    for target in targets:
        try:
            # Ensure target directory exists
            target_dir = os.path.dirname(target)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            shutil.copy2(source, target)
            print(f"Successfully synced {source} to {target}")
        except Exception as e:
            print(f"Failed to sync to {target}: {e}")

if __name__ == "__main__":
    sync_docs()
