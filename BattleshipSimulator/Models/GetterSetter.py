class GetterSetter:

    def  __init__(self):
        self.children = {}
        self.parent = None
    
    def add_child(self, child_name, child_object):
        if child_name in self.children:
            raise KeyError(f"This object already has a '{child_name}' child")
        self.children[child_name] = child_object
        child_object.parent = self
    
    def get_children(self):
        return [k for k in self.children]
    
    def get_child(self, child_name):
        return self.children[child_name]

    def get_attribute(self, variable_name, traversed = False):
        if ":" not in variable_name:
            return getattr(self, variable_name)
        else:
            child_name, child_variable_name = variable_name.split(":", maxsplit = 1)
            # If the child name is in this object, continue down the tree
            if child_name in self.children:
                return self.children[child_name].get_attribute(child_variable_name, True)
            # Else, if there is no calling parent, go up the tree to the parent and attempt to find a matching element
            # If there is a calling parent, then assume that there is a typo in the tree string
            elif self.parent is not None and not traversed:
                return self.parent.get_attribute(variable_name)
            else:
                #TODO: raise a better key error
                _ = self.children[child_name]

    def set_attribute(self, variable_name, value, traversed = False):
        if ":" not in variable_name:
            setattr(self, variable_name, value)
        else:
            child_name, child_variable_name = variable_name.split(":", maxsplit = 1)
            # If the child name is in this object, continue down the tree
            if child_name in self.children:
                self.children[child_name].set_attribute(child_variable_name, value, True)
            # Else, if there is no calling parent, go up the tree to the parent and attempt to find a matching element
            # If there is a calling parent, then assume that there is a typo in the tree string
            elif self.parent is not None and not traversed:
                self.parent.set_attribute(variable_name, value)
            else:
                #TODO: raise a better key error
                _ = self.children[child_name]