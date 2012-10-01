# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009 Nexedi SA and Contributors. All Rights Reserved.
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

import transaction
import zope.interface
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Products.ERP5Type import Permissions, interfaces
from Products.ERP5Type.Base import Base
from Products.ERP5Type.Core.Predicate import Predicate
from Products.ERP5Type.Errors import SimulationError
from Products.ERP5Type.TransactionalVariable import getTransactionalVariable
from Products.ERP5.ExpandPolicy import policy_dict
from Products.ERP5.MovementCollectionDiff import _getPropertyAndCategoryList

from zLOG import LOG

def _compare(tester_list, prevision_movement, decision_movement):
  for tester in tester_list:
    if not tester.compare(prevision_movement, decision_movement):
      return False
  return True

class MovementGeneratorMixin:
  """
  This class provides a generic implementation of IMovementGenerator
  which can be used together the Rule mixin class bellow. It does not
  have any pretention to provide more than that.

  TODO:
    - _getInputMovementList is still not well defined. Should input
      be an amount (_getInputAmountList) or a movement? This 
      requires careful thiking.
  """
  # Default values
  _applied_rule = None
  _rule = None
  _trade_phase_list = None
  _explanation = None

  def __init__(self, applied_rule, explanation=None, rule=None, trade_phase_list=None):
    self._trade_phase_list = trade_phase_list # XXX-JPS Why a list ?
    self._applied_rule = applied_rule
    if rule is None and applied_rule is not None:
      self._rule = applied_rule.getSpecialiseValue()
    else:
      self._rule = rule # for rule specific stuff
    if explanation is None:
      self._explanation = applied_rule
    else:
      # A good example of explicit explanation can be getRootExplanationLineValue
      # since different lines could have different dates
      # such an explicit root explanation only works if
      # indexing of simulation has already happened
      self._explanation = explanation
    # XXX-JPS handle delay_mode

  # Implementation of IMovementGenerator
  def getGeneratedMovementList(self, movement_list=None, rounding=False):
    """
    Returns a list of movements generated by that rule.

    movement_list - optional IMovementList which can be passed explicitely

    rounding - boolean argument, which controls if rounding shall be applied on
               generated movements or not

    NOTE:
      - implement rounding appropriately (True or False seems
        simplistic)
    """
    # Default implementation below can be overriden by subclasses
    # however it should be generic enough not to be overriden
    # by most classes
    # Results will be appended to result
    result = []
    # Build a list of movement and business path
    input_movement_list = self._getInputMovementList(
                            movement_list=movement_list, rounding=rounding)
    for input_movement in input_movement_list:
      # Merge movement and business path properties (core implementation)
      # Lookup Business Process through composition (NOT UNION)
      business_process = input_movement.asComposedDocument()
      explanation = self._applied_rule # We use applied rule as local explanation
      trade_phase = self._getTradePhaseList(input_movement, business_process) # XXX-JPS not convenient to handle
      update_property_dict = self._getUpdatePropertyDict(input_movement)
      result.extend(business_process.getTradePhaseMovementList(explanation, input_movement,
                                                 trade_phase=trade_phase, delay_mode=None,
                                                 update_property_dict=update_property_dict))

    # And return list of generated movements
    return result

  def _getUpdatePropertyDict(self, input_movement):
    # XXX Wouldn't it better to return {} or {'delivery': None} ?
    #     Below code is mainly for root applied rules.
    #     Other movement generators usually want to reset delivery.
    return {'delivery': input_movement.getRelativeUrl()}

  def _getTradePhaseList(self, input_movement, business_process): # XXX-JPS WEIRD
    if self._trade_phase_list:
      return self._trade_phase_list
    if self._rule is not None:
      trade_phase_list = self._rule.getTradePhaseList()
      if trade_phase_list:
        return trade_phase_list
    return input_movement.getTradePhaseList() or \
      business_process.getTradePhaseList()

  def _getInputMovementList(self, movement_list=None, rounding=None): #XXX-JPS should it be amount or movement ?
    raise NotImplementedError
    # Default implementation takes amounts ?
    # Use TradeModelRuleMovementGenerator._getInputMovementList as default implementation
    # and potentially use trade phase for that.... as a way to filter out


class RuleMixin(Predicate):
  """
  Provides generic methods and helper methods to implement
  IRule and IMovementCollectionUpdater.
  """
  # Declarative security
  security = ClassSecurityInfo()
  security.declareObjectProtected(Permissions.AccessContentsInformation)

  # Declarative interfaces
  zope.interface.implements(interfaces.IRule,
                            interfaces.IDivergenceController,
                            interfaces.IMovementCollectionUpdater,)

  # Portal Type of created children
  movement_type = 'Simulation Movement'

  # Implementation of IRule
  def constructNewAppliedRule(self, context, **kw):
    """
    Create a new applied rule in the context.

    An applied rule is an instantiation of a Rule. The applied rule is
    linked to the Rule through the `specialise` relation. The newly
    created rule should thus point to self.

    context -- usually, a parent simulation movement of the
               newly created applied rule

    activate_kw -- activity parameters, required to control
                   activity constraints

    kw -- XXX-JPS probably wrong interface specification
    """
    return context.newContent(portal_type='Applied Rule',
                              specialise_value=self, **kw)

  if 0: # XXX-JPS - if people are stupid enough not to configfure predicates,
        # it is not our role to be clever for them
        # Rules have a workflow - make sure applicable rule system works
        # if you wish, add a test here on workflow state to prevent using
        # rules which are no longer applicable
   def test(self, *args, **kw):
    """
    If no test method is defined, return False, to prevent infinite loop
    """
    if not self.getTestMethodId():
      return False
    return super(RuleMixin, self).test(*args, **kw)

  def expand(self, applied_rule, expand_policy=None, **kw):
    """
    Expand this applied rule to create new documents inside the
    applied rule.

    At expand time, we must replace or compensate certain
    properties. However, if some properties were overwritten
    by a decision (ie. a resource is changed), then we
    should not try to compensate such a decision.
    """
    policy_dict[expand_policy](**kw).expand(self, applied_rule)

  def _expandNow(self, maybe_expand, applied_rule):
    # Update moveme-nts
    #  NOTE-JPS: it is OK to make rounding a standard parameter of rules
    #            although rounding in simulation is not recommended at all
    self.updateMovementCollection(applied_rule,
      movement_generator=self._getMovementGenerator(applied_rule))
    # And forward expand
    for movement in applied_rule.getMovementList():
      maybe_expand(movement)

  security.declareProtected(Permissions.AccessContentsInformation,
                            'isAccountable')
  def isAccountable(self, movement):
    """Tells wether generated movement needs to be accounted or not.

    Only account movements which are not associated to a delivery;
    Whenever delivery is there, delivery has priority
    """
    return not movement.getDelivery()

  # Implementation of IDivergenceController # XXX-JPS move to IDivergenceController only mixin for 
  security.declareProtected( Permissions.AccessContentsInformation,
                            'isDivergent')
  def isDivergent(self, movement, ignore_list=[]):
    """
    Returns true if the Simulation Movement is divergent comparing to
    the delivery value
    """
    if not movement.getDelivery():
      return False
    return bool(self.getDivergenceList(movement))

  security.declareProtected(Permissions.View, 'getDivergenceList')
  def getDivergenceList(self, movement):
    """
    Returns a list of divergences of the movements provided
    in delivery_or_movement.

    movement -- a movement, a delivery, a simulation movement,
                or a list thereof
    """
    result_list = []
    for divergence_tester in self._getDivergenceTesterList(
                                          exclude_quantity=False):
      if divergence_tester.test(movement):
        result = divergence_tester.explain(movement)
        if isinstance(result, (list, tuple)): # for compatibility
          result_list.extend(result)
        elif result is not None:
          result_list.append(result)
    return result_list

  # Placeholder for methods to override
  def _getMovementGenerator(self, applied_rule):
    """
    Return the movement generator to use in the expand process
    """
    raise NotImplementedError

  def _getMovementGeneratorContext(self, applied_rule):
    """
    Return the movement generator context to use for expand
    XXX-JPS likely useless
    """
    raise NotImplementedError

  def _getMovementGeneratorMovementList(self, applied_rule):
    """
    Return the movement lists to provide to the movement generator
    """
    raise NotImplementedError

  def _getDivergenceTesterList(self, exclude_quantity=True):
    """
    Return the applicable divergence testers which must
    be used to test movement divergence. (ie. not all
    divergence testers of the Rule)

     exclude_quantity -- if set to true, do not consider
                         quantity divergence testers
    """
    if exclude_quantity:
      return filter(lambda x:x.isDivergenceProvider() and \
                    'quantity' not in x.getTestedPropertyList(), self.objectValues(
        portal_type=self.getPortalDivergenceTesterTypeList()))
    else:
      return filter(lambda x:x.isDivergenceProvider(), self.objectValues(
        portal_type=self.getPortalDivergenceTesterTypeList()))

  def _getMatchingTesterList(self):
    """
    Return the applicable divergence testers which must
    be used to match movements and build the diff (ie.
    not all divergence testers of the Rule)
    """
    return filter(lambda x:x.isMatchingProvider(), self.objectValues(
      portal_type=self.getPortalDivergenceTesterTypeList()))

  def _getUpdatingTesterList(self, exclude_quantity=False):
    """
    Return the applicable divergence testers which must be used to
    update movements. (ie. not all divergence testers of the Rule)

    exclude_quantity -- if set to true, do not consider
                        quantity divergence testers
    """
    if exclude_quantity:
      return filter(lambda x:x.isUpdatingProvider() and \
                    'quantity' not in x.getTestedPropertyList(), self.objectValues(
        portal_type=self.getPortalDivergenceTesterTypeList()))
    else:
      return filter(lambda x:x.isUpdatingProvider(), self.objectValues(
        portal_type=self.getPortalDivergenceTesterTypeList()))

  def _getQuantityTesterList(self):
    """
    Return the applicable quantity divergence testers.
    """
    tester_list = self.objectValues(
      portal_type=self.getPortalDivergenceTesterTypeList())
    return [x for x in tester_list if 'quantity' in x.getTestedPropertyList()]

  def _newProfitAndLossMovement(self, prevision_movement):
    """
    Returns a new temp simulation movement which can
    be used to represent a profit or loss in relation
    with prevision_movement

    prevision_movement -- a simulation movement
    """
    raise NotImplementedError

  def _isProfitAndLossMovement(movement): # applied_rule XXX-JPS add this ?
    """
    Returns True if movement is a profit and loss movement.
    """
    raise NotImplementedError

  def _extendMovementCollectionDiff(self, movement_collection_diff,
                                    prevision_movement, decision_movement_list):
    """
    Compares a prevision_movement to decision_movement_list which
    are part of the matching group and updates movement_collection_diff
    accordingly

    NOTE: this method API implicitely considers that each group of matching 
    movements has 1 prevision_movement (aggregated) for N decision_movement
    It implies that prevision_movement are "more" aggregated than 
    decision_movement.

    TODO:
       - is this assumption appropriate ?
    """
    # Sample implementation - but it actually looks very generic

    # Case 1: movements which are not needed
    if prevision_movement is None:
      # decision_movement_list contains simulation movements which must
      # be deleted
      for decision_movement in decision_movement_list:
        # If not frozen and all children are deletable
        if decision_movement.isDeletable():
          # Delete deletable
          movement_collection_diff.addDeletableMovement(decision_movement)
        else:
          # Compensate non deletable
          new_movement = decision_movement.asContext(
                            quantity=-decision_movement.getQuantity())
          new_movement.setDelivery(None)
          movement_collection_diff.addNewMovement(new_movement)
      return

    # Case 2: movements which should be added
    elif len(decision_movement_list) == 0:
      # if decision_movement_list is empty, we can just create a new one.
      movement_collection_diff.addNewMovement(prevision_movement)
      return

    # Case 3: movements which are needed but may need update or
    # compensation_movement_list.
    #  let us imagine the case of a forward rule
    #  ie. what comes in must either go out or has been lost
    divergence_tester_list = self._getDivergenceTesterList()
    profit_tester_list = divergence_tester_list
    updating_tester_list = self._getUpdatingTesterList(exclude_quantity=True)
    profit_updating_tester_list = updating_tester_list
    quantity_tester_list = self._getQuantityTesterList()
    compensated_quantity = 0.0
    updatable_movement = None
    not_completed_movement = None
    updatable_compensation_movement = None
    prevision_quantity = prevision_movement.getQuantity()
    decision_quantity = 0.0
    real_quantity = 0.0
    # First, we update all properties (exc. quantity) which could be divergent
    # and if we can not, we compensate them
    for decision_movement in decision_movement_list:
      real_movement_quantity = decision_movement.getQuantity()
      if decision_movement.isPropertyRecorded('quantity'):
        decision_movement_quantity = decision_movement.getRecordedProperty('quantity')
      else:
        decision_movement_quantity = real_movement_quantity
      decision_quantity += decision_movement_quantity
      real_quantity += real_movement_quantity
      if self._isProfitAndLossMovement(decision_movement):
        if decision_movement.isFrozen():
          # Record not completed movements
          if not_completed_movement is None and not decision_movement.isCompleted():
            not_completed_movement = decision_movement
          # Frozen must be compensated
          if not _compare(profit_tester_list, prevision_movement, decision_movement):
            new_movement = decision_movement.asContext(
                                quantity=-decision_movement_quantity)
            new_movement.setDelivery(None)
            movement_collection_diff.addNewMovement(new_movement)
            compensated_quantity += decision_movement_quantity
        else:
          updatable_compensation_movement = decision_movement
          # Not Frozen can be updated
          kw = {}
          for tester in profit_updating_tester_list:
            if not tester.compare(prevision_movement, decision_movement):
              kw.update(tester.getUpdatablePropertyDict(prevision_movement, decision_movement))
          if kw:
            movement_collection_diff.addUpdatableMovement(decision_movement, kw)
      else:
        if decision_movement.isFrozen():
          # Frozen must be compensated
          if not _compare(divergence_tester_list, prevision_movement, decision_movement):
            new_movement = decision_movement.asContext(
                                  quantity=-decision_movement_quantity)
            new_movement.setDelivery(None)
            movement_collection_diff.addNewMovement(new_movement)
            compensated_quantity += decision_movement_quantity
        else:
          updatable_movement = decision_movement
          # Not Frozen can be updated
          kw = {}
          for tester in updating_tester_list:
            if not tester.compare(prevision_movement, decision_movement):
              kw.update(tester.getUpdatablePropertyDict(prevision_movement, decision_movement))
              # XXX-JPS - there is a risk here that quantity is wrongly updated
          if kw:
            movement_collection_diff.addUpdatableMovement(decision_movement, kw)
    # Second, we calculate if the total quantity is the same on both sides
    # after compensation
    quantity_movement = prevision_movement.asContext(
                            quantity=decision_quantity-compensated_quantity)
    if not _compare(quantity_tester_list, prevision_movement, quantity_movement):
      missing_quantity = ( prevision_quantity
                           - real_quantity
                           + compensated_quantity )
      if updatable_movement is not None:
        # If an updatable movement still exists, we update it
        updatable_movement.setQuantity(
            updatable_movement.getQuantity() + missing_quantity)
        updatable_movement.clearRecordedProperty('quantity')
      elif not_completed_movement is not None:
        # It is still possible to add a new movement some movements are not
        # completed
        new_movement = prevision_movement.asContext(quantity=missing_quantity)
        new_movement.setDelivery(None)
        movement_collection_diff.addNewMovement(new_movement)
      elif updatable_compensation_movement is not None:
        # If not, it means that all movements are completed
        # but we can still update a profit and loss movement_collection_diff
        updatable_compensation_movement.setQuantity(
            updatable_compensation_movement.getQuantity() + missing_quantity)
        updatable_compensation_movement.clearRecordedProperty('quantity')
      else:
        # We must create a profit and loss movement
        new_movement = self._newProfitAndLossMovement(prevision_movement)
        movement_collection_diff.addNewMovement(new_movement)


class SimulableMixin(Base):

  def updateSimulation(self, **kw):
    """Create/update related simulation trees by activity

    This method is used to maintain related objects in simulation trees:
    - hiding complexity of activity dependencies
    - avoiding duplicate work

    Repeated calls of this method for the same delivery will result in a single
    call to _updateSimulation. Grouping may happen at the end of the transaction
    or by the grouping method.

    See _updateSimulation for accepted parameters.
    """
    tv = getTransactionalVariable()
    key = 'SimulableMixin.updateSimulation', self.getUid()
    item_list = kw.items()
    try:
      kw, ignore = tv[key]
      kw.update(item_list)
    except KeyError:
      ignore = set()
      tv[key] = kw, ignore
      def before_commit():
        if kw:
          path = self.getPath()
          if aq_base(self.unrestrictedTraverse(path, None)) is aq_base(self):
            self.activate(
              activity='SQLQueue',
              group_method_id='portal_rules/updateSimulation',
              tag='expand:' + path,
              after_tag='built:'+ path, # see SimulatedDeliveryBuilder
              priority=3,
              )._updateSimulation(**kw)
        tv[key] = None # disallow further calls to 'updateSimulation' for self
      transaction.get().addBeforeCommitHook(before_commit)
    for k, v in item_list:
      if not v:
        ignore.add(k)
      elif k not in ignore:
        continue
      del kw[k]

  def _updateSimulation(self, create_root=0, expand_root=0,
                              expand_related=0, index_related=0):
    """
    Depending on set parameters, this method will:
      create_root    -- if a root applied rule is missing, create and expand it
      expand_root    -- expand related root applied rule,
                        create it before if missing
      expand_related -- reindex related simulation movements (recursively)
      index_related  -- expand related simulation movements
    """
    if create_root or expand_root:
      applied_rule = self._getRootAppliedRule()
      if applied_rule is None:
        applied_rule = self._createRootAppliedRule()
        expand_root = applied_rule is not None
    activate_kw = {'tag': 'expand:'+self.getPath()}
    if expand_root:
      applied_rule.expand(activate_kw=activate_kw)
    else:
      applied_rule = None
    if expand_related:
      for movement in self._getAllRelatedSimulationMovementList():
        movement = movement.getObject()
        if not movement.aq_inContextOf(applied_rule):
          # XXX: make sure this will also reindex of all sub-objects recursively
          movement.expand(activate_kw=activate_kw)
    elif index_related:
      for movement in self._getAllRelatedSimulationMovementList():
        movement = movement.getObject()
        if not movement.aq_inContextOf(applied_rule):
          movement.recursiveReindexObject(activate_kw=activate_kw)

  def getRuleReference(self):
    """Returns an appropriate rule reference

    XXX: Using reference to select a rule (for a root applied rule) is wrong
         and should be replaced by predicate and workflow state.
    """
    method = self._getTypeBasedMethod('getRuleReference')
    if method is None:
      raise SimulationError("Missing type-based 'getRuleReference' script for "
                            + repr(self))
    return method()

  def _getRootAppliedRule(self):
    """Get related root applied rule if it exists"""
    applied_rule_list = self.getCausalityRelatedValueList(
        portal_type='Applied Rule')
    if len(applied_rule_list) == 1:
      return applied_rule_list[0]
    elif applied_rule_list:
      raise SimulationError('%r has more than one applied rule.' % self)

  def _createRootAppliedRule(self):
    """Create a root applied rule"""
    # XXX: Consider moving this first test to Delivery
    if self.isSimulated():
      # No need to have a root applied rule
      # if we are already in the simulation process
      return
    rule_reference = self.getRuleReference()
    if rule_reference:
      portal = self.getPortalObject()
      rule_list = portal.portal_catalog.unrestrictedSearchResults(
        portal_type=portal.getPortalRuleTypeList(),
        validation_state="validated", reference=rule_reference,
        sort_on='version', sort_order='descending')
      if rule_list:
        applied_rule = rule_list[0].constructNewAppliedRule(
          portal.portal_simulation, is_indexable=False)
        applied_rule._setCausalityValue(self)
        del applied_rule.isIndexable
        applied_rule.immediateReindexObject()
        self.serialize() # prevent duplicate root Applied Rule
        return applied_rule
      raise SimulationError("No such rule as %r is found" % rule_reference)

  def manage_beforeDelete(self, item, container):
    """Delete related Applied Rule"""
    for o in self.getCausalityRelatedValueList(portal_type='Applied Rule'):
      o.getParentValue().deleteContent(o.getId())
    super(SimulableMixin, self).manage_beforeDelete(item, container)
