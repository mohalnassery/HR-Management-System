import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import git
import fnmatch

# ========================= UTILITY FUNCTIONS =========================

def get_git_ignored_files():
    """Returns a set of files and folders ignored by .gitignore."""
    ignored_files = set()
    try:
        repo = git.Repo(os.getcwd(), search_parent_directories=True)
        git_root = repo.git.rev_parse("--show-toplevel")
        git_ignore_path = os.path.join(git_root, ".gitignore")

        if os.path.exists(git_ignore_path):
            with open(git_ignore_path, "r") as f:
                ignored_patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]

            for root, dirs, files in os.walk(git_root):
                for pattern in ignored_patterns:
                    if fnmatch.filter([root], pattern):
                        ignored_files.add(os.path.relpath(root, git_root))
                    for file in files:
                        if fnmatch.fnmatch(file, pattern):
                            ignored_files.add(os.path.relpath(os.path.join(root, file), git_root))
    except:
        pass
    return ignored_files

# ========================= TREE STRUCTURE HANDLING =========================

def build_file_tree(tree, states, ignored_files, parent="", path="", depth=0):
    """Recursively builds the file tree with indentation."""
    for item in sorted(os.listdir(path)):
        full_path = os.path.join(path, item)
        rel_path = os.path.relpath(full_path, os.getcwd())

        if rel_path in ignored_files:
            continue  # Skip ignored files and folders

        is_folder = os.path.isdir(full_path)
        expander = "▶" if is_folder else ""  # Expander for directories

        iid = rel_path  # Unique ID for each item in the tree
        tree.insert(parent, "end", iid=iid, values=("🔲", expander, " " * (depth * 4) + item), open=False)

        states[iid] = 0  # Default unselected

        if is_folder:
            build_file_tree(tree, states, ignored_files, parent=iid, path=full_path, depth=depth + 1)

def toggle_selection(event):
    """Handles checkbox selection only when clicking on the checkbox column."""
    item = tree.identify_row(event.y)
    column = tree.identify_column(event.x)

    if not item or column != "#1":  # Ensure clicking in first column only (checkbox column)
        return

    new_state = 1 - states[item]  # Toggle state
    set_recursive_state(item, new_state)
    update_tree_checkboxes()

def toggle_expander(event):
    """Toggles folder expansion without affecting selection."""
    item = tree.identify_row(event.y)
    column = tree.identify_column(event.x)

    if not item or column != "#2":  # Ensure clicking in second column only (expander column)
        return

    tree.item(item, open=not tree.item(item, "open"))
    update_tree_expanders()

def update_tree_expanders():
    """Updates the expander symbols based on folder state."""
    for item in tree.get_children():
        if os.path.isdir(item):
            expander = "▼" if tree.item(item, "open") else "▶"
            tree.set(item, column="#2", value=expander)

def set_recursive_state(item, state):
    """Recursively sets the checkbox state of an item and all its children."""
    states[item] = state
    for child in tree.get_children(item):
        set_recursive_state(child, state)

    update_parent_state(item)

def update_parent_state(item):
    """Updates the parent's state based on children (all selected, some selected, none selected)."""
    parent = tree.parent(item)
    if not parent:
        return

    children = tree.get_children(parent)
    child_states = [states[child] for child in children]

    if all(state == 1 for state in child_states):
        states[parent] = 1  # All selected ✅
    elif any(state == 1 for state in child_states):
        states[parent] = 2  # Partially selected ◇
    else:
        states[parent] = 0  # None selected 🔲

    update_tree_checkboxes()
    update_parent_state(parent)

def update_tree_checkboxes():
    """Updates checkboxes display to reflect selection state."""
    for item in states:
        if states[item] == 1:
            symbol = "✅"
        elif states[item] == 2:
            symbol = "◇"
        else:
            symbol = "🔲"

        tree.set(item, column="#1", value=symbol)

def export_files():
    """Exports selected files to Markdown format."""
    selected_files = [item for item, checked in states.items() if checked == 1 and os.path.isfile(item)]
    
    if not selected_files:
        messagebox.showwarning("No Selection", "Please select at least one file.")
        return

    save_path = filedialog.asksaveasfilename(defaultextension=".md", filetypes=[("Markdown Files", "*.md")])
    if not save_path:
        return
    
    with open(save_path, "w", encoding="utf-8") as f:
        for file in selected_files:
            f.write(f"### {file}\n```\n")
            with open(file, "r", encoding="utf-8", errors="ignore") as src:
                f.write(src.read())
            f.write("\n```\n\n")
    
    messagebox.showinfo("Export Complete", f"Exported to {save_path}")

# ========================= GUI SETUP =========================

root = tk.Tk()
root.title("File Exporter & Git Diff Exporter")
root.geometry("700x500")

columns = ("Checkbox", "Expander", "Filename")
tree = ttk.Treeview(root, columns=columns, selectmode="none", show="headings")

tree.column("#1", width=50, anchor="center")
tree.column("#2", width=30, anchor="center")
tree.column("#3", width=500, anchor="w")

tree.heading("#1", text="✔")
tree.heading("#2", text=" ")
tree.heading("#3", text="Filename")

tree.pack(fill="both", expand=True)
tree.bind("<ButtonRelease-1>", toggle_selection)
tree.bind("<Button-1>", toggle_expander)

export_button = ttk.Button(root, text="Export Selected Files", command=export_files)
export_button.pack()

states = {}
ignored_files = get_git_ignored_files()
build_file_tree(tree, states, ignored_files, path=os.getcwd())

root.mainloop()
