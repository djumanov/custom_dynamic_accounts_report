from odoo import api, fields, models
from odoo.tools.date_utils import get_month


class AccountTrialBalance(models.TransientModel):
    """For creating Trial Balance report"""
    _inherit = 'account.trial.balance'
    _description = 'Trial Balance Report'

    @api.model
    def view_custom_report(self):
        """
        Generates a trial balance report for multiple accounts.
        Retrieves account information and calculates total debit and credit
        amounts for each account within the specified date range. Returns a list
        of dictionaries containing account details and transaction totals.

        :return: List of dictionaries representing the trial balance report.
        :rtype: list
        """
        account_types_map = {
            'asset_receivable': 'Receivable',
            'asset_cash': 'Bank and Cash',
            'asset_current': 'Current Asset',
            'asset_non_current': 'Non-Current Asset',
            'asset_prepayments': 'Prepayments',
            'asset_fixed': 'Fixed Asset',
            'liability_payable': 'Payable',
            'liability_credit_card': 'Credit Card',
            'liability_current': 'Current Liability',
            'liability_non_current': 'Non-Current Liability',
            'equity': 'Equity',
            'equity_unaffected': 'Current Year Earnings',
            'income': 'Income',
            'income_other': 'Other Income',
            'expense': 'Expenses',
            'expense_depreciation': 'Depreciation',
            'expense_direct_cost': 'Cost of Revenue',
            'off_balance': 'Off-Balance Sheet',
        }
        
        # Define account types with normal debit balance
        debit_account_types = {
            'asset_receivable', 'asset_cash', 'asset_current', 'asset_non_current',
            'asset_prepayments', 'asset_fixed', 'expense', 'expense_depreciation',
            'expense_direct_cost'
        }
        
        account_ids = self.env['account.account'].search([
            # ('deprecated', '=', False)
        ])
        
        today = fields.Date.today()
        period_start, period_end = get_month(today)
        
        move_line_list = []
        account_type_totals = {}  # Track totals by account type
        
        for account_id in account_ids:
            # Get initial balances (before period)
            initial_move_line_ids = self.env['account.move.line'].search([
                ('date', '<', period_start),
                ('account_id', '=', account_id.id),
                ('parent_state', '=', 'posted')
            ])
            initial_total_debit = sum(initial_move_line_ids.mapped('debit'))
            initial_total_credit = sum(initial_move_line_ids.mapped('credit'))
            
            # Get period movements
            move_line_ids = self.env['account.move.line'].search([
                ('date', '>=', period_start),
                ('date', '<=', period_end),
                ('account_id', '=', account_id.id),
                ('parent_state', '=', 'posted')
            ])
            period_debit = sum(move_line_ids.mapped('debit'))
            period_credit = sum(move_line_ids.mapped('credit'))
            
            # Calculate ending balance
            total_debit = initial_total_debit + period_debit
            total_credit = initial_total_credit + period_credit
            balance = total_debit - total_credit
            
            # Determine ending debit/credit based on account type and balance
            account_type = account_id.account_type
            if account_type in debit_account_types:
                # Normal debit balance accounts
                if balance >= 0:
                    end_total_debit = balance
                    end_total_credit = 0.0
                else:
                    end_total_debit = 0.0
                    end_total_credit = abs(balance)
            else:
                # Normal credit balance accounts (liability, equity, income)
                if balance <= 0:
                    end_total_debit = 0.0
                    end_total_credit = abs(balance)
                else:
                    end_total_debit = balance
                    end_total_credit = 0.0
            
            # Skip accounts with no activity and zero balance
            if (initial_total_debit == 0 and initial_total_credit == 0 and 
                period_debit == 0 and period_credit == 0):
                continue
                
            data = {
                'account': account_id.display_name,
                'account_id': account_id.id,
                'account_code': account_id.code,
                'initial_total_debit': "{:,.2f}".format(initial_total_debit),
                'initial_total_credit': "{:,.2f}".format(initial_total_credit),
                'period_debit': "{:,.2f}".format(period_debit),
                'period_credit': "{:,.2f}".format(period_credit),
                'end_total_debit': "{:,.2f}".format(end_total_debit),
                'end_total_credit': "{:,.2f}".format(end_total_credit),
                # Store raw values for aggregation
                'raw_initial_debit': initial_total_debit,
                'raw_initial_credit': initial_total_credit,
                'raw_period_debit': period_debit,
                'raw_period_credit': period_credit,
                'raw_end_debit': end_total_debit,
                'raw_end_credit': end_total_credit,
            }
            
            # Group by account type
            if account_type not in account_type_totals:
                account_type_totals[account_type] = {
                    'account_type': account_type,
                    'account_type_name': account_types_map.get(account_type, account_type),
                    'accounts': [],
                    'initial_total_debit': 0.0,
                    'initial_total_credit': 0.0,
                    'period_total_debit': 0.0,
                    'period_total_credit': 0.0,
                    'end_total_debit': 0.0,
                    'end_total_credit': 0.0
                }
            
            # Add account to the group
            account_type_totals[account_type]['accounts'].append(data)
            
            # Aggregate totals using raw values
            account_type_totals[account_type]['initial_total_debit'] += initial_total_debit
            account_type_totals[account_type]['initial_total_credit'] += initial_total_credit
            account_type_totals[account_type]['period_total_debit'] += period_debit
            account_type_totals[account_type]['period_total_credit'] += period_credit
            account_type_totals[account_type]['end_total_debit'] += end_total_debit
            account_type_totals[account_type]['end_total_credit'] += end_total_credit
        
        # Format the aggregated totals
        for account_type_data in account_type_totals.values():
            account_type_data['initial_total_debit'] = "{:,.2f}".format(
                account_type_data['initial_total_debit'])
            account_type_data['initial_total_credit'] = "{:,.2f}".format(
                account_type_data['initial_total_credit'])
            account_type_data['period_total_debit'] = "{:,.2f}".format(
                account_type_data['period_total_debit'])
            account_type_data['period_total_credit'] = "{:,.2f}".format(
                account_type_data['period_total_credit'])
            account_type_data['end_total_debit'] = "{:,.2f}".format(
                account_type_data['end_total_debit'])
            account_type_data['end_total_credit'] = "{:,.2f}".format(
                account_type_data['end_total_credit'])
        
        # Convert to list and sort by account type for consistent ordering
        move_line_list = list(account_type_totals.values())
        
        # Sort by account type order (assets first, then liabilities, equity, income, expenses)
        type_order = ['asset_', 'liability_', 'equity', 'income', 'expense', 'off_balance']
        move_line_list.sort(key=lambda x: next((i for i, prefix in enumerate(type_order) 
                                            if x['account_type'].startswith(prefix)), 999))
        
        journal = {
            'journal_ids': self.env['account.journal'].search_read([], ['name'])
        }
        return move_line_list, journal
