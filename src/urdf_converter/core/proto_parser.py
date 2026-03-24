import re
"""
This module provides functionality to parse and manipulate a robot structure from a proto file.
Classes:
    proto_robot: Represents the robot structure parsed from a proto file.
    structure: Base class for different parts of the robot structure.
    Node: Represents a node in the robot structure.
    property: Represents a property in the robot structure.
    container: Represents a container in the robot structure.
Functions:
    proto_robot.__init__: Initializes the proto_robot object.
    proto_robot.add_child: Adds a child to the current node.
    proto_robot.set_current: Sets the current node.
    proto_robot.read_proto_file: Reads a proto file and builds the robot structure.
    proto_robot.search: Searches the robot structure with the given name.
    proto_robot.save_robot: Saves the robot structure to a file.
    proto_robot.__str__: Returns the string representation of the robot structure.
    proto_robot.__repr__: Returns the string representation of the robot structure.
    proto_robot.__dict__: Returns the dictionary representation of the robot structure.
    structure.__init__: Initializes the structure object.
    structure.add_child: Adds a child to the structure.
    structure.search: Searches the structure with the given name.
    structure.__str__: Returns the string representation of the structure.
    structure.__repr__: Returns the string representation of the structure.
    Node.__init__: Initializes the Node object.
    Node.get_self_only: Returns the string representation of the node itself.
    Node.__str__: Returns the string representation of the node.
    Node.__dict__: Returns the dictionary representation of the node.
    property.__init__: Initializes the property object.
    property.get_self_only: Returns the string representation of the property itself.
    property.__str__: Returns the string representation of the property.
    property.__dict__: Returns the dictionary representation of the property.
    container.__init__: Initializes the container object.
    container.get_self_only: Returns the string representation of the container itself.
    container.__str__: Returns the string representation of the container.
    container.__dict__: Returns the dictionary representation of the container.
Usage:
    The script can be run as a standalone program to open a proto file, parse it, and save the modified robot structure.
"""
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
import os
import json

class proto_robot:
    def __init__(self, proto_filename = None):
        self.header = ""
        self.children = []
        self.cursor = self
        self.parent = self      # parent of the root is itself
        if proto_filename:
            self.read_proto_file(proto_filename)

    # add child to the current node
    def add_child(self, child):
        self.children.append(child)

    # iterator to set the current node
    def set_current(self, child):
        self.cursor = child    
    
    # read proto file and build the robot structure
    def read_proto_file(self, proto_filename):
        # init variables
        current_stage = -1
        
        # read the proto file
        with open(proto_filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # parse the proto file
        for line in lines:
            line = line.strip()
            if line.startswith("#"):            #header
                self.header += line+"\n"
            else:
                if line.endswith("["):
                    line = line.split(" ",1)
                    current_stage += 1
                    self.cursor.add_child(container(name = line[0], parent=self.cursor, DEF = line[1], stage=current_stage))
                    self.set_current(self.cursor.children[-1])
                elif line.endswith("{"):
                    current_stage += 1
                    if line != "{":
                        line = line.split(" ",1)
                        self.cursor.add_child(Node(name = line[0], parent = self.cursor, DEF = line[1], stage=current_stage))
                        self.set_current(self.cursor.children[-1])
                    else:
                        self.cursor.add_child(Node(name = "", parent = self.cursor, stage=current_stage))
                        self.set_current(self.cursor.children[-1])
                elif line.endswith("]") or line.endswith("}") or line.endswith("} "):
                    if line.startswith("centerOfMass"):
                        line = line.split(" ",1)
                        self.cursor.add_child(property(name = line[0], parent = self.cursor, content = line[1], stage=current_stage+1))
                    else:
                        current_stage -= 1
                        self.set_current(self.cursor.parent)
                else:
                    line = line.split(" ",1)
                    if len(line) == 1:
                        self.cursor.add_child(property(name = line[0], parent = self.cursor, stage=current_stage+1))
                    else:
                        self.cursor.add_child(property(name = line[0], parent = self.cursor, content = line[1], stage=current_stage+1))
        # return lines
    
    # search the robot structure with the given name
    def search(self, name):
        result_list = []
        for child in self.children:
            if child.name == name:
                result_list.append(child)
            result_list += child.search(name)
        return result_list

    def save_robot(self, File_path = None):
        if not File_path:
            # check wether TK() is already created and if File_path is None
            try:
                Tk().withdraw()
            except:
                pass
        
        # get robot name
        Proto_Object = self.search("PROTO")[0]
        robot_Name = Proto_Object.DEF.split(" ")[0]
        
        if not File_path:
            # open a file dialog to save the robot file
            save_file = asksaveasfilename( defaultextension=".proto", filetypes=[("Proto files", "*.proto"), ("All Files", "*.*")])
        else:
            save_file = File_path
        
        save_file_name = os.path.basename(save_file).split(".")[0]
        
        # print(robot_Name)
        # print(save_file_name)
        # print(Proto_Object.DEF)
        
        Proto_Object.DEF = Proto_Object.DEF.replace(robot_Name, save_file_name)
        Proto_Object.children[2].content = Proto_Object.children[2].content.replace(robot_Name, save_file_name)
        with open(save_file, 'w') as f:
            f.write(str(self))

    # str()
    def __str__(self):
        s = self.header
        for child in self.children:
            s += str(child)
        return s

    # repr() -> the thing that is printed when you print the object
    def __repr__(self):
        return self.__str__()
    
    def __dict__(self):
        dct = {"headr": self.header}
        for child in self.children:
            dct[child.name] = child.__dict__()
        return dct

class structure:
    def __init__(self, name, parent, stage = 0, DEF = None):
        self.name = name
        self.stage = stage
        self.parent = parent
        self.children = []
        self.DEF = DEF

    def add_child(self, child):
        self.children.append(child)
    
    def update(self, new_structure):
        self.name = new_structure.name
        self.DEF = new_structure.DEF
        self.stage = new_structure.stage
        self.children = new_structure.children
        self.parent = new_structure.parent
    
    # search the structure with the given name
    def search(self, name):
        result_list = []
        for child in self.children:
            if child.name == name:
                result_list.append(child)
            result_list += child.search(name)
        return result_list

    def copy(self):
        return self.__class__(self.name, self.parent, self.DEF, self.stage)
    
    def __str__(self):
        return f"{self.name} {self.attributes} {self.children}"

    def __repr__(self):
        return self.__str__()

class Node(structure):
    # Node class is used to store the node information
    # for parts starts with '{' and ends with '}'
    def __init__(self, name, parent, DEF = None, stage = 0):
        super().__init__(name, parent, stage, DEF)
    
    # get the self information only
    def get_self_only(self):
        tab = "  " * self.stage
        s = ""
        if self.name == "":
            s = tab + "{\n"
        else:
            s += tab + f"{self.name}"
            if self.DEF:
                s += f" {self.DEF}"+ "\n"
            else:
                s += " {\n"
            for child in self.children:
                if type(child) == property:
                    s += str(child)
        return s+ tab + "}\n"
    
    def __str__(self):
        tab = "  " * self.stage
        s = ""
        if self.name == "":
            s = tab + "{\n"
            for child in self.children:
                s += str(child)
        else:
            s += tab + f"{self.name}"
            if self.DEF:
                s += f" {self.DEF}"+ "\n"
            else:
                s += " {\n"
            for child in self.children:
                s += str(child)
        return s + tab + "}\n"
    
    def __dict__(self):
        dct = {"DEF":self.DEF.replace("{","") if self.DEF else None}
        for child in self.children:
            dct[child.name] = child.__dict__()
        dct["structure_type"] = "node"
        return dct

class property(structure):
    # property class is used to store the property information
    # usually contains only one line
    def __init__(self, name, parent, stage = 0, content = ""):
        super().__init__(name, parent, stage, DEF = None)
        self.content = content

    def get_self_only(self):
        return str(self)

    def update(self, new_property):
        super().update(new_property)
        self.content = new_property.content

    def __str__(self):
        tab = "  " * self.stage
        s = tab + f"{self.name} {self.content}"+"\n"
        return s
    def __dict__(self):
        return {self.name: self.content, "structure_type": "property"}
    
    def copy(self):
        return self.__class__(self.name, self.parent, self.stage, self.content)
    
class container(structure):
    # container class is used to store the container information
    # for parts starts with '[' and ends with ']'
    def __init__(self, name, parent, DEF = None, stage = 0):
        super().__init__(name, parent, stage, DEF)

    def get_self_only(self):
        tab = "  " * self.stage
        s = ""
        s += tab + f"{self.name} [\n"
        for child in self.children:
            if type(child) == property:
                s += str(child)
        return s + tab + "]\n"
    
    def __str__(self):
        tab = "  " * self.stage
        s = ""
        s += tab + f"{self.name} " + self.DEF + "\n"
        for child in self.children:
            s += str(child)
        return s + tab + "]\n"
    
    def __dict__(self):
        dct = {"DEF":self.DEF.replace("[","")}
        for child in self.children:
            dct[child.name] = child.__dict__()
        dct["structure_type"] = "container"
        return dct

if __name__ == "__main__":
    # open a file dialog to select the proto file
    Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
    proto_file = askopenfilename()
    
    # create a robot object
    robot = proto_robot()
    robot.read_proto_file(proto_file)   # read the proto file and build the robot structure
    
# #==============================================================================
#                         # Replace Solid Empty and ADD Reference
# # =============================================================================
#     # search for the endPoint objects
#     l = robot.search("endPoint")
    
#     # search empty solid and remove some properties
#     for i in l:
#         Reference_Template = Node(name = "endPoint", parent = None, DEF = "SolidReference {")
        
#         ## Reference Template:
#         ## ==========================================
#         ## SolidReference {
#         ##   SFString solidName ""   # any string
#         ## }
#         ## ==========================================
        
#         n = i.search("name") #search for name property
#         name = ""
        
#         if len(n) >= 1: #if name property is found
#             name = n[0].content #get the name
        
#         # check if the node is a solid and empty
#         if "Solid" in i.DEF and "Empty" in name:
#             robot.set_current(i)
#             name_object = i.search("name")
#             if len(name_object) >= 1:
#                 name_object = name_object[0].content
#             else:
#                 name_object = None
            
#             if name_object and "Ref" not in name_object:
#                 # print
#                 i.DEF = "SolidReference {"
#                 i.children = []
#                 i.add_child(property(name = "solidName", parent = i, content = name_object[:-1:]+"_Ref\"", stage = i.stage+1))
    
# =============================================================================
#                         # Motor Torque
# =============================================================================
    # search for the RotationalMotor objects
    l = robot.search("RotationalMotor")     # search for RotationalMotor node

    for i in l:
        t = i.search("maxTorque")
        Reference_Template = property(name = "maxTorque", parent = t[0].parent, content = "0.001", stage = t[0].stage)
        if t[0].stage >6:
            temp = i
            robot.set_current(t[0])
            robot.cursor.update(Reference_Template)   # replace the maxTorque property with the Reference_Template
            robot.set_current(temp)
        t = i.search("maxTorque")   
        print("content: ",t[0],"\tstage: ",t[0].stage, "\tparent name: ",t[0].parent.search("name")[0])


# #==============================================================================
# #                         # Save the Robot
# #==============================================================================
#     # save the robot structure to a file
    robot.save_robot()


