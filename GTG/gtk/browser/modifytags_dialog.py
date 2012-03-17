# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Gettings Things Gnome! - a personal organizer for the GNOME desktop
# Copyright (c) 2008-2012 - Lionel Dricot & Bertrand Rousseau
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
""" A dialog for batch adding/removal of tags """
# FIXME pylint, pyflakes, pep8
import gtk

from GTG import _
from GTG.gtk.browser import GnomeConfig


class ModifyTagsDialog:
    """ Dialog for batch adding/removal of tags """

    def __init__(self, req):
        self.req = req
        self.tasks = []

        self._init_dialog()

        # Rember values from last time
        self.last_tag_entry = _("NewTag")
        self.last_apply_to_subtasks = False

    def _init_dialog(self):
        """ Init .glade file """
        builder = gtk.Builder()
        builder.add_from_file(GnomeConfig.MODIFYTAGS_GLADE_FILE)
        builder.connect_signals({
            "on_modifytags_confirm":
                self.on_confirm,
            "on_modifytags_cancel":
                lambda dialog: dialog.hide,
        })

        self.tag_entry = builder.get_object("tag_entry")
        self.apply_to_subtasks = builder.get_object("apply_to_subtasks")
        self.dialog = builder.get_object("modifytags_dialog")

    def modify_tags(self, tasks):
        """ Show and run dialog for selected tasks """
        if len(tasks) == 0:
            return

        self.tasks = tasks

        self.tag_entry.set_text(self.last_tag_entry)

        #FIXME completion
        #FIXME diacritic
        #self.tag_entry.set_completion(self.tag_completion)
        self.tag_entry.grab_focus()
        self.apply_to_subtasks.set_active(self.last_apply_to_subtasks)

        self.dialog.run()
        self.dialog.hide()

        self.tasks = []

    # FIXME write unittests
    # FIXME parse in tools/*
    # FIXME: make sure that '!' is not allowed first character of tagname (tag handling should be unified)
    def parse_entry(self, text):
        """ parse entry and return list of tags to add and remove """
        positive = []
        negative = []
        tags = [tag.strip() for by_space in text.split()
                                for tag in by_space.split(",")]

        for tag in tags:
            if tag == "":
                continue

            is_positive = True
            if tag.startswith('!'):
                tag = tag[1:]
                is_positive = False

            if not tag.startswith('@'):
                tag = "@" + tag

            if is_positive:
                positive.append(tag)
            else:
                negative.append(tag)

        return positive, negative

    def on_confirm(self, widget):
        """ apply changes """
        new_tags, del_tags = self.parse_entry(self.tag_entry.get_text())

        # If the checkbox is checked, find all subtasks
        if self.apply_to_subtasks.get_active():
            for task_id in self.tasks:
                task = self.req.get_task(task_id)
                # FIXME: Python not reinitialize the default value of its
                # parameter therefore it must be done manually. This function
                # should be refractored # as far it is marked as depricated
                for subtask in task.get_self_and_all_subtasks(tasks=[]):
                    subtask_id = subtask.get_id()
                    if subtask_id not in self.tasks:
                        self.tasks.append(subtask_id)

        for task_id in self.tasks:
            task = self.req.get_task(task_id)
            for new_tag in new_tags:
                task.add_tag(new_tag)
            for del_tag in del_tags:
                task.remove_tag(del_tag)
            task.sync()

        # Rember the last actions
        self.last_tag_entry = self.tag_entry.get_text()
        self.last_apply_to_subtasks = self.apply_to_subtasks.get_active()
