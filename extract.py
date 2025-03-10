import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import git
import fnmatch

# ===================== UTILITY FUNCTIONS =====================

def get_git_root():
    """Returns the root directory of the git repository."""
    try:
        repo = git.Repo(os.getcwd(), search_parent_directories=True)
        return repo.git.rev_parse("--show-toplevel")
    except git.exc.InvalidGitRepositoryError:
        return None

# Allowed Code File Extensions - Now a global set that can be modified
ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".cs", ".rb", ".go", ".rs", ".php", ".html"}

# ===================== TREE STRUCTURE HANDLING =====================

def build_file_tree(tree, states, repo, parent="", path="", depth=0):
    """Recursively builds the file tree with indentation and excludes gitignored & non-code files."""
    # Clear existing tree items first
    if parent == "":
        for item in tree.get_children():
            tree.delete(item)
        states.clear()
    
    try:
        items = sorted(os.listdir(path))
    except PermissionError:
        return  # Skip folders we don't have permission to access
    
    for item in items:
        full_path = os.path.join(path, item)
        rel_path = os.path.relpath(full_path, os.getcwd())

        # Check if the path is ignored by Git
        if repo and repo.ignored(full_path):
            continue

        is_folder = os.path.isdir(full_path)
        ext = os.path.splitext(item)[1].lower()
        if not is_folder and ext not in ALLOWED_EXTENSIONS:
            continue  # Skip files with excluded extensions

        expander = "▶" if is_folder else ""
        iid = rel_path
        tree.insert(parent, "end", iid=iid, values=("🔲", expander, " " * (depth * 4) + (f"📁 {item}" if is_folder else f"📄 {item}")), open=False)
        states[iid] = 0

        if is_folder:
            build_file_tree(tree, states, repo, parent=iid, path=full_path, depth=depth + 1)

def toggle_selection(event):
    """Handles checkbox selection efficiently."""
    item = tree.identify_row(event.y)
    column = tree.identify_column(event.x)
    if not item or column != "#1":
        return

    new_state = 1 - states[item]
    batch_update_states(item, new_state)
    update_tree_checkboxes()

def toggle_expander(event):
    """Toggles folder expansion without affecting selection."""
    item = tree.identify_row(event.y)
    column = tree.identify_column(event.x)
    if not item or column != "#2":
        return

    tree.item(item, open=not tree.item(item, "open"))
    update_tree_expanders()

def update_tree_expanders():
    """Updates the expander symbols based on folder state."""
    for item in tree.get_children():
        if os.path.isdir(item):
            expander = "▼" if tree.item(item, "open") else "▶"
            tree.set(item, column="#2", value=expander)

def batch_update_states(item, state):
    """Efficiently updates the checkbox state of a folder and its children."""
    stack = [item]
    while stack:
        current = stack.pop()
        states[current] = state
        stack.extend(tree.get_children(current))
    update_parent_state(item)

def update_parent_state(item):
    """Updates the parent's state based on children (all selected, some selected, none selected)."""
    parent = tree.parent(item)
    if not parent:
        return
    
    children = tree.get_children(parent)
    child_states = [states[child] for child in children]
    
    if all(state == 1 for state in child_states):
        states[parent] = 1
    elif any(state == 1 for state in child_states):
        states[parent] = 2
    else:
        states[parent] = 0
    
    update_tree_checkboxes()
    update_parent_state(parent)

def update_tree_checkboxes():
    """Updates checkboxes display efficiently."""
    for item, state in states.items():
        if tree.exists(item):  # Check if item still exists in tree
            tree.set(item, column="#1", value="✅" if state == 1 else "◇" if state == 2 else "🔲")

def export_files():
    """Exports selected files to Markdown format."""
    selected_files = [item for item, checked in states.items() if checked == 1 and os.path.isfile(item)]
    if not selected_files:
        messagebox.showwarning("⚠️ No Selection", "Please select at least one file.")
        return
    
    save_path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown Files", "*.md")])
    if not save_path:
        return
    
    with open(save_path, "w", encoding="utf-8") as f:
        for file in selected_files:
            f.write(f"### 📄 {file}\n```")
            with open(file, "r", encoding="utf-8", errors="ignore") as src:
                f.write(src.read())
            f.write("\n```\n\n")
    
    messagebox.showinfo("✅ Export Complete", f"Exported to {save_path}")

# ===================== EXTENSION MANAGEMENT =====================

def add_extension():
    """Adds a new extension to exclude list."""
    ext = simpledialog.askstring("Add Extension", "Enter extension to exclude (e.g., .pdf):")
    if not ext:
        return
    
    # Ensure extension starts with a dot
    if not ext.startswith('.'):
        ext = '.' + ext
    
    ext = ext.lower()
    if ext in ALLOWED_EXTENSIONS:
        ALLOWED_EXTENSIONS.remove(ext)
        update_extension_listbox()
        status_label.config(text=f"✅ Excluded: {ext}")
    else:
        status_label.config(text=f"⚠️ {ext} is already excluded")

def remove_extension():
    """Re-allows a previously excluded extension."""
    selected = excluded_extensions_listbox.curselection()
    if not selected:
        status_label.config(text="⚠️ No extension selected")
        return
    
    ext = ALL_EXTENSIONS[selected[0]]
    ALLOWED_EXTENSIONS.add(ext)
    update_extension_listbox()
    status_label.config(text=f"✅ Re-allowed: {ext}")

def update_extension_listbox():
    """Updates the listbox of excluded extensions."""
    global ALL_EXTENSIONS
    excluded_extensions_listbox.delete(0, tk.END)
    
    # Get all known extensions for display
    ALL_EXTENSIONS = sorted([ext for ext in ALL_CODE_EXTENSIONS if ext not in ALLOWED_EXTENSIONS])
    
    for ext in ALL_EXTENSIONS:
        excluded_extensions_listbox.insert(tk.END, ext)

def rescan_files():
    """Rescans files based on current exclusion settings."""
    status_label.config(text="🔄 Rescanning files...")
    root.update()
    build_file_tree(tree, states, repo, path=os.getcwd())
    status_label.config(text="✅ Rescan complete")

# ===================== GUI SETUP =====================

root = tk.Tk()
root.title("📂 File Exporter & Git Diff Exporter")
root.geometry("900x600")

# Main frame to hold everything
main_frame = ttk.Frame(root)
main_frame.pack(fill="both", expand=True)

# Left frame for tree
left_frame = ttk.Frame(main_frame)
left_frame.pack(side="left", fill="both", expand=True)

# Right frame for extension management
right_frame = ttk.Frame(main_frame, width=200)
right_frame.pack(side="right", fill="y", padx=10, pady=10)
right_frame.pack_propagate(False)

# Tree setup
columns = ("Checkbox", "Expander", "Filename")
tree = ttk.Treeview(left_frame, columns=columns, selectmode="none", show="headings")

tree.column("#1", width=50, anchor="center")
tree.column("#2", width=30, anchor="center")
tree.column("#3", width=500, anchor="w")

tree.heading("#1", text="✔")
tree.heading("#2", text=" ")
tree.heading("#3", text="📂 Filename")

tree_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=tree_scroll.set)

tree_scroll.pack(side="right", fill="y")
tree.pack(side="left", fill="both", expand=True)

tree.bind("<ButtonRelease-1>", toggle_selection)
tree.bind("<Button-1>", toggle_expander)

export_button = ttk.Button(left_frame, text="📥 Export Selected Files", command=export_files)
export_button.pack(pady=10)

# Extension management UI
ttk.Label(right_frame, text="Extension Management", font=("", 12, "bold")).pack(pady=(0, 10))

# All known code extensions (for reference)
ALL_CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".cs", ".rb", ".go", ".rs", ".php", 
                      ".html", ".css", ".scss", ".sass", ".less", ".json", ".xml", ".yaml", ".yml", ".md", ".swift", 
                      ".kt", ".dart", ".lua", ".pl", ".sh", ".bat", ".ps1", ".sql", ".r", ".m", ".h", ".hpp", ".cc"}

# Global variable to track excluded extensions for the listbox
ALL_EXTENSIONS = []

# Create and populate listbox of excluded extensions
ttk.Label(right_frame, text="Excluded Extensions:").pack(anchor="w")
excluded_extensions_listbox = tk.Listbox(right_frame, height=15, width=25)
excluded_extensions_listbox.pack(fill="x", pady=5)

# Buttons for extension management
button_frame = ttk.Frame(right_frame)
button_frame.pack(fill="x", pady=5)

add_button = ttk.Button(button_frame, text="➕ Add", command=add_extension)
add_button.pack(side="left", expand=True, fill="x", padx=2)

remove_button = ttk.Button(button_frame, text="➖ Remove", command=remove_extension)
remove_button.pack(side="right", expand=True, fill="x", padx=2)

# Rescan button
rescan_button = ttk.Button(right_frame, text="🔄 Rescan Files", command=rescan_files)
rescan_button.pack(fill="x", pady=10)

# Status label
status_label = ttk.Label(right_frame, text="Ready", anchor="center")
status_label.pack(fill="x", pady=5)

# Initialize states
states = {}

# Initialize Git repo
git_root = get_git_root()
repo = None
if git_root:
    try:
        repo = git.Repo(git_root)
    except git.exc.InvalidGitRepositoryError:
        pass

# Setup initial UI state
update_extension_listbox()
build_file_tree(tree, states, repo, path=os.getcwd())

root.mainloop()