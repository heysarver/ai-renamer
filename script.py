from dotenv import load_dotenv
import os
import sys
import re
from openai import OpenAI

client = OpenAI()

# Load environment variables from .env file
load_dotenv()

# Setup OpenAI API key
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    print("Please set your OpenAI API key in the .env file or as an environment variable.")
    sys.exit(1)


def to_title_case(text):
    """
    Convert text to title case, capitalizing only the necessary words.
    """
    exceptions = ["a", "an", "and", "the", "but", "for",
                  "or", "nor", "on", "at", "to", "by", "with"]
    words = text.split()
    title_case_words = []
    capitalize_next = True

    for word in words:
        if capitalize_next or word.lower() not in exceptions:
            title_case_words.append(word.capitalize())
        else:
            title_case_words.append(word.lower())

        # Check if the word ends with a hyphen
        if word.endswith('-'):
            capitalize_next = True
        else:
            capitalize_next = False

    # Ensure the first word is always capitalized
    title_case_words[0] = title_case_words[0].capitalize()
    return " ".join(title_case_words)


def get_new_filename(old_filename):
    # Check if the filename contains a 4-digit year
    year_match = re.search(r'\b\d{4}\b', old_filename)
    year = year_match.group(0) if year_match else ""

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",
            "content": f"Rename the following concert file to the format <Artist> - <ConcertName>{' - <Year>' if year else ''}: {old_filename}. Only return the filename (with extension) and nothing else. NEVER include \"The New Filename Should Be:\" in your response, only return the new filename.  If there's a Live on <something> in the original filename include that in the output filename.  Convert all non-english characters to english characters e.g. ö to o."},
    ]
    response = client.chat.completions.create(model="gpt-4",
                                              messages=messages,
                                              temperature=0.4,
                                              max_tokens=60)

    try:
        new_filename = response.choices[0].message.content.strip()

        # Post-process to ensure proper title capitalization
        if '.' in new_filename:  # Ensure we don't alter the file extension
            name_part, extension = new_filename.rsplit('.', 1)
            name_part = to_title_case(name_part)
            new_filename = f"{name_part}.{extension}"
        else:
            new_filename = to_title_case(new_filename)

        return new_filename
    except Exception as e:
        print(f"Failed to get a new name for {old_filename}: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py [--noop] /path/to/directory")
        sys.exit(1)

    noop = False
    folder_path = ""

    if "--noop" in sys.argv:
        noop = True
        if len(sys.argv) != 3:
            print("Usage: python script.py [--noop] /path/to/directory")
            sys.exit(1)
        folder_path = sys.argv[2]
    else:
        if len(sys.argv) != 2:
            print("Usage: python script.py [--noop] /path/to/directory")
            sys.exit(1)
        folder_path = sys.argv[1]

    if not os.path.isdir(folder_path):
        print(f"The path {folder_path} is not a valid directory.")
        sys.exit(1)

    files = os.listdir(folder_path)

    for old_filename in files:
        old_filepath = os.path.join(folder_path, old_filename)
        new_filename = get_new_filename(old_filename)

        if new_filename:
            new_filepath = os.path.join(folder_path, new_filename)
            if noop:
                print(f'Would rename "{old_filename}" to "{new_filename}"')
            else:
                print(f'Renaming "{old_filename}" to "{new_filename}"')
                os.rename(old_filepath, new_filepath)
        else:
            # Handle filenames without a 4-digit year
            base_name, extension = os.path.splitext(old_filename)
            new_base_name = to_title_case(
                base_name.replace('_', ' ').replace('-', ' '))
            new_filename = f"{new_base_name}{extension}"
            new_filepath = os.path.join(folder_path, new_filename)
            if noop:
                print(f'Would rename "{old_filename}" to "{new_filename}"')
            else:
                print(f'Renaming "{old_filename}" to "{new_filename}"')
                os.rename(old_filepath, new_filepath)
