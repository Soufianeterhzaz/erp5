##############################################################################
#
# Copyright (c) 2002 Nexedi SARL and Contributors. All Rights Reserved.
#                    Jean-Paul Smets-Solanes <jp@nexedi.com>
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

class VariationRange:
    """
        VariationRange which allows to define possible
        variations for a Resource, a Transformation, etc.
    """

    _properties = (
        # Definition of the variation domain
        {   'id'          : 'variation_base_category',
            'storage_id'  : 'variation_base_category_list', # Coramy Compatibility
            'description' : 'A list of base categories which define possible discrete variations. '\
                            'Variation ranges are stored as category membership. '\
                            '(prev. variation_category_list).',
            'type'        : 'lines',
            'default'     : [],
            'mode'        : 'w' },
        {   'id'          : 'variation_base_category_line',
            'description' : 'The variation base category which serves as line in the matrix representation.',
            'type'        : 'string',
            'mode'        : 'w' },
        {   'id'          : 'variation_base_category_column',
            'description' : 'The variation base category which serves as column in the matrix representation.',
            'type'        : 'string',
            'mode'        : 'w' },
        {   'id'          : 'variation_base_category_tab',
            'description' : 'The variation base category which serves as tab in the matrix representation.',
            'type'        : 'lines',
            'default'     : [],
            'mode'        : 'w' },
        {   'id'          : 'variation_property',
            'storage_id'  : 'variation_property_list', # Coramy Compatibility
            'description' : 'A list of properties which define variations',
            'type'        : 'lines',
            'default'     : [],
            'mode'        : 'w' },

    )

    _categories = ('variation',)
