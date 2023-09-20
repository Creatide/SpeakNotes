#!python3.10

import platform, os

# https://github.com/kivy/kivy/issues/6908
if platform.system() == 'Windows':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import string
from datetime import datetime, timedelta
from notes import Notes
from asr import ASR
from utils import Utilities

# ============================================================================ #
# USER INTERFACE: IMPORTS & SETTINGS                                           #
# ============================================================================ #

import kivy

from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set("graphics", "width", "720")
Config.set("graphics", "height", "1280")

from kivy.config import ConfigParser
from kivy.uix.settings import SettingsWithNoMenu

from kivy.app import App
from kivy.clock import Clock

from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.properties import ObjectProperty, StringProperty, DictProperty, ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.core.text import LabelBase

LabelBase.register(name="IconFont", fn_regular="./assets/icons.ttf")


# ============================================================================ #
# USER INTERFACE: PARTS                                                        #
# ============================================================================ #


class UserSettingsMenu(SettingsWithNoMenu):
    def __init__(self, **kwargs):
        super(UserSettingsMenu, self).__init__(**kwargs)
        self.add_json_panel("User Settings", main_app.config, "./data/settings.json")

    def on_config_change(self, config, section, key, value):
        main_app.load_settings_from_ini()


# ClickableItem -------------------------------------------------------------- #
class ClickableItem(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super(ClickableItem, self).__init__(**kwargs)

    def on_press_item(self, *args):
        print(f"Clicked: {self.data}")
        main_app.screen_manager.change_screen("screen_preview", self.data["id"])
        # scrollable_list = self.parent.parent.parent.parent
        # scrollable_list.add_data(new_data)


# ScrollableList ------------------------------------------------------------- #
class ScrollableListItem(BoxLayout):
    data = DictProperty({"title": "", "date": "", "summary": ""})


class ScrollableList(BoxLayout):
    data = ListProperty([])

    def __init__(self, **kwargs):
        super(ScrollableList, self).__init__(**kwargs)
        self.bind(data=self.update_list)

    def update_list(self, *args):
        self.ids.list_layout.clear_widgets()
        for item in self.data:
            self.ids.list_layout.add_widget(ScrollableListItem(data=item))

    def add_data(self, new_data):
        current_data = self.data
        current_data.append(new_data)
        self.data = current_data
        self.update_list()


# ============================================================================ #
# USER INTERFACE: SCREENS                                                      #
# ============================================================================ #

# ScreenNotes ---------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #
class ScreenNotes(Screen):
    def on_enter(self):
        main_app.notes.active_note_id = 0
        scrollable_list = self.ids.scrollable_list
        scrollable_list.data = main_app.notes.load_notes()

    def on_release_button_newnote(self):
        main_app.screen_manager.current = "screen_record"


# ScreenRecord --------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #
class ScreenRecord(Screen):
    def __init__(self, **kwargs):
        super(ScreenRecord, self).__init__(**kwargs)
        self.asr = main_app.asr
        self.start_time = timedelta(0)
        self.pause_time = timedelta(0)
        self.total_paused_time = timedelta(0)
        self.session_duration = timedelta(0)
        self.is_paused = False
        self.session_running = False
        self.session_ended = False

        # Session info
        self.session_info_set = False
        self.session_title = ""
        self.session_date = None
        self.session_id = None

        Clock.schedule_once(self.initialize_session, 0.5)

        # Get all buttons with id starting with "record_button_"
        self.buttons = {}
        for id, button in self.ids.items():
            if id.startswith("record_button_"):
                self.buttons[id] = button

    # Initialization --------------------------------------------------------- #
    def initialize_session(self, dt=None):

        # Generate session info
        date_and_id = Utilities.create_date_and_id(self)
        self.session_info_set = False
        self.session_title = ""
        self.session_date = date_and_id["date"]
        self.session_id = date_and_id["id"]

        # Reset session
        self.asr.reset()
        self.ids.record_title.text = ""
        self.ids.record_date.text = ""
        self.ids.record_textinput.text = ""

        self.start_time = timedelta(0)
        self.pause_time = timedelta(0)
        self.total_paused_time = timedelta(0)
        self.session_duration = timedelta(0)
        self.is_paused = False
        self.session_running = False
        self.session_ended = False
        self.ids.record_time.text = "0:00:00"
        self.show_buttons(["record_button_start"])

    # Show/Hide Buttons ------------------------------------------------------ #
    def show_buttons(self, ids):
        visible_buttons = [id for id in ids if id in self.buttons]
        num_buttons = len(visible_buttons)
        for id, button in self.buttons.items():
            # Hide all buttons that are not in the list of visible buttons
            if id not in visible_buttons:
                button.opacity = 0
                button.size_hint = (0, 0)
                button.height = 0
                button.width = 0
                button.disabled = True
            # Show all buttons that are in the list of visible buttons
            else:
                button.opacity = 1
                button.size_hint = (1 / num_buttons, 1)
                button.height = self.height
                button.width = self.width / num_buttons
                button.disabled = False

    # On Enter/Leave Events -------------------------------------------------- #
    def on_enter(self):
        if not self.session_running and self.session_ended:
            self.initialize_session()

    def on_leave(self):
        if self.session_running and not self.session_ended:
            self.show_buttons(["record_button_stop", "record_button_resume"])
            self.session_pause()

    # Button Release Events -------------------------------------------------- #
    def on_release_button_start(self):
        self.show_buttons(["record_button_stop", "record_button_pause"])
        self.session_start()

    def on_release_button_stop(self):
        self.show_buttons(["record_button_discard", "record_button_save"])
        self.session_stop()

    def on_release_button_pause(self):
        self.show_buttons(["record_button_stop", "record_button_resume"])
        self.session_pause()

    def on_release_button_resume(self):
        self.show_buttons(["record_button_stop", "record_button_pause"])
        self.session_resume()

    def on_release_button_discard(self):
        self.initialize_session()

    def on_release_button_save(self):
        self.session_end()
        self.session_save()
        # Clock.schedule_once(self.initialize_session, 1)

    # Session Functions ------------------------------------------------------ #
    def session_save(self):
        if self.session_info_set:
            main_app.notes.create_note(
                title=self.session_title,
                text=self.ids.record_textinput.text,
                date=self.session_date,
                id=self.session_id,
                save=True,
            )
            main_app.screen_manager.change_screen("screen_preview", self.session_id)

    def session_start(self):
        if not self.session_running:
            self.asr.start()
            self.start_time = datetime.now()
            self.session_running = True
            Clock.schedule_interval(self.update_info_values, 0.5)
            print("Session started in: ", self.start_time.strftime("%H:%M:%S"))

    def session_pause(self):
        if not self.is_paused:
            self.asr.pause()
            self.pause_time = datetime.now()
            self.is_paused = True
            Clock.unschedule(self.update_info_values)
            print("Session paused in: ", self.pause_time.strftime("%H:%M:%S"))

    def session_resume(self):
        if self.is_paused:
            self.asr.resume()
            self.total_paused_time += datetime.now() - self.pause_time
            self.pause_time = timedelta(0)
            self.is_paused = False
            Clock.schedule_interval(self.update_info_values, 1)
            print("Session resumed in: ", datetime.now().strftime("%H:%M:%S"))

    def session_stop(self, dt=None):
        if self.session_running:

            self.asr.stop()
            Clock.unschedule(self.update_info_values)

            # Calculate total paused time if session is paused
            if self.is_paused:
                self.total_paused_time += datetime.now() - self.pause_time

            # Calculate session duration
            self.session_duration = str(
                datetime.now() - self.start_time - self.total_paused_time
            ).split(".")[0]

            self.session_running = False
            print("Session stopped in: ", datetime.now().strftime("%H:%M:%S"))

    def session_end(self):
        self.session_ended = True
        print("Session ended in: ", datetime.now().strftime("%H:%M:%S"))
        print("Session duration: ", self.session_duration)

    # Update Functions ------------------------------------------------------- #

    def update_info_values(self, dt=None):

        # Update text
        asr_text = self.asr.get_transcription()
        self.ids.record_textinput.text = " ".join(asr_text)

        # Update title and date
        if self.session_info_set == False and len(asr_text) and len(asr_text[0]):
            self.session_title = (
                self.ids.record_title.text
            ) = Utilities().remove_punctuations(asr_text[0])
            self.ids.record_date.text = self.session_date
            self.session_info_set = True

        # Update timer
        time = datetime.now() - self.start_time - self.total_paused_time
        self.ids.record_time.text = str(time).split(".")[0]


# ScreenPreview -------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #
class ScreenPreview(Screen):
    def __init__(self, **kwargs):
        super(ScreenPreview, self).__init__(**kwargs)
        self.ids.preview_text.foreground_color = (0.8, 0.8, 0.8, 1)

        Clock.schedule_once(self.initialize_session, 0.5)

        # Get all buttons with id starting with "record_button_"
        self.buttons = {}
        for id, button in self.ids.items():
            if id.startswith("preview_button_"):
                self.buttons[id] = button

    # Initialization --------------------------------------------------------- #
    def initialize_session(self, dt=None):
        # main_app.notes.load_notes()
        self.show_buttons(["preview_button_delete", "preview_button_edit"])
        self.ids.preview_title.readonly = True
        # self.ids.preview_title.disabled = True
        self.ids.preview_text.readonly = True
        # self.ids.preview_text.disabled = True

    # Show/Hide Buttons ------------------------------------------------------ #
    def show_buttons(self, ids):
        visible_buttons = [id for id in ids if id in self.buttons]
        num_buttons = len(visible_buttons)
        for id, button in self.buttons.items():
            # Hide all buttons that are not in the list of visible buttons
            if id not in visible_buttons:
                button.opacity = 0
                button.size_hint = (0, 0)
                button.height = 0
                button.width = 0
                button.disabled = True
            # Show all buttons that are in the list of visible buttons
            else:
                button.opacity = 1
                button.size_hint = (1 / num_buttons, 1)
                button.height = self.height
                button.width = self.width / num_buttons
                button.disabled = False

    # On Enter/Leave Events -------------------------------------------------- #
    def on_enter(self):
        print(main_app.notes.active_note_id)
        id = main_app.notes.active_note_id
        loaded_note = main_app.notes.load_note_by_id(id)
        self.ids.preview_title.text = loaded_note["title"]
        self.ids.preview_date.text = loaded_note["date"]
        self.ids.preview_text.text = loaded_note["text"]

    # Focus color for TextInput
    def on_textinput_focus(self, instance, value):
        if value:
            instance.foreground_color = (1, 1, 1, 1)
        else:
            instance.foreground_color = (0.8, 0.8, 0.8, 1)

    # Button Release Events -------------------------------------------------- #
    def on_release_button_edit(self):
        self.show_buttons(["preview_button_delete", "preview_button_save"])
        self.ids.preview_title.readonly = False
        # self.ids.preview_title.disabled = False
        self.ids.preview_text.readonly = False
        # self.ids.preview_text.disabled = False

    def on_release_button_save(self):
        self.save_note()
        Clock.schedule_once(self.initialize_session, 1)

    def on_release_button_delete(self):
        self.delete_note()

    # Session Functions ------------------------------------------------------ #
    def save_note(self):
        main_app.notes.create_note(
            title=self.ids.preview_title.text,
            text=self.ids.preview_text.text,
            date=self.ids.preview_date.text,
            id=main_app.notes.active_note_id,
            save=True,
        )

    def delete_note(self):
        if main_app.notes.delete_note_by_id(main_app.notes.active_note_id):
            main_app.screen_manager.current = "screen_notes"
        else:
            print("Error deleting note with id:", main_app.notes.active_note_id)


# ScreenSettings ------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #
class ScreenSettings(Screen):
    def __init__(self, **kwargs):
        super(ScreenSettings, self).__init__(**kwargs)

        Utilities().update_json_data(
            value="michrophone",
            new_data=main_app.asr.get_mic_devices(),
            replace_data=True,
        )

        Utilities().update_json_data(
            value="model",
            new_data=main_app.asr.whisper_all_models,
            replace_data=True,
        )

        self.settings = UserSettingsMenu()
        self.ids.settings_boxlayout.add_widget(self.settings)


# ScreenManagement ----------------------------------------------------------- #
# ---------------------------------------------------------------------------- #
class ScreenManagement(ScreenManager):
    def __init__(self, **kwargs):
        super(ScreenManagement, self).__init__(**kwargs)
        self.transition = NoTransition()
        # self.asr = ObjectProperty(ASR())
        self.note_id = 0
        self.initialize()

    def initialize(self):
        print("ScreenManagement.initialize called")
        global main_screens
        main_screens = [
            ScreenNotes(name="screen_notes"),
            ScreenRecord(name="screen_record"),
            ScreenPreview(name="screen_preview"),
            ScreenSettings(name="screen_settings"),
        ]

        for screen in main_screens:
            self.add_widget(screen)

        self.current = "screen_notes"

    def change_screen(self, screen_name, note_id=0):
        main_app.notes.active_note_id = note_id
        self.current = screen_name


# ============================================================================ #
# MAIN APP                                                                     #
# ============================================================================ #


class MainApp(App):
    def __init__(self, **kwargs):
        super(MainApp, self).__init__(**kwargs)

        self.notes = Notes()
        self.screen_manager = None
        self.config = None
        self.asr = ASR()

        # Debug -------------------------------------------------------------- #
        # self.notes.create_example_notes(number_of_notes=20)

    # Create Kivy UI --------------------------------------------------------- #
    def build(self):
        self.config = ConfigParser()
        self.config.read("./data/settings.ini")
        self.load_settings_from_ini()
        self.screen_manager = ScreenManagement()
        return self.screen_manager

    def load_settings_from_ini(self):
        # Set mic device
        self.asr.set_mic_device(self.config.get("Settings", "michrophone"))
        # Set whisper model name and load it
        model = self.asr.load_whisper_model(self.config.get("Settings", "model"))
        self.config.set("Settings", "model", model)
        # Set energy threshold
        self.asr.recognizer.energy_threshold = self.config.getint(
            "Settings", "energy_threshold"
        )

    # System Info Details ---------------------------------------------------- #
    def system_info(self):
        print("Kivy version:", kivy.__version__)
        print("Current PyTorch device is set to:", self.pytorch_device)


global main_app
main_app = None

if __name__ == "__main__":
    main_app = MainApp()
    main_app.run()
