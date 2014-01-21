##############################################################################
#
# Copyright (c) 2002-2006 Nexedi SARL and Contributors. All Rights Reserved.
# Copyright (c) 2007-2009 Nexedi SA and Contributors. All Rights Reserved.
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

from SearchKey import SearchKey
from Products.ZSQLCatalog.Query.SimpleQuery import SimpleQuery
from Products.ZSQLCatalog.SearchText import parse
from Products.ZSQLCatalog.interfaces.search_key import ISearchKey
from zope.interface.verify import verifyClass
from Products.ZSQLCatalog.SQLCatalog import profiler_decorator

class FullTextKey(SearchKey):
  """
    This SearchKey generates SQL fulltext comparisons.
  """
  default_comparison_operator = 'boolean_match'
  get_operator_from_value = False

  def parseSearchText(self, value, is_column):
    return parse(value, is_column)

  def dequoteParsedText(self):
    return False

  def _renderValueAsSearchText(self, value, operator):
    return '(%s)' % (value, )

  @profiler_decorator
  def _buildQuery(self, operator_value_dict, logical_operator, parsed, group):
    """
      Special Query builder for FullText queries: merge all values having the
      same operator into just one query, to save SQL server from the burden to
      do multiple fulltext lookups when one would suit the purpose.
    """
    column = self.getColumn()
    query_list = []
    append = query_list.append
    for comparison_operator, value_list in operator_value_dict.iteritems():
      append(SimpleQuery(search_key=self,
                         comparison_operator=comparison_operator,
                         group=group, **{column: ' '.join(value_list)}))
    return query_list

verifyClass(ISearchKey, FullTextKey)

