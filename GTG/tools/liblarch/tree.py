# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Gettings Things Gnome! - a personal organizer for the GNOME desktop
# Copyright (c) 2008-2009 - Lionel Dricot & Bertrand Rousseau
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

import gobject

from GTG.tools.logger import Log

class MainTree(gobject.GObject):
    __gsignals__ = {'node-added': (gobject.SIGNAL_RUN_FIRST, \
                                    gobject.TYPE_NONE, (str, )),
                    'node-deleted': (gobject.SIGNAL_RUN_FIRST, \
                                    gobject.TYPE_NONE, (str, )),
                    'node-modified': (gobject.SIGNAL_RUN_FIRST, \
                                    gobject.TYPE_NONE, (str, ))}

    def __init__(self, root=None):
        gobject.GObject.__init__(self)
        self.root_id = 'root'
        self.nodes = {}
        self.old_paths = {}
        self.pending_relationships = []
        if root:
            self.root = root
        else:
            self.root = TreeNode(id=self.root_id)
        self.root.set_tree(self)
        
    def modify_node(self,nid):
        self.__modified(nid)
        
    def __modified(self,nid):
        if nid != 'root' and nid in self.nodes:
            self.emit("node-modified", nid)

    def __str__(self):
        return "<Tree: root = '%s'>" % (str(self.root))

    def get_node_for_path(self, path):
        return self._node_for_path(self.root,path)

    def get_path_for_node(self, node):
        toreturn = self._path_for_node(node)
        return toreturn
        
    #a deleted path can be requested only once
    def get_deleted_path(self,id):
        toreturn = None
        print "old paths are : %s" %self.old_paths
        if self.old_paths.has_key(id):
            toreturn = self.old_paths.pop(id)
        return toreturn
            

    def get_root(self):
        return self.root

    def set_root(self, root):
        self.root = root
        self.root.set_tree(self)

    #We add a node. By default, it's a child of the root
    def add_node(self, node, parent_id=None):
        id = node.get_id()
        if self.nodes.has_key(id):
            print "Error : A node with this id %s already exists" %id
            return False
        else:
            #We add the node
            node.set_tree(self)
            if parent_id:
                parent = self.get_node(parent_id)
                if parent: 
                    node.set_parent(parent.get_id())
                    parent.add_child(id)
            else:
                self.root.add_child(id)
            self.nodes[id] = node
            #build the relationships that were waiting for that node
            for rel in list(self.pending_relationships):
                if id in rel:
                    self.new_relationship(rel[0],rel[1])
            self.emit("node-added", id)
            return True

    #this will remove a node but not his children
    #if recursive: will also remove children and children of childrens
    #does nothing if the node doesn't exist
    def remove_node(self, id,recursive=False):
        node = self.get_node(id)
        path = self.get_path_for_node(node)
        if not node :
            return
        else:
            if node.has_child():
                for c_id in node.get_children():
                    if not recursive:
                        self.break_relationship(id,c_id)
                    else:
                        self.remove_node(c_id,recursive=recursive)
            if node.has_parent():
                for p_id in node.get_parents():
                    par = self.get_node(p_id)
                    par.remove_child(id)
            else:
                self.root.remove_child(id)
            self.old_paths[id] = path
            self.emit("node-deleted", id)
            self.nodes.pop(id)
        
    #create a new relationship between nodes if it doesn't already exist
    #return False if nothing was done
    def new_relationship(self,parent_id,child_id):
        Log.debug("new relationship between %s and %s" %(parent_id,child_id))
        if [parent_id,child_id] in self.pending_relationships:
            self.pending_relationships.remove([parent_id,child_id])
        toreturn = False
        #no relationship allowed with yourself
        if parent_id != child_id:
            if parent_id == 'root':
#                Log.debug("    -> adding %s to the root" %child_id)
                p = self.get_root()
            else:
                p = self.get_node(parent_id)
            c = self.get_node(child_id)
            if p and c :
                #no circular relationship allowed
                if not p.has_parent(child_id) and not c.has_child(parent_id):
                    if not p.has_child(child_id):
                        p.add_child(child_id)
                        toreturn = True
                    if parent_id != 'root' and not c.has_parent(parent_id):
                        c.add_parent(parent_id)
                        toreturn = True
                    #removing the root from the list of parent
                    if toreturn and parent_id != 'root' and \
                                                self.root.has_child(child_id):
                        self.root.remove_child(child_id)
                    if not toreturn:
                        Log.debug("  * * * * * Relationship already existing")
                else:
                    #a circular relationship was found
                    #undo everything
                    Log.debug("  * * * * * Circular relationship found : undo")
                    self.break_relationship(parent_id,child_id)
                    toreturn = False
            else:
                #at least one of the node is not loaded. Save the relation for later
                #undo everything
                self.break_relationship(parent_id,child_id)
                #save it for later
                if [parent_id,child_id] not in self.pending_relationships:
                    self.pending_relationships.append([parent_id,child_id])
                toreturn = True
        if toreturn:
            self.__modified(parent_id)
            self.__modified(child_id)
        return toreturn
    
    #break an existing relationship. The child is added to the root
    #return False if the relationship didn't exist    
    def break_relationship(self,parent_id,child_id):
        toreturn = False
        p = self.get_node(parent_id)
        c = self.get_node(child_id)
        if p and c :
            if p.has_child(child_id):
                ret = p.remove_child(child_id)
                toreturn = True
            if c.has_parent(parent_id):
                c.remove_parent(parent_id)
                toreturn = True
                #if no more parent left, adding to the root
                if not c.has_parent():
                    self.root.add_child(child_id)
        if toreturn:
            self.__modified(parent_id)
            self.__modified(child_id)
        return toreturn
            
    #Trying to make a function that bypass the weirdiness of lists
    def get_node(self,id):
        return self.nodes.get(id)
            
    def get_all_nodes(self):
        return list(self.nodes.keys())
            
#    def get_all_nodes(self):
#        li = []
#        for k in self.nodes.keys():
#            no = self.get_node(k)
#            if no:
#                li.append(no)
#        return li

    def is_displayed(self,id):
        return self.has_node(id)

    def has_node(self, id):
        return (self.nodes.get(id) != None)

    def print_tree(self):
        self._print_from_node(self.root)

    def visit_tree(self, pre_func=None, post_func=None):
        if self.root.has_child():
            for c in self.root.get_children():
                node = self.root.get_child(c)
                self._visit_node(node, pre_func, post_func)

### HELPER FUNCTION FOR TREE #################################################
#
    def _node_for_path(self,node,path):
        if path[0] < node.get_n_children():
            if len(path) == 1:
                return node.get_nth_child(path[0])
            else:
                node = node.get_nth_child(path[0])
                path = path[1:]
                return self._node_for_path(node, path)
        else:
            return None

    def _path_for_node(self, node):
        if node: 
            if node == self.root:
                toreturn = ()
            elif not node.has_parent():
                index  = self.root.get_child_index(node.get_id())
                toreturn = self._path_for_node(self.root) + (index, )
            else:
                # no multiparent support here
                parent_id = node.get_parent()
                if len(node.get_parents()) >= 2:
                    print "multiple parents for task %s" %node.get_id()
                    print "you should use a filteredtree above this tree"
                parent = self.get_node(parent_id)
                if parent:
                    index  = parent.get_child_index(node.get_id())
                    toreturn = self._path_for_node(parent) + (index, )
                else:
                    toreturn = ()
#                    print "returning %s" %str(toreturn)
        else:
            toreturn = None
        return toreturn

    def _print_from_node(self, node, prefix=""):
        print prefix + node.id
        prefix = prefix + " "
        if node.has_child():
            for c in node.get_children():
                cur_node = node.get_child(c)
                self._print_from_node(cur_node, prefix)

    def _visit_node(self, node, pre_func=None, post_func=None):
        if pre_func:
            pre_func(node)
        if node.has_child():
            for c in node.get_children():
                cur_node = node.get_child(c)
                self._visit_node(cur_node, pre_func, post_func)
        if post_func:
            post_func(node)


class TreeNode():

    def __init__(self, id, parent=None):
        self.parents   = []
        self.id       = id
        self.children      = []
        self.tree = None
        self.pending_relationship = []
        if parent:
            self.add_parent(parent)

    def __str__(self):
        return "<TreeNode: '%s'>" % (self.id)
        
    def modified(self):
        if self.tree:
            self.tree.modify_node(self.id)
        
    def set_tree(self,tree):
        self.tree = tree
        for rel in list(self.pending_relationship):
            self.tree.new_relationship(rel[0],rel[1])
            self.pending_relationship.remove(rel)
            
    def get_tree(self):
        return self.tree

    def get_id(self):
        return self.id
        
    
    def new_relationship(self,par,chi):
        if self.tree:
            return self.tree.new_relationship(par,chi)
        else:
            self.pending_relationship.append([par,chi])
            #it's pending, we return False
            Log.debug("** There's still no tree, relationship is pending")
            return False
        
        
##### Parents

    def has_parent(self,id=None):
        if id:
            return id in self.parents
        else:
            toreturn = len(self.parents) > 0
        return toreturn
    
    #this one return only one parent.
    #useful for tree where we know that there is only one
    def get_parent(self):
        #we should throw an error if there are multiples parents
        if len(self.parents) > 1 :
            print "Warning: get_parent will return one random parent for task %s because there are multiple parents." %(self.get_id())
            print "Get_parent is deprecated. Please use get_parents instead"
        if self.has_parent():
            return self.parents[0]
        else:
            return None

    def get_parents(self):
        '''
        Return a list of parent ids
        '''
        return list(self.parents)

    def add_parent(self, parent_id):
        if parent_id not in self.parents:
            self.parents.append(parent_id)
            toreturn = self.new_relationship(parent_id, self.get_id())
#            if not toreturn:
#                Log.debug("** parent addition failed (probably already done)*")
        else:
            toreturn = False
        return toreturn
    
    #set_parent means that we remove all other parents
    #if par_id is None, we will remove all parents, thus being on the root.
    def set_parent(self,par_id):
        is_already_parent_flag = False
        for i in self.parents:
            if i != par_id:
                assert(self.remove_parent(i) == True)
            else:
                is_already_parent_flag = True
        if par_id and not is_already_parent_flag:
            self.add_parent(par_id)
        elif par_id == None:
            self.new_relationship('root', self.get_id())
            
    def remove_parent(self,id):
        if id in self.parents:
            self.parents.remove(id)
            ret = self.tree.break_relationship(id,self.get_id())
            return ret
        else:
            return False
            
###### Children

    def has_child(self,id=None):
        if id :
            return id in self.children
        else:
            return len(self.children) != 0

    def get_children(self):
        return list(self.children)

    def get_n_children(self):
        return len(self.children)

    def get_nth_child(self, index):
        try:
            id = self.children[index]
            return id
        except(IndexError):
            raise ValueError("Index is not in the children list")

    def get_child(self, id):
        if id in self.children:
            return self.tree.get_node(id)
        else:
            return None

    def get_child_index(self, id):
        if id in self.children:
            return self.children.index(id)
        else:
            return None

    #return True if the child was added correctly. False otherwise
    #takes the id of the child as parameter.
    #if the child is not already in the tree, the relation is anyway "saved"
    def add_child(self, id):
        if id not in self.children:
            self.children.append(id)
            toreturn = self.new_relationship(self.get_id(),id)
#            Log.debug("new relationship : %s" %toreturn)
        else:
            Log.debug("%s was already in children of %s" %(id,self.get_id()))
            toreturn = False
        return toreturn

    def remove_child(self, id):
        if id in self.children:
            self.children.remove(id)
            ret = self.tree.break_relationship(self.get_id(),id)
            return ret
        else:
            return False

        
    def change_id(self,newid):
        oldid = self.id
        self.id = newid
        for p in self.parents:
            par = self.tree.get(p)
            par.remove_child(oldid)
            par.add_child(self.id)
        for c in self.get_children():
            c.add_parent(newid)
            c.remove_parent(oldid)