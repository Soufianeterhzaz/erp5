# -*- coding: utf-8 -*-
import sys
from ZODB.POSException import ConflictError
from zExceptions import ExceptionFormatter

from Products.CMFActivity.ActiveResult import ActiveResult
from Products.ERP5Type.Document import newTempOOoDocument
from zLOG import LOG, INFO

def dumpWorkflowChain(self):
  # This method outputs the workflow chain in the format that you can
  # easily get diff like the following:
  # ---
  # Account,account_workflow
  # Account,edit_workflow
  # ...
  # ---
  workflow_tool = self.getPortalObject().portal_workflow
  cbt = workflow_tool._chains_by_type
  ti = workflow_tool._listTypeInfo()
  types_info = []
  for t in ti:
    id = t.getId()
    title = t.Title()
    if title == id:
      title = None
    if cbt is not None and cbt.has_key(id):
      chain = sorted(cbt[id])
    else:
      chain = ['(Default)']
    types_info.append({'id': id,
                       'title': title,
                       'chain': chain})
  output = []
  for i in sorted(types_info, key=lambda x:x['id']):
    for chain in i['chain']:
      output.append('%s,%s' % (i['id'], chain))
  return '\n'.join(output)

def checkFolderHandler(self, fixit=0, **kw):
  error_list = []
  try:
    is_btree = self.isBTree()
    is_hbtree = self.isHBTree()
  except AttributeError:
    return error_list
  message = '%s' % self.absolute_url_path()
  problem = False
  if not is_btree and not is_hbtree:
    problem = True
    message = '%s is NOT BTree NOR HBTree' % message
    if fixit:
      try:
        result = self._fixFolderHandler()
      except AttributeError:
        result = False
      if result:
        message = '%s fixed' % message
      else:
        message = '%s CANNOT FIX' % message
  if is_btree and is_hbtree:
    problem = True
    message = '%s is BTree and HBTree' % message
    if fixit:
      message = '%s CANNOT FIX' % message
  if problem:
    error_list.append(message)
    LOG('checkFolderHandler', INFO, message)
  return error_list


def MessageCatalog_getMessageDict(self):
  """
    Get Localizer's MessageCatalog instance messages.
  """
  d = {}
  for k,v in self._messages.iteritems():
    d[k] = v
  return d

def MessageCatalog_getNotTranslatedMessageDict(self):
  """
    Get Localizer's MessageCatalog instance messages that are NOT translated.
  """
  not_translated_message_dict = {}
  messages = MessageCatalog_getMessageDict(self)
  for k,v in messages.iteritems():
    if not len(v) or not len(filter(lambda x:x, v.values())):
      not_translated_message_dict[k] = v
  return not_translated_message_dict

def MessageCatalog_deleteNotTranslatedMessageDict(self):
  """
    Delete from  Localizer's MessageCatalog instance messages that are NOT translated.
  """
  not_translated_message_dict = MessageCatalog_getNotTranslatedMessageDict(self)
  for k,v in not_translated_message_dict.iteritems():
    # delete message from dict
    del(self._messages[k])
  return len(not_translated_message_dict.keys())


def checkConversionToolAvailability(self):
  """
  Check conversion tool (oood) is available for erp5.
  This script convert an odt document into HTML and try to read
  the returned string and find out expected string
  """
  portal = self.getPortalObject()
  document_id = 'P-ERP5-TEST.Conversion.Tool.Availability-001-en.odt'
  document_path = 'portal_skins/erp5_administration/%s' % (document_id,)
  document_file = portal.restrictedTraverse(document_path)

  message = None
  severity = 0

  try:
    temp_document = newTempOOoDocument(self, document_id, data=document_file.data, source_reference=document_id)
    temp_document.convertToBaseFormat()
    mimetype, html_result = temp_document.convert(format='html')
  except ConflictError:
    raise
  except: #Which Errors should we catch ?
    #Transformation failed
    message = 'Conversion tool got unexpected error:\n%s' % ''.join(ExceptionFormatter.format_exception(*sys.exc_info()))
  else:
    #Everything goes fine, Check that expected string is present in HTML conversion
    if 'AZERTYUIOPMQ' not in html_result:
      message = 'Conversion to HTML Failed:\n%s' % (html_result,)

  active_process = self.newActiveProcess()
  result = ActiveResult()
  if message:
    severity = 1
    result.edit(detail=message)
  result.edit(severity=severity)
  active_process.activateResult(result)

from Products.ERP5Type.Utils import checkPythonSourceCode

def checkPythonSourceCodeAsJSON(self, data):
  """
  Check Python source suitable for Ace Editor and return a JSON object
  """
  import json

  # XXX data is encoded as json, because jQuery serialize lists as []
  if isinstance(data, basestring):
    data = json.loads(data)

  # data contains the code, the bound names and the script params. From this
  # we reconstruct a function that can be checked
  def indent(text):
    return ''.join(("  " + line) for line in text.splitlines(True))

  is_python_script = 'bound_names' in data
  if is_python_script:
    signature_parts = data['bound_names']
    if data['params']:
      signature_parts += [data['params']]
    signature = ", ".join(signature_parts)

    function_name = "function_name"
    body = "def %s(%s):\n%s" % (function_name,
                                signature,
                                indent(data['code']) or "  pass")
  else:
    body = data['code']

  message_list = checkPythonSourceCode(body)
  for message_dict in message_list:
    if is_python_script:
      message_dict['row'] = message_dict['row'] - 2
    else:
      message_dict['row'] = message_dict['row'] - 1

    if message_dict['type'] in ('E', 'F'):
      message_dict['type'] = 'error'
    else:
      message_dict['type'] = 'warning'

  self.REQUEST.RESPONSE.setHeader('content-type', 'application/json')
  return json.dumps(dict(annotations=message_list))