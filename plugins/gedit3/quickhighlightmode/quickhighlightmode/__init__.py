import os
import os.path
from gettext import gettext as _
from gi.repository import GObject, Gtk, GtkSource, Gedit

ui_str = """
<ui>
    <menubar name="MenuBar">
        <menu name="ViewMenu" action="View">
            <menuitem name="QuickHighlightMode" action="QuickHighlightMode"/>
        </menu>
    </menubar>
</ui>
"""

GLADE_FILE = os.path.join(os.path.dirname(__file__), "quickhighlightmode.ui")

class QuickHighlightPlugin(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "QuickHighlightMode"
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self.dialog = None
        self.language_manager = GtkSource.LanguageManager.get_default()
        langs = self.language_manager.get_language_ids()
        self.model = Gtk.ListStore(str)
        self.available_ids = {}

        for id in langs:
            lang = self.language_manager.get_language(id)
#            mimes = lang.get_mime_types()
            name = lang.get_name()
            self.available_ids[name.upper()] = id
            self.model.append([name])

        actions = [
            ('QuickHighlightMode', Gtk.STOCK_SELECT_COLOR, _('Quick Highlight Mode'),
              '<Control><Shift>h', _("Press Ctrl+Shift+H for quick highlight selection"),
            self.on_open)
        ]

        action_group = Gtk.ActionGroup("QuickHighlightModeActions")
        action_group.add_actions(actions, self.window)

        self.statusbar = self.window.get_statusbar()
        self.context_id = self.statusbar.get_context_id("QuickHighlightMode")
        self.message_id = None

        self.manager = self.window.get_ui_manager()
        self.manager.insert_action_group(action_group, -1)
        self.manager.add_ui_from_string(ui_str)

    def on_open(self, *args):
        glade_xml = Gtk.Builder.new()
        glade_xml.add_from_file(GLADE_FILE)

        if self.dialog:
            self.dialog.set_focus(True)
            return

        self.dialog = glade_xml.get_object('quickhighlight_dialog')
        self.dialog.connect('delete_event', self.on_close)
        self.dialog.show_all()
        self.dialog.set_transient_for(self.window)

        self.combo = glade_xml.get_object('language_list')

        self.cancel_button = glade_xml.get_object('cancel_button')
        self.cancel_button.connect('clicked', self.on_cancel)

        self.apply_button = glade_xml.get_object('apply_button')
        self.apply_button.connect('clicked', self.on_apply)

        self.combo.set_model(self.model)
#        self.combo.set_entry_text_column(0)

        self.completion = Gtk.EntryCompletion()
        self.completion.connect('match-selected', self.on_selected)
        self.completion.set_model(self.model)
        self.completion.set_text_column(0)

        self.entry = self.combo.get_child()
        self.entry.set_completion(self.completion)

    def close_dialog(self):
        self.dialog.destroy()
        self.dialog = None

    def on_selected(self, completion, model, iter):
        lang = model.get_value(iter, 0)
        self.set_mime_type(lang)

    def on_close(self, *args):
        self.close_dialog()

    def on_cancel(self, *args):
        self.close_dialog()

    def on_apply(self, *args):
        lang = self.combo.get_active_text()
        self.set_mime_type(lang)

    def set_mime_type(self, lang):
        lang = lang.upper()

        if self.available_ids.has_key(lang):
            lang_id = self.available_ids[lang]
            view = self.window.get_active_view()
            buffer = view.get_buffer()
            language = GtkSource.LanguageManager.get_default().get_language(lang_id)
            buffer.set_language(language)

        self.close_dialog()
