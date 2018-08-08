
import clr
import System

clr.AddReference("System.Xml")
from System.Xml import XmlDocument

from System.IO import File, Path, IOException

try:
  clr.AddReference("DynamoRevitDS")
except IOException, e:
  raise Exception("Could not load the Dynamo module! There must be EXACTLY ONE VERSION of Dynamo installed!")
from Dynamo.Applications import DynamoRevit, DynamoRevitCommandData


DYNAMO_RUNTYPE_AUTOMATIC = "Automatic"
DYNAMO_RUNTYPE_MANUAL = "Manual"
DYNAMO_WORKSPACE_NODE = "Workspace"
DYNAMO_RUNTYPE_ATTRIBUTE = "RunType"

def SetDynamoScriptRunType(dynamoScriptFilePath, runType):
  prevRunType = None
  doc = XmlDocument()
  try:
    doc.Load(dynamoScriptFilePath)
    dynamoRunTypeAttribute = doc[DYNAMO_WORKSPACE_NODE].Attributes[DYNAMO_RUNTYPE_ATTRIBUTE]
    prevRunType = dynamoRunTypeAttribute.Value
    dynamoRunTypeAttribute.Value = runType
    doc.Save(dynamoScriptFilePath)
  except Exception, e:
    prevRunType = None
  return prevRunType

def GetDynamoScriptRunType(dynamoScriptFilePath):
  runType = None
  doc = XmlDocument()
  try:
    doc.Load(dynamoScriptFilePath)
    runType = doc[DYNAMO_WORKSPACE_NODE].Attributes[DYNAMO_RUNTYPE_ATTRIBUTE].Value
  except Exception, e:
    runType = None
  return runType

# NOTE: Dynamo requires an active UIDocument! The document must be active before executing this function.
#       The Dynamo script must have been saved with the 'Automatic' run mode!
def ExecuteDynamoScriptInternal(uiapp, dynamoScriptFilePath, showUI=False):
  dynamoScriptRunType = GetDynamoScriptRunType(dynamoScriptFilePath)
  if dynamoScriptRunType is None:
    raise Exception("Could not determine the Run mode of this Dynamo script!")
  elif dynamoScriptRunType != DYNAMO_RUNTYPE_AUTOMATIC:
    raise Exception(
        "The Dynamo script has Run mode set to '" + dynamoScriptRunType + "'. " +
        "It must be set to '" + DYNAMO_RUNTYPE_AUTOMATIC + "' in order for Dynamo script automation to work."
      )
  revitVersionNumber = uiapp.Application.VersionNumber
  if revitVersionNumber == "2015":
    raise Exception("Automation of Dynamo scripts is not supported in Revit 2015!")
  elif revitVersionNumber == "2016":
    JOURNAL_KEY__AUTOMATION_MODE = "dynAutomation"
    JOURNAL_KEY__SHOW_UI = "dynShowUI"
    JOURNAL_KEY__DYN_PATH = "dynPath"
  else:
    from Dynamo.Applications import JournalKeys
    JOURNAL_KEY__AUTOMATION_MODE = JournalKeys.AutomationModeKey
    JOURNAL_KEY__SHOW_UI = JournalKeys.ShowUiKey
    JOURNAL_KEY__DYN_PATH = JournalKeys.DynPathKey

  dynamoRevitCommandData = DynamoRevitCommandData()
  dynamoRevitCommandData.Application = uiapp
  dynamoRevitCommandData.JournalData = {
      JOURNAL_KEY__AUTOMATION_MODE : True.ToString(),
      JOURNAL_KEY__SHOW_UI : showUI.ToString(),
      JOURNAL_KEY__DYN_PATH : dynamoScriptFilePath
    }

  dynamoRevit = DynamoRevit()
  externalCommandResult = dynamoRevit.ExecuteCommand(dynamoRevitCommandData)
  return externalCommandResult

def ExecuteDynamoScript(uiapp, dynamoScriptFilePath, showUI=False):
  externalCommandResult = None
  # NOTE: The temporary copy of the Dynamo script file is created in same folder as the original so
  # that any relative paths in the script won't break.
  tempDynamoScriptFilePath = Path.Combine(Path.GetDirectoryName(dynamoScriptFilePath), Path.GetRandomFileName())
  File.Copy(dynamoScriptFilePath, tempDynamoScriptFilePath)
  try:
    SetDynamoScriptRunType(tempDynamoScriptFilePath, DYNAMO_RUNTYPE_AUTOMATIC)
    externalCommandResult = ExecuteDynamoScriptInternal(uiapp, tempDynamoScriptFilePath, showUI)
  finally:
    File.Delete(tempDynamoScriptFilePath)
  return externalCommandResult