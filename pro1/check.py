import subprocess
import os
import re
import xml.etree.ElementTree as ET

#----------------------------------------------------Recommendation ------------------------------------------
def get_see_also_section(command):
    try:
        result = subprocess.run(['man', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        man_page = result.stdout

        # Use regex to find the 'SEE ALSO' section
        match = re.search(r'SEE ALSO(.*?)\n\n', man_page, re.S)

        if match:
            return match.group(1).strip()
        else:
            return "No 'SEE ALSO' section found."

    except Exception as e:
        return f"Error occurred: {e}"

#----------------------------------------------------Searching---------------------------------------------------------
def run_research(word):
    word = word.lower()
    files = os.listdir('.')
    found = False
    for filename in files:
        if filename.endswith('_manual.xml'):
            with open(filename, 'r') as file:
                if word in file.read().lower():
                    print(f"Found in {filename}")
                    found = True
    
    if not found:
        print("No commands related to this word were found.")

###------------------------------------------------- Verification ----------------------------------------

def fetch_manual_info(command):
    # Fetch the manual page description and related commands
    man_page = subprocess.run(f"man {command}", shell=True, capture_output=True, text=True)
    description = version = related = None
    if man_page.returncode == 0 and man_page.stdout:
        # Extract description
        description_match = re.search(r"DESCRIPTION(.+?)(?=\n\n)", man_page.stdout, re.DOTALL)
        if description_match:
            description = description_match.group(1).strip()

        # Extract related commands
        related_match = re.search(r"SEE ALSO(.+?)(?=\n\n)", man_page.stdout, re.DOTALL)
        if related_match:
            related = related_match.group(1).strip()

    # Fetch the version information
    version_info = subprocess.run(f"{command} --version", shell=True, capture_output=True, text=True)
    if version_info.returncode == 0 and version_info.stdout:
        version = version_info.stdout.split('\n')[0]

    return description, version, related

# Function to verify XML content against manual pages
def verify_xml(xml_file, command):
    try:
        # Parse the generated XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        return [f"XML parsing error in file: {xml_file} - {e}"]

    # Fetch the original manual information
    original_description, original_version, original_related = fetch_manual_info(command)

    # Compare each element
    xml_description = root.find('description').text
    xml_version = root.find('version').text
    xml_related = root.find('related').text

    discrepancies = []
    if xml_description != original_description:
        discrepancies.append(f"Description mismatch for {command}")
    if xml_version and original_version and xml_version.strip() != original_version.strip():
        discrepancies.append(f"Version mismatch for {command}")
    if xml_related and original_related and xml_related.strip() != original_related.strip():
        discrepancies.append(f"Related commands mismatch for {command}")

    return discrepancies

# Function to verify all commands in the input file
def verify_all_commands(input_file):
    with open(input_file, 'r') as file:
        commands = [line.strip() for line in file.readlines()]

    for command in commands:
        xml_file = f"{command}_manual.xml"
        if not os.path.exists(xml_file):  # Check if the XML file exists
            print(f"Warning: No XML file found for {command}. Skipping verification.")
            continue
        discrepancies = verify_xml(xml_file, command)
        if discrepancies:
            for discrepancy in discrepancies:
                print(discrepancy)
        else:
            print(f"No discrepancies found for {command}.")

#***************************************************


# -------------------------------------------------CommandManual class------------------------------------------------------------------------------------
class CommandManual:
    def __init__(self, command, example_inputs=[]):
        self.command = command.strip()
        self.description = "No description available"
        self.version = "No version information available"
        self.related_commands = "No related commands information available"
        self.example_inputs = example_inputs
        self.examples = []

    def run_command(self, command, shell=False):
        try:
            result = subprocess.run(command, capture_output=True, text=True, shell=shell)
            if result.returncode != 0:
                return None
            return result
        except subprocess.CalledProcessError:
            return None

    def extract_description(self):
        man_command = f"man {self.command}"
        result = self.run_command(man_command, shell=True)
        if result and result.stdout:
            match = re.search(r"DESCRIPTION(.+?)(?=\n\n)", result.stdout, re.DOTALL)
            if match:
                self.description = match.group(1).strip()

    def extract_version(self):
        version_command = f"{self.command} --version"
        result = self.run_command(version_command.split())
        if result and result.stdout:
            self.version = result.stdout.split('\n')[0]

    def extract_related_commands(self):
        man_command = f"man {self.command}"
        result = self.run_command(man_command, shell=True)
        if result and result.stdout:
            match = re.search(r"SEE ALSO(.+?)(?=\n\n)", result.stdout, re.DOTALL)
            if match:
                self.related_commands = match.group(1).strip()

    def run_example_commands(self):
        for example_input in self.example_inputs:
            try:
                command_string = ' '.join(example_input)
                result = subprocess.run(command_string, capture_output=True, text=True, shell=True)
                example_output = result.stdout if result.stdout else "No output or error"
                self.examples.append({"input": ' '.join(example_input), "output": example_output})
            except Exception as e:
                self.examples.append({"input": ' '.join(example_input), "output": f"Error: {e}"})


# -------------------------------------------------XmlSerializer class -----------------------------------------------------------------------------
class XmlSerializer:
    @staticmethod
    def serialize(command_manual):
        xml_content = "<?xml version='1.0' encoding='utf-8'?>\n"
        xml_content += "<command>\n"
        xml_content += f"  <name>{command_manual.command}</name>\n"
        xml_content += f"  <description>{command_manual.description}</description>\n"
        xml_content += f"  <version>{command_manual.version}</version>\n"
        xml_content += f"  <related>{command_manual.related_commands}</related>\n"
        xml_content += "  <examples>\n"
        for example in command_manual.examples:
            xml_content += f"    <example>\n"
            xml_content += f"      <input>{example['input']}</input>\n"
            xml_content += f"      <output>{example['output']}</output>\n"
            xml_content += f"    </example>\n"
        xml_content += "  </examples>\n"
        xml_content += "</command>"
        return xml_content


# ---------------------------------------------CommandManualGenerator class-----------------------------------------------------------
class CommandManualGenerator:
    def __init__(self, command_examples):
        self.command_manuals = [CommandManual(command, examples) for command, examples in command_examples.items()]

    def generate_manuals(self):
        for command_manual in self.command_manuals:
            command_manual.extract_description()
            command_manual.extract_version()
            command_manual.extract_related_commands()
            command_manual.run_example_commands()
            output_filename = f"{command_manual.command}_manual.xml"
            xml_content = XmlSerializer.serialize(command_manual)
            self.save_to_file(xml_content, output_filename)


    def save_to_file(self, content, filename):
        with open(filename, "w", encoding='utf-8') as xml_file:
            xml_file.write(content)


# ---------------------------------------------------Example usage-----------------------------------------------------------------
command_examples = {
    "pwd": [["pwd"]],
    "head": [["head", "input_file.txt"]],
    "tail": [["tail", "input_file.txt"]],
    "mv": [["mv", "file.txt", "file.txt"]],
    "sort": [["sort -n", "remover.txt"]],  # Sort lines of text in a file
    "uniq": [["uniq", "remover.txt"]],  # Report or omit repeated lines in a file
    "mkdir": [["mkdir", "directory"]],
    "rmdir": [["rmdir", "directory"]],
    "chmod": [["chmod", "644", "file.txt"]],  # Example: Change file permissions
    "chown": [["chown", "user:group", "file.txt"]],  # Example: Change file owner
    "grep": [["grep", "good", "file.txt"]],  # Example: Search for a pattern in a file
    "find": [["find", ".", "-name", "file.txt"]],  # Example: Find files by name
   # "who": [["who"]],  # Example: List logged-in users
  #  "man": [["man", "ls"]],  # Example: Display manual page for ls
    "cat": [["cat", "file.txt"]],  # Example: Display contents of a file
    "sed": [["sed", "s/oldText/newText/g", "file.txt"]],
    "awk": [["awk", "/pattern/ {print $0}", "file.txt"]],
   # "ps": [["ps", "aux"]],  # Example: Display all running processes
    "diff": [["diff", "file.txt", "example.txt"]],  # Compare two files
    "ln": [["ln", "-s", "/path/to/file", "/path/to/symlink"]],  # Create a symbolic link to a file
    "chgrp": [["chgrp", "group", "file.txt"]],  # Change the group ownership of a file
    "free": [["free", "-m"]]  # Display memory usage in MB
    
}


while True: 
    print("-----------------------------------------------------------MENU ---------------------------------------------------------")
    print("Which script would you like to run?\n")
    print("1) Generate Commands\n")
    print("2) Verify commands\n")
    print("3) Search commands\n")
    print("4) Recommendation commands\n")
    print("0) EXIT THE PROGRAM ")
        
    input_choice = input("PLEASE CHOOSE ONE OF THE RECOMMENDED (1/2/3/4): ")
        
    if input_choice == '1':
        manual_generator = CommandManualGenerator(command_examples)
        manual_generator.generate_manuals()
    
    elif input_choice == '2':
        verify_all_commands('input_file.txt')

    elif input_choice == '3':
        word = input("Please Enter The Word You Are Looking For: ")
        run_research(word) 
        input2 =input("1) Do You Want To Find the Recommendation commands? By entering a yes or no\n")
        if input2 == "yes":
            with open('input_file.txt', 'r') as file:
                commands = [line.strip() for line in file]
                cmd=input("please chose a  command : \n")
                see_also = get_see_also_section(cmd)
                print(f"Command: {cmd}\nSee Also:\n{see_also}\n")
        else:
            pass

    elif input_choice == '4':
        with open('input_file.txt', 'r') as file:
            commands = [line.strip() for line in file]
            cmd=input("please enter what command you are lokking at: ")
            see_also = get_see_also_section(cmd)
            print(f"Command: {cmd}\nSee Also:\n{see_also}\n")


    elif input_choice == '0':  # Condition to break the loop
        print("Exiting the program.")
        break  # Exit the loop # Exit the loop

    else:
        pass


