#!python3.10

import os
import random

from utils import Utilities

# ============================================================================ #
# NOTES "DATABASE"                                                             #
# ============================================================================ #

# Note Class ----------------------------------------------------------------- #
class Note:
    def __init__(self, title, date, text, summary, id):
        self.title = title
        self.date = date
        self.text = text
        self.summary = summary
        self.id = id

    def __dict__(self):
        return {
            "title": self.title,
            "date": self.date,
            "text": self.text,
            "summary": self.summary,
            "id": self.id,
        }


# Notes Class ---------------------------------------------------------------- #
class Notes:
    def __init__(self) -> None:
        self.folder_data = "./data"
        self.folder_notes = os.path.join(self.folder_data, "notes")
        self.notes_all = []
        self.active_note_id = 0

    # Create New Note -------------------------------------------------------- #
    def create_note(self, title="", text="", date="", id=None, save=True):
        
        if date and id:
            date_and_id = {"date": date, "id": id}
        else:
            date_and_id = Utilities().create_date_and_id()
            
        summary = self.create_summary(text=text)

        new_note = Note(
            title=title,
            date=date if date else date_and_id["date"],
            text=text,
            summary=summary,
            id=id if id else date_and_id["id"],
        )
        self.notes_all.append(new_note)

        if save:
            Utilities().save_file(
                name=new_note.id,
                data=new_note,
                path=os.path.join(self.folder_notes),
                format="json",
            )

    # Load Notes JSON Files -------------------------------------------------- #
    def load_notes(self):
        self.notes_all = []
        
        if not os.path.exists(self.folder_notes):
            os.makedirs(self.folder_notes)
            
        for file in os.listdir(self.folder_notes):
            if file.endswith(".json"):
                note = Utilities().load_file(
                    path=os.path.join(self.folder_notes, file),
                    format="json",
                )
                self.notes_all.append(note)
        return self.notes_all

    # Load Note By ID -------------------------------------------------------- #
    def load_note_by_id(self, id):
        self.load_notes()
        for note in self.notes_all:
            if note["id"] == id:
                return note
            
    # Delete Note By ID ------------------------------------------------------ #
    def delete_note_by_id(self, id):
        for note in self.notes_all:
            if note["id"] == id:
                self.notes_all.remove(note)
                # Delete note json file
                if Utilities().delete_file(filename=f"{id}.json", folder_path=self.folder_notes):
                    self.active_note_id = 0
                    return True
                return False
        return False

    # Create Summary --------------------------------------------------------- #
    def create_summary(self, text="", summary_length=50):
        summary = ""
        if len(text) > summary_length:
            summary = text[:summary_length]
            summary += "..."
        elif len(text) < summary_length:
            summary = text + "..."
        return summary

    # Create Example Notes For Testing --------------------------------------- #
    def create_example_notes(self, number_of_notes=1):
        words = [
            "lorem",
            "ipsum",
            "dolor",
            "sit",
            "amet",
            "consectetur",
            "adipiscing",
            "elit",
            "nunc",
            "non",
            "risus",
            "ac",
            "turpis",
            "vestibulum",
            "luctus",
            "duismod",
            "felis",
            "suspendisse",
            "in",
            "habitasse",
        ]

        for i in range(number_of_notes):
            # Create lorem ipsum text
            def lorem_ipsum(text_length=200):
                title = ""
                text = ""
                while len(text) < text_length:
                    # Create a sentence
                    sentence = ""
                    for j in range(random.randint(2, 10)):
                        sentence += random.choice(words) + " "
                    # Add a period and capitalize the first letter
                    text += (sentence[:-1] + ". ").capitalize()
                for j in range(random.randint(2, 10)):
                    title += random.choice(words) + " "
                return {"title": title.capitalize().strip(), "text": text.strip()}

            note = lorem_ipsum()
            date_and_id = Utilities().create_date_and_id(random_date=True)
            self.create_note(
                title=note["title"],
                text=note["text"],
                date=date_and_id["date"],
                id=date_and_id["id"],
            )
