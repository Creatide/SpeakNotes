#!python3.10

import os
import json
import random
import string

from pathlib import Path
from datetime import datetime, timedelta

# ============================================================================ #
# UTILITIES                                                                    #
# ============================================================================ #


class Utilities:
    def __init__(self) -> None:
        pass

    # Create Date And Id ------------------------------------------------------ #
    def create_date_and_id(self, random_date=False):
        date_now = None
        if random_date:
            date_now = datetime.now() - timedelta(days=random.randint(1, 1000))
        else:
            date_now = datetime.now()
        date = date_now.strftime("%d.%m.%Y")
        id = date_now.strftime("%Y%m%d%H%M%S%f")
        return {"date": date, "id": id, "datetime": date_now}

    # Remove Punctuations ----------------------------------------------------- #
    def remove_punctuations(self, text):
        return "".join([c for c in text if c not in string.punctuation])
    
    # Delete File ------------------------------------------------------------- #
    def delete_file(self, filename, folder_path=Path.cwd()):
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File has been deleted from {file_path}")
            return True
        else:
            print(f"File does not exist in {file_path}")
            return False

    # Load File From Path ----------------------------------------------------- #
    def load_file(self, path=Path.cwd(), format="json"):
        if format == "json":
            with open(path, "r") as f:
                data = json.load(f)
        return data

    # Load Json Files To Dict ------------------------------------------------- #
    def load_json_files_to_dict(self, folder_path=Path.cwd()):
        path = folder_path
        data = []
        for filename in os.listdir(path):
            if filename.endswith(".json"):
                with open(os.path.join(path, filename), "r") as f:
                    data.append(json.load(f))
        return data

    # Find Index By Name ------------------------------------------------------ #
    def find_index_by_name(self, name, lst):
        try:
            return lst.index(name)
        except ValueError:
            return None

    # Update Json File Data -------------------------------------------------- #
    def update_json_data(self, key="key", value="", new_data={}, replace_data=True):
        with open("./data/settings.json", "r") as f:
            settings = json.load(f)
        for option in settings:
            if option[key] == value:
                if isinstance(option["options"], list):
                    if replace_data:
                        option["options"] = new_data
                    else:
                        option["options"].extend(new_data)
                elif isinstance(option["options"], dict):
                    option["options"].update(new_data)
                elif isinstance(option["options"], str):
                    if replace_data:
                        option["options"] = [new_data]
                    else:
                        option["options"].append(new_data)
        with open("./data/settings.json", "w") as f:
            json.dump(settings, f, indent=4)

    # Save File To Path ------------------------------------------------------ #
    def save_file(
        self,
        data,
        path=Path.cwd(),
        name="",
        format="json",
        prefix="",
        suffix="",
    ):
        filename = ""

        if not os.path.exists(path):
            os.makedirs(path)

        if not name:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            filename = str(timestamp)
        else:
            filename = name

        filename = prefix + filename + suffix + "." + format
        path = os.path.join(path, filename)

        with open(path, "w") as f:
            if format == "json":
                with open(path, "w") as f:
                    json.dump(data.__dict__(), f, indent=4)
            else:
                f.write(str(data))
