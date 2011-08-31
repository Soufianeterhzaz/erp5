##############################################################################
#
# Copyright (c) 2002-2011 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################

class MagentoTestProduct:
  """
      MagentoTestProduct properties for all ERP5 objects
  """

  _properties = (
      {   'id'          : 'sku',
          'type'        : 'string',
          'mode'        : 'w' },
      {   'id'          : 'product_id',
          'type'        : 'string',
          'mode'        : 'w' },
      {   'id'          : 'type',
          'type'        : 'string',
          'mode'        : 'w' },
      {   'id'          : 'name',
          'type'        : 'string',
          'mode'        : 'w' },
      {   'id'          : 'category',
          'type'        : 'string',
          'mode'        : 'w' },
  )



