##############################################################################
#
# Copyright (c) 2009 Nexedi KK, Nexedi SA and Contributors. All Rights Reserved.
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
import unittest
from transaction import get as get_transaction
from AccessControl.SecurityManagement import newSecurityManager
from Products.ERP5Type.tests.ERP5TypeTestCase import ERP5TypeTestCase
from DateTime import DateTime


class TestOpenOrder(ERP5TypeTestCase):
  """
  Test Open Order
  """

  def getTitle(self):
    return 'Test Open Order'

  def getBusinessTemplateList(self):

    return ('erp5_base',
            'erp5_pdm',
            'erp5_trade',
            )

  def afterSetUp(self):
    if getattr(self.portal, '_run_after_setup', None) is not None:
      return

    self.portal.portal_rules.default_open_order_rule.validate()
    self.portal.portal_rules.default_order_rule.validate()

    self.portal.portal_categories.base_amount.newContent(
      id='taxable',
      portal_type='Category',
      title='Taxable')
    tax = self.portal.tax_module.newContent(
      portal_type='Tax',
      title='VAT',
      base_contribution='base_amount/taxable')
    client = self.portal.organisation_module.newContent(
      id='client',
      portal_type='Organisation',
      title='Client')
    vendor = self.portal.organisation_module.newContent(
      id='vendor',
      portal_type='Organisation',
      title='Vendor')
    internet_connection = self.portal.service_module.newContent(
      id='internet_connection',
      title='Internet Connection',
      base_contribution='base_amount/taxable')
    training = self.portal.service_module.newContent(
      id='training',
      title='Training',
      base_contribution='base_amount/taxable')
    bread = self.portal.product_module.newContent(
      id='bread',
      title='Bread',
      base_contribution='base_amount/taxable')
    water = self.portal.product_module.newContent(
      id='water',
      title='Water',
      base_contribution='base_amount/taxable')
    main_trade_condition = self.portal.sale_trade_condition_module.newContent(
      id='main_trade_condition',
      portal_type='Sale Trade Condition',
      title='Vendor ---> Client',
      source=vendor.getRelativeUrl(),
      source_section=vendor.getRelativeUrl(),
      destination=client.getRelativeUrl(),
      destination_section=client.getRelativeUrl(),
      )
    main_trade_condition.newContent(portal_type='Tax Model Line',
                               title='VAT',
                               base_application='base_amount/taxable',
                               efficiency=0.05)
    main_trade_condition.newContent(portal_type='Sale Supply Line',
                               resource=internet_connection.getRelativeUrl(),
                               priced_quantity=1,
                               base_price=200)
    main_trade_condition.newContent(
      id='internet_connection_periodicity_line',
      portal_type='Periodicity Line',
      resource=internet_connection.getRelativeUrl(),
      periodicity_term_scope_type='until_the_end_of_month',
      periodicity_minute=0,
      periodicity_hour=0,
      periodicity_month_day=1)
    main_trade_condition.newContent(portal_type='Sale Supply Line',
                                    resource=training.getRelativeUrl(),
                                    priced_quantity=4,
                                    base_price=400)
    main_trade_condition.newContent(
      id='training_periodicity_line',
      portal_type='Periodicity Line',
      resource=training.getRelativeUrl(),
      periodicity_term_time_scale='day',
      periodicity_term_length_number=1,
      periodicity_hour=10,
      periodicity_week_day='Monday')
    main_trade_condition.newContent(portal_type='Sale Supply Line',
                               resource=bread.getRelativeUrl(),
                               priced_quantity=1,
                               base_price=10)
    main_trade_condition.newContent(
      id='bread_periodicity_line',
      portal_type='Periodicity Line',
      resource=bread.getRelativeUrl(),
      periodicity_term_time_scale='day',
      periodicity_term_length_number=0,
      periodicity_minute=0,
      periodicity_hour_list=(6, 12),
      periodicity_week_day_list=('Monday',
                                 'Tuesday',
                                 'Wednesday',
                                 'Thursday',
                                 'Friday',
                                 'Saturday'))
    main_trade_condition.newContent(portal_type='Sale Supply Line',
                               resource=water.getRelativeUrl(),
                               priced_quantity=1,
                               base_price=5)
    main_trade_condition.newContent(
      id='water_periodicity_line',
      portal_type='Periodicity Line',
      resource=water.getRelativeUrl(),
      periodicity_term_scope_type='until_the_next_period',
      periodicity_minute=0,
      periodicity_hour_list=10,
      periodicity_week_frequency=2,
      periodicity_week_day = 'Monday')

    # Inherit trade conditions to make sure that it works.
    useless_trade_condition = self.portal.sale_trade_condition_module.newContent(
      portal_type='Sale Trade Condition')

    self.portal.sale_trade_condition_module.newContent(
      id='trade_condition',
      portal_type='Sale Trade Condition',
      specialise_list=(useless_trade_condition.getRelativeUrl(),
                       main_trade_condition.getRelativeUrl())
      )
     
    self.portal._run_after_setup = True
    get_transaction().commit()
    self.tic()

  def testPeriodicityDateList(self):
    """
    Make sure that periodicity line can generate correct schedule.
    """
    self.assertEqual(self.portal.sale_trade_condition_module.main_trade_condition.internet_connection_periodicity_line.getDatePeriodList(
      DateTime(2008,1,15), DateTime(2008,12,1)),
                     [(DateTime(2008,2,1), DateTime(2008,2,29)),
                      (DateTime(2008,3,1), DateTime(2008,3,31)),
                      (DateTime(2008,4,1), DateTime(2008,4,30)),
                      (DateTime(2008,5,1), DateTime(2008,5,31)),
                      (DateTime(2008,6,1), DateTime(2008,6,30)),
                      (DateTime(2008,7,1), DateTime(2008,7,31)),
                      (DateTime(2008,8,1), DateTime(2008,8,31)),
                      (DateTime(2008,9,1), DateTime(2008,9,30)),
                      (DateTime(2008,10,1), DateTime(2008,10,31)),
                      (DateTime(2008,11,1), DateTime(2008,11,30)),
                      (DateTime(2008,12,1), DateTime(2008,12,31)),
                      ])
    
    self.assertEqual(self.portal.sale_trade_condition_module.main_trade_condition.bread_periodicity_line.getDatePeriodList(
      DateTime(2008,2,26), DateTime(2008,3,5)),
                     [(DateTime(2008,2,26,6,0), DateTime(2008,2,26,6,0)),
                      (DateTime(2008,2,26,12,0), DateTime(2008,2,26,12,0)),
                      (DateTime(2008,2,27,6,0), DateTime(2008,2,27,6,0)),
                      (DateTime(2008,2,27,12,0), DateTime(2008,2,27,12,0)),
                      (DateTime(2008,2,28,6,0), DateTime(2008,2,28,6,0)),
                      (DateTime(2008,2,28,12,0), DateTime(2008,2,28,12,0)),
                      (DateTime(2008,2,29,6,0), DateTime(2008,2,29,6,0)),
                      (DateTime(2008,2,29,12,0), DateTime(2008,2,29,12,0)),
                      (DateTime(2008,3,1,6,0), DateTime(2008,3,1,6,0)),
                      (DateTime(2008,3,1,12,0), DateTime(2008,3,1,12,0)),
                      (DateTime(2008,3,3,6,0), DateTime(2008,3,3,6,0)),
                      (DateTime(2008,3,3,12,0), DateTime(2008,3,3,12,0)),
                      (DateTime(2008,3,4,6,0), DateTime(2008,3,4,6,0)),
                      (DateTime(2008,3,4,12,0), DateTime(2008,3,4,12,0)),
                      ])

    self.assertEqual(self.portal.sale_trade_condition_module.main_trade_condition.water_periodicity_line.getDatePeriodList(
      DateTime(2008,2,16), DateTime(2008,4,15)),
                     [(DateTime(2008,2,18,10,0), DateTime(2008,3,3,10,0)),
                      (DateTime(2008,3,3,10,0), DateTime(2008,3,17,10,0)),
                      (DateTime(2008,3,17,10,0), DateTime(2008,3,31,10,0)),
                      (DateTime(2008,3,31,10,0), DateTime(2008,4,14,10,0)),
                      (DateTime(2008,4,14,10,0), DateTime(2008,4,28,10,0)),
                      ])
    self.assertEqual(self.portal.sale_trade_condition_module.main_trade_condition.training_periodicity_line.getDatePeriodList(
      DateTime(2008,2,16), DateTime(2008,3,6)),
                     [(DateTime(2008,2,18,10,0), DateTime(2008,2,19,10,0)),
                      (DateTime(2008,2,25,10,0), DateTime(2008,2,26,10,0)),
                      (DateTime(2008,3,3,10,0), DateTime(2008,3,4,10,0)),
                      ])

  def testOpenOrderRule(self):
    """
    Make sure that Open Order Rule can generate simulation movements by
    following trade conditon's periodicity setting and order's forecasting term.
    """
    open_sale_order = self.portal.sale_order_module.newContent(
      portal_type='Open Sale Order',
      specialise=self.portal.sale_trade_condition_module.trade_condition.getRelativeUrl(),
      start_date=DateTime(3000,2,9),
      stop_date=DateTime(3000,8,1),
      )

    open_sale_order_line = open_sale_order.newContent(
      portal_type='Open Sale Order Line',
      resource=self.portal.service_module.training.getRelativeUrl(),
      quantity=1)

    open_sale_order.Order_applyTradeCondition(open_sale_order.getSpecialiseValue())

    get_transaction().commit()
    self.tic()

    self.assertEqual(open_sale_order_line.getPrice(), 100)
    self.assertEqual(open_sale_order.getTotalPrice(), 100)
    self.assertEqual(open_sale_order.getTotalNetPrice(), 105)

    open_sale_order.setForecastingTermDayCount(5)
    open_sale_order.order()
    open_sale_order.start()

    get_transaction().commit()
    self.tic()

    applied_rule = open_sale_order.getCausalityRelatedValue(portal_type='Applied Rule')
    self.assertEqual(len(applied_rule.objectIds()), 0)

    self.portal.portal_rules.default_open_order_rule.expand(
      applied_rule,
      calculation_base_date=DateTime(3000,2,9))

    get_transaction().commit()
    self.tic()

    self.assertEqual(len(applied_rule.objectIds()), 1)
    self.assertEqual(applied_rule['1'].getStartDate(), DateTime(3000,2,10,10,0))
    self.assertEqual(applied_rule['1'].getStopDate(), DateTime(3000,2,11,10,0))

    open_sale_order.setForecastingTermDayCount(10)
    self.portal.portal_rules.default_open_order_rule.expand(
      applied_rule,
      calculation_base_date=DateTime(3000,2,9))

    get_transaction().commit()
    self.tic()

    self.assertEqual(len(applied_rule.objectIds()), 2)
    self.assertEqual(applied_rule['2'].getStartDate(), DateTime(3000,2,17,10,0))
    self.assertEqual(applied_rule['2'].getStopDate(), DateTime(3000,2,18,10,0))

    self.portal.portal_rules.default_open_order_rule.expand(
      applied_rule,
      calculation_base_date=DateTime(3000,3,1))

    get_transaction().commit()
    self.tic()

    self.assertEqual(len(applied_rule.objectIds()), 5)
    self.assertEqual([(movement.getStartDate(), movement.getStopDate())
                      for movement in applied_rule.objectValues(sort_on='start_date')],
                     [(DateTime(3000,2,10,10,0), DateTime(3000,2,11,10,0)),
                      (DateTime(3000,2,17,10,0), DateTime(3000,2,18,10,0)),
                      (DateTime(3000,2,24,10,0), DateTime(3000,2,25,10,0)),
                      (DateTime(3000,3,3,10,0), DateTime(3000,3,4,10,0)),
                      (DateTime(3000,3,10,10,0), DateTime(3000,3,11,10,0))
                      ])

    self.portal.portal_rules.default_open_order_rule.expand(
      applied_rule,
      calculation_base_date=DateTime(3000,3,1))

    get_transaction().commit()
    self.tic()

    self.assertEqual(len(applied_rule.objectIds()), 5)

    self.portal.sale_trade_condition_module.main_trade_condition.setExpirationDate(DateTime(3000,3,22))
    self.portal.portal_rules.default_open_order_rule.expand(
      applied_rule,
      calculation_base_date=DateTime(3000,3,30))

    get_transaction().commit()
    self.tic()

    self.assertEqual(len(applied_rule.objectIds()), 6)
    self.assertEqual([(movement.getStartDate(), movement.getStopDate())
                      for movement in applied_rule.objectValues(sort_on='start_date')],
                     [(DateTime(3000,2,10,10,0), DateTime(3000,2,11,10,0)),
                      (DateTime(3000,2,17,10,0), DateTime(3000,2,18,10,0)),
                      (DateTime(3000,2,24,10,0), DateTime(3000,2,25,10,0)),
                      (DateTime(3000,3,3,10,0), DateTime(3000,3,4,10,0)),
                      (DateTime(3000,3,10,10,0), DateTime(3000,3,11,10,0)),
                      (DateTime(3000,3,17,10,0), DateTime(3000,3,18,10,0)),
                      ])

  def testBuildingSaleOrder(self):
    """
    Make sure that open sale order can create sale orders repeatedly
    """
    open_sale_order = self.portal.sale_order_module.newContent(
      portal_type='Open Sale Order',
      specialise=self.portal.sale_trade_condition_module.trade_condition.getRelativeUrl(),
      start_date=DateTime(3000,2,9),
      stop_date=DateTime(3000,8,1),
      forecasting_term_day_count=5
      )

    # Remove other test's side effect.
    self.portal.sale_trade_condition_module.main_trade_condition.setExpirationDate(None)

    get_transaction().commit()
    self.tic()

    open_sale_order.newContent(
      title='Piano Lesson',
      portal_type='Open Sale Order Line',
      resource=self.portal.service_module.training.getRelativeUrl(),
      quantity=1)

    open_sale_order.newContent(
      title='Internet Connection',
      portal_type='Open Sale Order Line',
      resource=self.portal.service_module.internet_connection.getRelativeUrl(),
      quantity=1)

    open_sale_order.newContent(
      title='Bread Delivery Serivce',
      portal_type='Open Sale Order Line',
      resource=self.portal.product_module.bread.getRelativeUrl(),
      quantity=1)

    open_sale_order.newContent(
      title='Mineral Water Delivery Service',
      portal_type='Open Sale Order Line',
      resource=self.portal.product_module.water.getRelativeUrl(),
      quantity=1)

    open_sale_order.Order_applyTradeCondition(open_sale_order.getSpecialiseValue())

    get_transaction().commit()
    self.tic()

    open_sale_order.order()
    open_sale_order.start()

    get_transaction().commit()
    self.tic()

    applied_rule = open_sale_order.getCausalityRelatedValue(portal_type='Applied Rule')
    self.assertEqual(len(applied_rule.objectIds()), 0)

    open_sale_order.autoOrderPeriodically(comment='Test', calculation_base_date=DateTime(3000,2,9))

    get_transaction().commit()
    self.tic()

    self.assertEqual(len(applied_rule.objectIds()), 9)
    self.assertEqual(len(open_sale_order.getCausalityRelatedValueList(portal_type='Sale Order')), 9)

    # Do the same thing and nothing happens.
    open_sale_order.autoOrderPeriodically(comment='Test', calculation_base_date=DateTime(3000,2,9))

    get_transaction().commit()
    self.tic()

    self.assertEqual(len(applied_rule.objectIds()), 9)
    self.assertEqual(len(open_sale_order.getCausalityRelatedValueList(portal_type='Sale Order')), 9)

    # Next
    open_sale_order.autoOrderPeriodically(comment='Test', calculation_base_date=DateTime(3000,2,14))

    get_transaction().commit()
    self.tic()

    self.assertEqual(len(applied_rule.objectIds()), 19)
    self.assertEqual(len(open_sale_order.getCausalityRelatedValueList(portal_type='Sale Order')), 19)

    # Check sale orders
    sale_order_list = [
      brain.getObject()
      for brain in self.portal.portal_catalog(portal_type='Sale Order',
                                              causality_uid=open_sale_order.getUid(),
                                              sort_on='delivery.start_date')]

    # The first order is bread.
    self.assertEqual(
      len(sale_order_list[0].objectValues(portal_type='Sale Order Line')),
      1)
    self.assertEqual(
      sale_order_list[0].objectValues(portal_type='Sale Order Line')[0].getTitle(),
      'Bread Delivery Serivce')
    self.assertEqual(sale_order_list[0].getTotalPrice(), 10)
    self.assertEqual(sale_order_list[0].getTotalNetPrice(), 10.5)

    # The second order is piano lesson.
    self.assertEqual(
      len(sale_order_list[1].objectValues(portal_type='Sale Order Line')),
      1)
    self.assertEqual(
      sale_order_list[1].objectValues(portal_type='Sale Order Line')[0].getTitle(),
      'Piano Lesson')
    self.assertEqual(sale_order_list[1].getTotalPrice(), 100)
    self.assertEqual(sale_order_list[1].getTotalNetPrice(), 105)


def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestOpenOrder))
  return suite
