import sys, time, os
import string, threading
from task import Task

try:
    import pygtk
    pygtk.require("2.0")
except:
      pass
try:
    import gtk
    import gtk.glade
    import gobject
except:
    sys.exit(1)

class TaskEditor :
    def __init__(self, task, refresh_callback=None) :
        self.gladefile = "gtd-gnome.glade"
        self.wTree = gtk.glade.XML(self.gladefile, "TaskEditor")
        #Create our dictionay and connect it
        dic = {
                "mark_as_done_clicked"       : self.change_status,
                "delete_clicked"        : self.delete_task,
              }
        self.wTree.signal_autoconnect(dic)
        self.window = self.wTree.get_widget("TaskEditor")
        self.textview = self.wTree.get_widget("textview")
        self.task = task
        self.refresh = refresh_callback
        buff = gtk.TextBuffer()
        texte = self.task.get_text()
        title = self.task.get_title()
        #the first line is the title
        #If we don't have text, it's also valid
        if texte :
            sepa = '\n'
            to_set = sepa.join([title,texte])
        else : 
            to_set = title
        buff.set_text(to_set)
        self.textview.set_buffer(buff)
        self.window.connect("destroy", self.close)
        self.window.show_all()
    
    def change_status(self,widget) :
        stat = self.task.get_status()
        if stat == "Active" :
            toset = "Done"
        elif stat == "Done" :
            toset = "Active"
        self.task.set_status(toset)
        self.close(None)
        self.refresh()
    
    def delete_task(self,widget) :
        print "implement delete task from the editor"
    
    def save(self) :
        #the text buffer
        buff = self.textview.get_buffer()
        #the tag table
        table = buff.get_tag_table()
        #we get the text
        texte = buff.get_text(buff.get_start_iter(),buff.get_end_iter())
        #We should have a look at Tomboy Serialize function 
        #NoteBuffer.cs : line 1163
        #Currently, we are not saving the tag table.
        content = texte.partition('\n')
        self.task.set_title(content[0])
        self.task.set_text(content[2])
        if self.refresh :
            self.refresh()
        self.task.sync()
        
    def close(self,window) :
        #Save should be also called when buffer is modified
        self.save()
        #TODO : verify that destroy the window is enough ! 
        #We should also destroy the whole taskeditor object.
        self.window.destroy()
