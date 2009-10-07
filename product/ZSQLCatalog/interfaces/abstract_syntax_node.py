##############################################################################
#
# Copyright (c) 2002-2009 Nexedi SA and Contributors. All Rights Reserved.
#                    Jean-Paul Smets-Solanes <jp@nexedi.com>
#                    Vincent Pelletier <vincent@nexedi.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from zope.interface import Interface

class INode(Interface):
  """
    Any kind of node in an Abstract Syntax Tree.
  """

  def isLeaf():
    """
      Returns True if current node is a leaf in node tree.
      Returns False otherwise.
    """

  def isColumn():
    """
      Returns True if current node is a column in node tree.
      Returns False otherwise.
    """

class IValueNode(INode):
  """
    Value- and comparison-operator-containig node.
    They are leaf nodes in the syntax tree.
  """

  def getValue():
    """
      Returns node's value.
    """

  def getComparisonOperator():
    """
      Returns node's comparison operator.
    """

class ILogicalNode(INode):
  """
    Logical-operator-containing node.
    They are internal tree nodes.
  """

  def getLogicalOperator():
    """
      Returns node's logical operator.
    """

  def getNodeList():
    """
      Returns the list of subnodes.
    """

class IColumnNode(INode):
  """
    Column-name-containing node.
    They are internal tree nodes.
    Their value applies to any contained ValueNode, except if there is another
    ColumnNode between current one and a ValueNode, for which the other
    ColumnNode will take precedence.
  """

  def getColumnName():
    """
      Returns node's column name.
    """

  def getSubNode():
    """
      Returns node's (only) subnode.
    """

