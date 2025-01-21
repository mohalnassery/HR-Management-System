import os

def save_files_to_md(directory_path, output_file):
    try:
        # Open the output file in write mode
        with open(output_file, 'w', encoding='utf-8') as md_file:
            # Get a list of all files in the directory
            files = os.listdir(directory_path)
            
            # Iterate through each file in the directory
            for file_name in files:
                file_path = os.path.join(directory_path, file_name)
                
                # Check if it's a file (not a directory)
                if os.path.isfile(file_path):
                    # Write the filename in the Markdown format
                    md_file.write(f"## {file_name}\n\n")
                    
                    # Read the content of the file
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        code = file.read()
                    
                    # Write the code block in Markdown format
                    md_file.write(f"```\n{code}\n```\n\n")
        
        print(f"Output saved to {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Ask user for the directory path and output file name
    path = input("Enter the directory path: ").strip()
    output_file = input("Enter the output Markdown file name (e.g., output.md): ").strip()
    
    # Call the function
    save_files_to_md(path, output_file)
