"""Convert an Obsidian vault into a collection of Markdown notes readable by Cosma (https://cosma.graphlab.fr/en/)

Usage: python obsidian2cosma.py -i input_folder_path -o output_folder_path
                                [--type TYPE] [--tags TAGS]
                                [--typedlinks TYPEDLINKS] [--semanticsection SEMANTICSECTION]
                                [--method METHOD]
                                [--attrreplacement ATTRIBUTEPAIR1[, ATTRIBUTEPAIR2 ...]]
                                [--zettlr ZETTLR]
                                [-f] [--ignore]
                                [--verbose]
Optional arguments:
  -h, --help                            Show this help message and exit
  --type TYPE                           Select notes with type TYPE (e.g --type "article")
  --tags TAGS                           Select notes with tags TAGS (e.g --tags "philosophy truth")
  --typedlinks TYPEDLINKS               Syntax of typed links modified if TYPEDLINKS=True (e.g --typedlinks True)
  --semanticsection SEMANTICSECTION     Specify in which section typed links are (e.g --semanticsection "## Typed links")
  --method METHOD                       Fill the ID with the specified Method (e.g --METHOD ctime).
                                        Fill the ID with file creation date if METHOD=ctime (Not recommended),
                                        or with attribute 'abbrlink' in front-matter if METHOD=abbrlink.
  --attrreplacement ATTRIBUTEPAIRS      Rename front-matter attributes of a record. (e.g --attrreplacement categories,types).
                                        Use a comma to separate two attributes in a pair.
                                        And you can type attribute pairs as many as you want.
                                        Spaces cannot exist in an attribute pair, but can be used between pairs.
  --ignore                              Don't copy the creation time when copying files from the source directory.
                                        If the method to fill the ID by ctime was designated, this option will be invalid.
  -f, --force                           Force overwrite output directory if it already exists.
  --zettlr ZETTLR                       Use Zettlr syntax for wiki-links if ZETTLR=True (e.g --zettlr True)
  -v, --verbose                         Print changes in the terminal

Editor of This version: Wanqin Wu
Contact: 2472963374@qq.com
Original Author: Kévin Polisano
Contact: kevin.polisano@cnrs.fr

License: GNU General Public License v3.0

"""

# TODO: 检查并发表 fork（查一下有没有fork后merge回去的先例，纯属好奇）
# TODO: 中英文档，分两个文件夹
# TODO：中英博客文章
# TODO：另写脚本。修剪html
# TODO：部署至hexo，实现自动化流程
# TODO: 添加中英文注释
# TODO：项目宣传（Obsidian原帖宣传、Obsidian中文论坛宣传）
# TODO: 你需要知道，这是为了减少平台依赖性而重写YAML解析与生成的
# TODO: 为什么要使用abbrlink，在README中写上

import os
import platform
import argparse
import re
import shutil
import csv
import unicodedata
from datetime import datetime as dt
from pathlib import Path
import binascii

# Create an ArgumentParser object
parser = argparse.ArgumentParser(epilog="See more information on https://github.com/uuanqin/obsidian2cosma.")

# Add command line arguments
parser.add_argument("-i", "--input", help="Path to the input folder", required=True)
parser.add_argument("-o", "--output", help="Path to the output folder", required=True)
parser.add_argument("--type", help="Select notes with type TYPE (e.g --type 'article')", default=None)
parser.add_argument("--tags", help="Select notes with tags TAGS (e.g --tags 'philosophy truth')", default=None)
parser.add_argument("--typedlinks", help="Syntax of typed links modified if TYPEDLINKS=True (e.g --typedlinks True)",
                    default=False)
parser.add_argument("--semanticsection",
                    help="Specify in which section typed links are (e.g --semanticsection '## Typed links')",
                    default=None)
parser.add_argument("--method",
                    type=str,
                    help="Specify a method to generate ID (e.g --method ctime)",
                    default="default")
parser.add_argument("--attrreplacement",
                    type=str,
                    help="Rename front-matter attributes of a record. (e.g --attrreplacement categories,types)",
                    nargs="*")
parser.add_argument("--zettlr", help="Use Zettlr syntax for wiki-links if ZETTLR=True", default=False)
parser.add_argument("--ignore", action='store_true',
                    help='Do not copy the creation time when copying files from the source directory')
parser.add_argument("-f", "--force", action='store_true', help='Force overwrite output directory if it already exists')
parser.add_argument("-v", "--verbose", action='store_true', help='Print changes in the terminal')

# Parse the command line arguments
args = parser.parse_args()

# Input and output folders path
input_folder = args.input
output_folder = args.output

# Initialize an ID with the current date timestamp
currentId = int(dt.fromtimestamp(dt.now().timestamp()).strftime('%Y%m%d%H%M%S'))
# Initialize conflict ID counter
total_conflict_ID = 0


# Print function displaying text if option --verbose is used
def printv(text):
    if args.verbose:
        print(text)


def creation_date(file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See https://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        # On windows, it means the creation time for path.
        # See https://docs.python.org/3.10/library/os.path.html#os.path.getctime
        return os.path.getctime(file)
    else:
        stat = os.stat(file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime


def copy_system_birthtime(source, destination):
    """Assign the creation date of source file to destination file"""
    # Get the creation date of source file
    timestamp = creation_date(source)
    # The function that changes a file's creation time depends on OS.
    if platform.system() == 'Windows':
        # It takes a long time to evoke Powershell to excute a command.
        birthtime = dt.fromtimestamp(timestamp).strftime('%d %b %Y %X')
        str_cmd = f"Powershell -Command (Get-Item \'{destination}\').CreationTime=(\'{birthtime}\')"
        # Another solution but takes time too.
        # dt_obj = dt.fromtimestamp(timestamp)
        # str_cmd = f"Powershell $NewDate = Get-Date -Year {dt_obj.year} -Month {dt_obj.month} -Day {dt_obj.day} -Hour {dt_obj.hour} -Minute {dt_obj.minute} -Second {dt_obj.second} ; \
        #     Set-ItemProperty -Path '{destination}' -Name CreationTime -Value $NewDate"
    else:
        # Convert in the format YYYYMMDDHHmm.ss (see man touch)
        birthtime = dt.fromtimestamp(timestamp).strftime('%Y%m%d%H%M.%S')
        # Assign source file's creation date to destination's one (but also overwrite access and modification dates)
        # Can use instead on Mac OSX: SetFile -d "$(GetFileInfo -d source)" destination to avoid this issue
        str_cmd = "touch -t " + birthtime + " " + "\"" + destination + "\""
    os.system(str_cmd)


def create_id(file, front_matter: dict):
    """
    Function to create an id. The method of this creation depends on the option the user designated.
    """
    global currentId
    # Create an id by the 'abbrlink' attrbute in front-matter
    if args.method == 'abbrlink':
        # If the front-matter contains 'abbrlink' attribute, then use it.
        if 'abbrlink' in front_matter.keys():
            hex_abbr = str(front_matter['abbrlink']).strip('\'')
        # Otherwise generate an ID by using the crc32 algorithm.
        else:
            # The source string is the 'title' attribute in front matter.
            # Assume that the 'title' attribute is exists.
            hex_abbr = crc32_str2hex(front_matter['title'])
        # Identifier of the record must be a unique number.
        # See https://cosma.arthurperret.fr/user-manual.html#configuration
        return int("0x" + hex_abbr, 16)
    # If the files creation date are available
    elif args.method == 'ctime':
        # To create an 14-digit id by timestamp (year, month, day, hours, minutes and seconds) corresponding to the file creation date
        # Retrieve the file creation date
        timestamp = creation_date(file)
        # Convert the date to a string in the format YYYYMMDDHHMMSS
        return dt.fromtimestamp(timestamp).strftime('%Y%m%d%H%M%S')
    # Otherwise create ad-hoc IDs by incrementing the current ID (initialized with current date)
    else:
        currentId = currentId + 1
        return currentId


def parse_yaml_front_matter(content):
    """
    Parses YAML front matter from a Markdown file (More general).
    Now it can recognize Block Mode and Flow Mode of the YAML specification (See https://cosma.arthurperret.fr/user-manual.html#metadata).
    Also, it can process Line Folding (See https://yaml.org/spec/1.2.2/).
    """
    match = re.match(r"^---\n(.*?)\n---(.*)", content, re.DOTALL)
    data = {}
    if match:
        # Divide a markdown file to two parts: the front-matter and the remaining content.
        front_matter = match.group(1)
        content = match.group(2)
        block_mode_attribute = None
        line_fold_attribute = None
        # Parse yaml by lines.
        for line in front_matter.split("\n"):
            # If the line is the first line of an attribute.
            if re.match(r"^([a-zA-Z-_]+):(.*)$", line):
                match_obj = re.match(r"^([a-zA-Z-_]+):(.*)$", line, re.DOTALL)
                key = match_obj.group(1)
                value = match_obj.group(2)
                value = value.strip(" \'\"")
                value = convert2num_if_possible(value)
                # A line like 'attribute: ', which means that it uses Block Mode.
                if not value:
                    # A mark to indicate that we should treat the next line as one of the parameter of the attribute.
                    block_mode_attribute = key
                    data[key] = []
                    continue
                # A line like 'attribute: >-', which means that it uses Line Folding.
                elif value == '>-':
                    # A mark to indicate that we should treat the next line as one of the parameter of the attribute.
                    line_fold_attribute = key
                    data[key] = ''
                    continue
                # Otherwise, treat the line as a common key-value pair.
            # Parse a line that is in Block Mode.
            elif block_mode_attribute and re.match(r"^\s*-\s(.*)$", line):
                match_obj = re.match(r"^\s*-\s(.*)$", line)
                data[block_mode_attribute].append(match_obj.group(1).strip())
                continue
            # Parse a line that is in Line Folding.
            elif line_fold_attribute:
                data[line_fold_attribute] = data[line_fold_attribute] + line.strip(" \'\"")
                continue
            else:
                printv(f"[WARNING] Unknown YAML line: {line}")
                continue

            block_mode_attribute = None
            line_fold_attribute = None

            # Parse a line that is in Flow Mode.
            if isinstance(value, str) and re.match(r"\[(.*)\]", value, re.DOTALL):
                match_obj = re.match(r"\[(.*)\]", value, re.DOTALL)
                value = match_obj.group(1)
                # Remove the brackets from the string
                value = value.strip("[]")
                # Split the string on commas and store the resulting list of tags
                value = value.split(",")
                # Strip any leading or trailing whitespace from each tag
                value = [convert2num_if_possible(v.strip()) for v in value]
            data[key] = value
    return data, content


def convert_dict2_yaml_front_matter(d: dict) -> str:
    """Convert a dictionary of Python to the front matter (YAML)"""
    front_matter = "---\n"
    for k, v in d.items():
        front_matter = front_matter + f"{k}: {str(v)}\n"
    return front_matter + "---\n"


def convert2num_if_possible(value):
    """ Parse values as integers or floats if possible, otherwise keep as string"""
    try:
        value = int(value)
    except ValueError:
        try:
            # Check the number to avoid the peculiar bugs occur, such as '13e4' converts to 130000.0
            if str(float(value)) != value:
                raise ValueError
            else:
                value = float(value)
        except ValueError:
            pass
    return value


def filter_files(root, files, type=None, tags=None):
    """
    Filters a list of Markdown files based on the given type and tags, and images.
    Also, you can set the cosma configuration file ('record_filters' parameter) to achieve this.
    See https://cosma.arthurperret.fr/user-manual.html
    """
    filtered_files = []
    for file in files:
        # Select Markdown files
        if file.endswith(".md"):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Extract the YAML front matter
                front_matter, _ = parse_yaml_front_matter(content)
                if tags:
                    # Check for tags in the front matter
                    yaml_tags = front_matter.get("tags", [])
                    if isinstance(yaml_tags, str):
                        yaml_tags = [yaml_tags]
                    file_tags_set = set(yaml_tags)
                    printv("\t - YAML tags: {}".format(file_tags_set))
                    # Check for tags in the content
                    content_tags = re.findall(r"#(\w+)", content)
                    printv("\t - Content #tags: {}".format(set(content_tags)))
                    file_tags_set = file_tags_set.union(set(content_tags))
                    printv("\t - All file tags: {}".format(file_tags_set))
                    # Set of tags passing in arguments
                    if isinstance(tags, str):
                        if " " in tags:
                            tags_temp = tags.split()
                        else:
                            tags_temp = [tags]
                    filter_tags_set = set(tags_temp)
                    printv("\t - Filter tags: {}".format(filter_tags_set))
                    # Compare the two sets of tags: if filter TAGS are not part of file tags then it is not selected
                    if not filter_tags_set.issubset(file_tags_set):
                        printv("[IGNORED] {} (missing tags)".format(file))
                        continue
                # If type field is missing then the file is not selected
                if type and "type" not in front_matter:
                    printv("[IGNORED] {} (missing type)".format(file))
                    continue
                # If type field exists but is not consistent with TYPE then the file is not selected
                if type and "type" in front_matter and front_matter["type"] != type:
                    printv("[IGNORED] {} (different type)".format(file))
                    continue
                # Otherwise the file is selected
                printv("[SELECTED] {}".format(file))
                filtered_files.append(file)
        if file.endswith(".jpg") or file.endswith(".jpeg") or file.endswith(".png"):
            printv("[SELECTED] {}".format(file))
            filtered_files.append(file)
    return filtered_files


def copy_and_filter_files(input_folder, output_folder):
    """Function to copy all Markdown files and images from the input folder and its subfolders to the output folder"""
    printv("\n=== Filtering files and copying them in the output folder ===\n")
    for root, dirs, files in os.walk(input_folder):
        # Ignore subfolders that start with an underscore. See https://stackoverflow.com/questions/19859840/excluding-directories-in-os-walk.
        dirs[:] = [d for d in dirs if not d.startswith("_")]
        # Filter Markdown files based on the given type and tags
        filtered_files = filter_files(root, files, type=args.type, tags=args.tags)
        for file in filtered_files:
            # Copy current file from the input folder to output folder
            shutil.copy2(os.path.join(root, file), output_folder)  # copy2() preserve access and modifications dates
            # Do not copy the creation time when copying files from the source directory if '--ignore' was designated.
            if not args.ignore:
                copy_system_birthtime(os.path.join(root, file), os.path.join(output_folder,
                                                                             file))  # but birthtime (= creation date) has to be set up manually


def metadata_init(files) -> dict:
    """Function to initialize metadata and save them in a csv file
    Find (or create) the title and id fields in the YAML frontmatter of all Markdown files
    Return a dictionary title2id["title"] = "id"
    """
    global total_conflict_ID
    printv("\n=== Initialize or complete metadata of filtered files ===\n")
    title2id = {}
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            all_text = f.read()
        # Extract the YAML front matter
        front_matter, content = parse_yaml_front_matter(all_text)
        # Search for the ID and title fields
        id = front_matter.get("id")
        title = front_matter.get("title")
        # At this stage no ID or title are created
        idcreated = False
        titlecreated = False
        # If the title field does not exist, then create one.
        # Make sure the 'title' attribute is exists before generate an ID.
        if title is None:
            # Extract the filename (file without path and extension)
            title = Path(file).stem
            printv('[COMPLETED] {}:\n \t - Title created'.format(os.path.basename(file)))
            front_matter['title'] = title
            titlecreated = True
        # If the id field does not exist, then create one
        if id is None:
            id = create_id(file, front_matter)
            if titlecreated:
                printv('\t - Id created')
            else:
                printv('[COMPLETED] {}:\n \t - Id {} created'.format(os.path.basename(file), id))
            front_matter['id'] = id
            idcreated = True
        # No ID or title have been created means the file already contains ones
        if not idcreated and not titlecreated:
            printv('[OK] {}'.format(os.path.basename(file)))
        # Detect the ID conflict
        if id in title2id.values():
            printv(f'[ID CONFLICT] {id}')
            total_conflict_ID = total_conflict_ID + 1
        # The value "id" is associated to the key "title" in a dictionary
        title2id[title] = id
        # Change attributes' names
        if args.attrreplacement is not None:
            for pair in args.attrreplacement:
                old_name, new_name = pair.split(",")
                if old_name in front_matter.keys():
                    front_matter[new_name] = front_matter.pop(old_name)
        # Finally, write the front matter and content back to the markdown file.
        with open(file, "w", encoding="utf-8") as f:
            f.write(convert_dict2_yaml_front_matter(front_matter) + content)
    # Write the results to a CSV file
    # csvname = os.path.basename(input_folder) + '_title2id.csv'
    csvname = os.path.join(output_folder, '_title2id.csv')
    with open(csvname, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(title2id.items())
    # Return the dictionary
    return title2id


def replace_wiki_links(file, title2id):
    """Function to replace every single wiki-style [[internal link]] in a Markdown file with [[id | internal link]]
    where internal link refers to the title (possibily with an alias) of an other Markdown file
    whose id can be found in the dictionary title2id
    Eventually transforms image wiki-links ![[image.{jpg,jpeg,png}]] to ![](image.{jpg,jpeg,png})"""
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    global count  # Variable counting the number of links replaced
    count = 0

    # Function replacing one internal link matched
    def replace_wiki_link(match):
        global count
        count = count + 1
        # Extract the [[link_text]]
        link_text = match.group(1)
        # If this link text contains an alias ([[title | alias]])
        if "|" in link_text:
            # Separate the title from the alias
            link_title, link_alias = link_text.split("|")
            # If the title is not in the dictionary, there is no corresponding Markdown file (ghost note)
            if link_title not in title2id:
                return f"[[{link_text}]]"  # Keep the original link
            # Otherwise find the corresponding ID of this file
            id = title2id[link_title]
            # If Zettlr syntax: Return [alias]([[id]])
            if args.zettlr:
                return f"[{link_alias.strip()}]([[{id}]])"
            # Return [[id | alias]]
            return f"[[{id}|{link_alias.strip()}]]"
        # Otherwise link_text = title
        else:
            # If the title is not in the dictionary, there is no corresponding Markdown file (ghost note)
            if link_text not in title2id:
                return f"[[{link_text}]]"  # Keep the original link
            # Otherwise find the corresponding ID of this file
            id = title2id[link_text]
            # If Zettlr syntax: Return [title]([[id]])
            if args.zettlr:
                return f"[{link_text}]([[{id}]])"
            # Return [[id | title]]
            return f"[[{id}|{link_text}]]"

    # Substitute all wiki links match with replace_wiki_link(match)
    content = re.sub(r"(?<!!)\[\[(.+?)\]\](?!\()", replace_wiki_link, content)
    # Eventually let replace images wiki-link
    pattern = r'!\[\[(.+?\.jpe?g|.+?\.png)\]\]'  # ![[image.{jpg,jpeg,png}]]
    matches = re.finditer(pattern, content)
    # Transform ![[image.{jpg,jpeg,png}]] to ![](image.{jpg,jpeg,png})
    for match in matches:
        image_link = match.group(1)
        content = content.replace(match.group(0), '![]({})'.format(image_link))
        count = count + 1
    printv("[{} links replaced] {}".format(count, os.path.basename(file)))
    # Write the results in the file
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)


def transform_typed_links(file):
    """Function to transform typed links as "- prefix [[destination]]" into the format "[[prefix:destination]]"
    prefix is a word characterizing the type of the directional link between the current file and another one (destination)
    In Obsdian, such semantic links can be drawn with the syntax of the Juggl plugin: https://juggl.io/Link+Types
    """
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    # Find the section corresponding to SEMANTICSECTION
    if args.semanticsection is not None:
        pattern = r"(?:^|\n)%s[^\n]*\n(.*?)(?=\n##?\s|$)" % args.semanticsection
        match = re.search(pattern, content, re.DOTALL)
        if match:
            printv("Semantic section << {} >> found".format(args.semanticsection))
            # Extract the content of this section
            section = match.group(1)
            # Transform typed links as "- prefix [[destination]]" into the format "[[prefix:destination]]"
            section = re.sub(r"- (.*?) \[\[(.*?)\]\]", r"[[\1:\2]]", section)
            # Substitute the old content section by the new one
            new_string = "{}\n{}\n".format(args.semanticsection, section)
            content = content.replace(match.group(0), new_string)
    # If not found then replace typed links everywhere
    else:
        content = re.sub(r"- (.*?) \[\[(.*?)\]\]", r"[[\1:\2]]", content)
    # Save changes
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)


def rename_file(file):
    """Function to rename a file by replacing spaces with hyphens"""
    # Remove accents
    # new_name = unicodedata.normalize("NFD", file).encode("ascii", "ignore").decode("utf-8")
    new_name = unicodedata.normalize("NFD", file).encode("utf-8", "ignore").decode("utf-8")

    # Replace spaces with hyphens
    new_name = new_name.replace(" ", "-")
    # Write the new filename
    os.rename(file, new_name)


def crc32_str2hex(string: str) -> str:
    """
    Encode a string in crc32 algorithm, then return a 4 Bytes string in hexadecimal.
    Inspired by https://github.com/rozbo/hexo-abbrlink.
    """
    str_bin = string.encode('utf-8')
    return '%08x' % (binascii.crc32(str_bin) & 0xffffffff)


def main():
    # If the method to fill the ID by ctime was designated (Option '--method ctime'), option '--ignore' will be invalid.
    if args.method == 'ctime':
        if args.ignore:
            printv(f'[MESSAGE] Option --ignore is invalid.')
        args.ignore = False

    # Force overwrite output directory if it already exists
    if args.force and os.path.isdir(output_folder):
        shutil.rmtree(output_folder)
        Path(output_folder).mkdir(parents=True)
        printv(f"[MESSAGE] Force overwrite output directory.")
    else:
        # If the output folder does not exist, then create one.
        try:
            Path(output_folder).mkdir(parents=True)
        except FileExistsError as fe:
            print("[ERROR] Output folder already exists, or try -f option.")
            print(f"[ERROR] {fe.args}")
            exit(1)

    # Copy all Markdown files and images from the input folder and subfolders to the output folder
    copy_and_filter_files(input_folder, output_folder)

    # Store the list of Markdown files within the output folder
    filenames = [file for file in os.listdir(output_folder) if file.endswith(".md")]
    files = [os.path.join(output_folder, file) for file in filenames]

    # Initialize YAML metadata of the selected files, fill a dictionary title -> id and save it into a csv file
    title2id = metadata_init(files)

    # Replace links in a format compatible with Cosma
    printv("\n=== Replacing wiki links ===\n")
    for file in files:
        # Replace every single wiki-style [[internal link]] in a Markdown file with [[id | internal link]]
        replace_wiki_links(file, title2id)
        # Transform typed links as "- prefix [[destination]]" into the format "[[prefix:destination]]"
        if args.typedlinks:
            transform_typed_links(file)

    # Rename files by removing accents and replacing spaces with hyphens
    for file in files:
        rename_file(file)


if __name__ == "__main__":
    # Calculate the program run time
    start_dt = dt.now()
    main()
    end_dt = dt.now()
    printv(f"[FINISHED] Total ID conflict: {total_conflict_ID}")
    printv(f"[FINISHED] Time cost: {(end_dt - start_dt).seconds} s")
