import os
import logging

class ToolManager:
    def __init__(self):
        # Sandbox Folder Security
        self.sandbox_dir = os.path.abspath(os.path.join(os.getcwd(), "sandbox"))
        if not os.path.exists(self.sandbox_dir):
            os.makedirs(self.sandbox_dir)

    def execute(self, tool_name, args):
        try:
            if tool_name == "create_file":
                return self.create_file(args.get("filename"), args.get("content", ""))
            
            elif tool_name == "edit_file":
                return self.edit_file(
                    args.get("filename"), 
                    args.get("content", ""), 
                    args.get("mode", "append") # Default is append (add to bottom)
                )
            
            elif tool_name == "read_file":
                return self.read_file(args.get("filename"))
            elif tool_name == "delete_file":
                return self.delete_file(args.get("filename"))
            elif tool_name == "list_files":
                return self.list_files()
            else:
                return "Unknown Tool"
        except Exception as e:
            return f"Error: {str(e)}"

    def _is_safe(self, filename):
        """Prevents accessing files outside sandbox"""
        path = os.path.abspath(os.path.join(self.sandbox_dir, filename))
        return path.startswith(self.sandbox_dir)

    def create_file(self, filename, content):
        if not self._is_safe(filename): return "Access Denied"
        with open(os.path.join(self.sandbox_dir, filename), "w") as f: f.write(content)
        return f"File '{filename}' created."

    def edit_file(self, filename, content, mode="append"):
        if not self._is_safe(filename): return "Access Denied"
        path = os.path.join(self.sandbox_dir, filename)
        
        # Check if file exists before editing
        if not os.path.exists(path) and mode == "append":
            return "File not found. Create it first."

        file_mode = "a" if mode == "append" else "w"
        # Add newline for appending to keep it clean
        final_content = f"\n{content}" if mode == "append" else content

        with open(path, file_mode) as f:
            f.write(final_content)
        
        action = "updated" if mode == "append" else "overwritten"
        return f"File '{filename}' {action}."

    def read_file(self, filename):
        if not self._is_safe(filename): return "Access Denied"
        path = os.path.join(self.sandbox_dir, filename)
        if os.path.exists(path):
            with open(path, "r") as f: return f"Content:\n{f.read()[:1000]}"
        return "File not found."

    def delete_file(self, filename):
        if not self._is_safe(filename): return "Access Denied"
        path = os.path.join(self.sandbox_dir, filename)
        if os.path.exists(path): os.remove(path); return "Deleted."
        return "File not found."

    def list_files(self):
        files = os.listdir(self.sandbox_dir)
        return str(files) if files else "Folder is empty."
