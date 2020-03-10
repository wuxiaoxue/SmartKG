import json
from xlrd import open_workbook
import os.path
from os import path


def generateOutputPaths(outputDir, suffix):
    checkDir(outputDir)
    checkDir(outputDir + "\\KG\\")
    checkDir(outputDir + "\\NLU\\")

    vJsonPath = outputDir + "\\KG\\" + "Vertexes_" + suffix + ".json"
    eJsonPath = outputDir + "\\KG\\" + "Edges_" + suffix + ".json"

    intentPath = outputDir + "\\NLU\\intentrules.tsv"
    entityMapPath = outputDir + "\\NLU\\entitymap.tsv"

    return vJsonPath, eJsonPath, intentPath, entityMapPath

def checkDir(dir):
    if not path.exists(dir):
        os.mkdir(dir)
        print(dir + " is created to contain KG and NLU files.")
    else:
        if os.path.isdir(dir):
            print(dir + " exists, and KG and NLU files will be created in it.")
        else:
            os.mkdir(dir)
            print(dir + " is created to contain KG and NLU files.")
    return


def convertFile(excelPath, default_rules, scenarios, vJsonPath, eJsonPath, intentPath, entityMapPath, cleanNLU):
    wb = open_workbook(excelPath)
    sheet_vertexes = wb.sheets()[0]
    sheet_edges = wb.sheets()[1]

    edges = []

    nodeNameSet = set()
    propertyNameSet = set()
    relationTypeSet = set()

    headVidSet = set()
    tailVidSet = set()

    for row in range(1, sheet_edges.nrows):
        data = {}
        data["scenarios"] = scenarios
        data["relationType"] = sheet_edges.cell_value(row, 0)
        relationTypeSet.add(data["relationType"])

        rawSrcVId = sheet_edges.cell_value(row, 1)
        data["headVertexId"] = rawSrcVId
        headVidSet.add(data["headVertexId"])

        rawDstVID = sheet_edges.cell_value(row, 2)
        data["tailVertexId"] = rawDstVID
        tailVidSet.add(data["tailVertexId"])

        edges.append(data)

    vertexes = []

    for col in range(1, sheet_vertexes.ncols):

        if sheet_vertexes.cell_value(1, col) is not "":
            data = {}

            data["id"] = sheet_vertexes.cell_value(0, col)
            data["name"] = sheet_vertexes.cell_value(1, col)
            nodeNameSet.add(data["name"])
            data["label"] = sheet_vertexes.cell_value(2, col)
            data["scenarios"] = scenarios
            data["leadSentence"] = sheet_vertexes.cell_value(3, col)

            vid = data["id"]

            if vid in headVidSet and vid in tailVidSet:
                data["nodeType"] = "MIDDLE"
            elif vid in headVidSet:
                data["nodeType"] = "ROOT"
            elif vid in tailVidSet:
                data["nodeType"] = "LEAF"
            else:
                data["nodeType"] = "SINGLE"

            properties = []

            for row in range(4, sheet_vertexes.nrows - 1, 2):
                property = {}
                if sheet_vertexes.cell_value(row, col) is not "":
                    property["name"] = sheet_vertexes.cell_value(row, col)
                    propertyNameSet.add(property["name"])
                    property["value"] = sheet_vertexes.cell_value(row + 1, col)
                    properties.append(property)

            data["properties"] = properties

            vertexes.append(data)

    print("Generating vertex file:", vJsonPath)
    vfp = open(vJsonPath, 'w', encoding="utf-8")
    json.dump(vertexes, vfp, ensure_ascii=False, sort_keys=True, indent=2, separators=(',', ': '))

    print("Generating edge file:", eJsonPath)
    efp = open(eJsonPath, 'w', encoding="utf-8")
    json.dump(edges, efp, ensure_ascii=False, sort_keys=True, indent=2, separators=(',', ': '))

    entity_lines = ""
    for nodeName in nodeNameSet:
        for scenario in scenarios:
            entity_lines += scenario + "\t" + nodeName + "\t" + nodeName + "\t" + "NodeName" + "\n"

    for pn in propertyNameSet:
        for scenario in scenarios:
            entity_lines += scenario + "\t" + pn + "\t" + pn + "\t" + "PropertyName" + "\n"

    for rt in relationTypeSet:
        for scenario in scenarios:
            entity_lines += scenario + "\t" + rt + "\t" + rt + "\t" + "RelationType" + "\n"

    entity_lines = entity_lines[:-1]

    type = 'a'
    if cleanNLU:
        type = 'w'
    else:
        entity_lines = "\n" + entity_lines

    print("Generating entities in", entityMapPath)
    with open(entityMapPath, type, encoding="utf-8") as ef:
        ef.write(entity_lines)

    print("Generating intent rules in", intentPath)
    nodeNameRule = ""
    for nodeName in nodeNameSet:
        nodeNameRule += nodeName + "|"
    nodeNameRule = nodeNameRule[:-1]

    rule_lines = ""
    if cleanNLU:
        for rule in default_rules:
            rule_lines += rule + "\n"
        for scenario in scenarios:
            rule_lines += scenario + "\tPOSITIVE\t" + nodeNameRule
    else:
        for scenario in scenarios:
            rule_lines += "\n" + scenario + "\tPOSITIVE\t" + nodeNameRule

    with open(intentPath, type, encoding="utf-8") as rf:
        rf.write(rule_lines)
    return
