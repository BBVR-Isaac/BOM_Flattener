# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 09:34:55 2022

@author: Isaac
"""

import pandas as pd
import os 
import numpy as np

class BOM_Line:
    
    def __init__(self, partNum, qty, desc):
        self.partNum = partNum.split(".")[0]
        self.description = desc
        self.qty = qty

class Assembly(BOM_Line):
    
    def __init__(self, partNum, qty, desc, parts):
        super().__init__(partNum, qty, desc)
        self.BOM = self.createBOM(parts)
         
    def createBOM(self, parts):
        items = self.createObjects(parts)
        parts["Object"] = items
        return parts
    
    def createObjects(self, parts):
        items = []
        try:
            if not parts.empty:
                for i in parts.iterrows():
                    if i[1].PartType.lower() == "assembly":
                        items.append(Subassembly(i[1].PartNumber, i[1].Qty, i[1].Description, pd.DataFrame(), self.partNum))
                    else:
                        items.append(Part(i[1].PartNumber, i[1].Qty, i[1].Description, self.partNum))
                return items
            else:
                return None
        except AttributeError:
            raise AttributeError("Incorrect Column Formatting on {}".format(i[1].PartNumber))
                 
    def flattenBOM(self):
        output = self.getAllParts()[["PartNumber", "Description", "Qty", "PartType", "Object", "Parent"]]
        output.reset_index(drop = True, inplace = True)
        
        unique = output.PartNumber.unique()
        temp = []
        for i in unique:
            item = output[output.PartNumber == i]
            total = item["Qty"].sum()
            temp.append({"Total":total, "PartNumber": item.Object.iloc[0].partNum, "Description": item.Description.values[0], "Parents": list(set(item.Parent.values))})
        output = pd.DataFrame.from_records(temp)
        output["PartNumber"] = output["PartNumber"].apply(lambda x: x.replace("\n", "")) 
        return output.set_index("PartNumber")
    
    def AllAssemblies(self):
        assys = self.getAllAssemblies()
        assys["PartNumber"] = assys["Object"].apply(lambda x: x.partNum)
        # return assys.drop_duplicates(keep = "first", subset = "PartNumber")
        return assys
        
    def getAllParts(self):
        assys = self.BOM[self.BOM.PartType == "Assembly"]
        parts = self.BOM[self.BOM.PartType == "Part"].copy()
        parts["Parent"] = self.partNum
        if not assys.empty:
            for i in assys.iterrows():
                if not i[1].Object.BOM.empty:
                    child = i[1].Object.getAllParts().copy()
                    child["Qty"] = child["Qty"] * self.qty
                    parts = pd.concat([parts, child])
        return parts
    
    def getAllAssemblies(self):
        assys = self.BOM[self.BOM.PartType == "Assembly"].copy()
        # parts = self.BOM[self.BOM.PartType == "Part"].copy()
        assys["Parent"] = self.partNum
        if not assys.empty:
            for i in assys.iterrows():
                if not i[1].Object.BOM.empty:
                    child = i[1].Object.getAllAssemblies().copy()
                    child["Qty"] = child["Qty"] * self.qty
                    assys = pd.concat([assys, child])
        return assys
        
class Subassembly(Assembly):
    
    def __str__(self):
        return "{} - {}".format(self.partNum, self.description)
        
    def __init__(self, partNum, qty, desc, parts, parent):
        super().__init__(partNum, qty, desc, parts)
        # print(self.partNum)
        self.FindSubassembly()
        self.parentAssembly = parent

    def FindSubassembly(self):
        if self.partNum + ".xlsx" in os.listdir(os.getcwd() + "/Assemblies"):
            file = os.getcwd() + "/Assemblies/{}.xlsx".format(self.partNum)
            items = pd.read_excel(file)
            self.BOM = self.createBOM(items)
            
class Part(BOM_Line):
    
    def __str__(self):
        return "{} - {}".format(self.partNum, self.description)
        
    def __init__(self, partNum, qty, desc, parent):
        super().__init__(partNum, qty, desc)
        self.parentAssembly = parent
        
assy = "01-EL-001"
xcel = pd.read_excel(os.getcwd() + "/{}.xlsx".format(assy))

assembly = Assembly(assy, 1, "Top Level", xcel)

assys = assembly.AllAssemblies()

for i in assys.Object:
    if i.BOM.empty:
        print(i.partNum)

parts = assembly.flattenBOM()
# parts.fillna("Nothing", inplace = True)
# print(parts[parts.Description == "Nothing"])
