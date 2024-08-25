from dotenv import load_dotenv
import os
import sys
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
    title_case_words = [word.capitalize() if word.lower() not in exceptions else word.lower()
                        for i, word in enumerate(words)]
    # Ensure the first word is always capitalized
    title_case_words[0] = title_case_words[0].capitalize()
    return " ".join(title_case_words)


def get_new_filename(old_filename):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user",
            "content": f"Rename the following concert file to the format <Artist> - <ConcertName> - <Year>: {old_filename}. Only return the filename (with extension) and nothing else."}
    ]
    response = client.chat.completions.create(model="gpt-3.5-turbo",
                                              messages=messages,
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
    if len(sys.argv) != 2:
        print("Usage: python script.py /path/to/directory")
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
            print(f'Renaming "{old_filename}" to "{new_filename}"')
            # Uncomment the following line when ready to perform the actual renaming
            # os.rename(old_filepath, new_filepath)
