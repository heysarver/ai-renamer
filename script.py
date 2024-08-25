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


def get_new_filename(old_filename, output_format):
    # Check if the filename contains a 4-digit year starting with 19xx or 20xx
    year_match = re.search(r'\b(19|20)\d{2}\b', old_filename)
    year = year_match.group(0) if year_match else ""

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",
            "content": f"Rename the following concert file to the format {output_format}: {old_filename}. Only return the filename (with extension) and nothing else. NEVER include \"The New Filename Should Be:\" in your response, only return the new filename. If there's a Live on <something> in the original filename include that in the output filename. Convert all non-english characters to english characters e.g. ö to o. Always include a year if there is a 19xx or 20xx 4 digit number in the filename, leave that section of the filename out if unknown. Any errors just skip the file by not renaming it."},
    ]
    response = client.chat.completions.create(model="gpt-4",
                                              messages=messages,
                                              temperature=0.4,
                                              max_tokens=60)

    try:
        new_filename = response.choices[0].message.content.strip()

        # Check for error message and skip if found
        if "Without the Original Filename" in new_filename or "As an Ai" in new_filename:
            return None

        # Post-process to ensure proper title capitalization
        if '.' in new_filename:  # Ensure we don't alter the file extension
            name_part, extension = new_filename.rsplit('.', 1)
            name_part = to_title_case(name_part)
            new_filename = f"{name_part}.{extension}"
        else:
            new_filename = to_title_case(new_filename)

        # Remove any trailing dashes or spaces
        new_filename = re.sub(r' -$', '', new_filename).strip()

        return new_filename
    except Exception as e:
        print(f"Failed to get a new name for {old_filename}: {e}")
        return None


if __name__ == "__main__":
    noop = "--noop" in sys.argv
    output_format = "<Standardized US English Name>"
    folder_path = None

    for arg in sys.argv[1:]:
        if arg.startswith("--output-format="):
            output_format = arg.split("=", 1)[1]
        elif arg != "--noop":
            folder_path = arg

    if not folder_path:
        folder_path = "/app/dir"

    if not os.path.isdir(folder_path):
        print(f"The path {folder_path} is not a valid directory.")
        sys.exit(1)

    files = os.listdir(folder_path)

    for old_filename in files:
        old_filepath = os.path.join(folder_path, old_filename)
        new_filename = get_new_filename(old_filename, output_format)

        if new_filename and '?' not in new_filename:
            new_filepath = os.path.join(folder_path, new_filename)
            if noop:
                print(f'Would rename "{old_filename}" to "{new_filename}"')
            else:
                print(f'Renaming "{old_filename}" to "{new_filename}"')
                os.rename(old_filepath, new_filepath)
        else:
            print(
                f'Skipping "{old_filename}" due to error in renaming or invalid characters in the new filename.')
