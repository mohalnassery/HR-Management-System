# Employee Offense Management Guide

This guide explains how to manage employee offenses in the HR Management System.

## Offense Status Workflow

1. **Active Status**: All new offenses are created with `is_active=True` by default.
   - Offenses remain active until explicitly deactivated.
   - Monetary penalties with remaining balances will always stay active.
   - Only when a monetary penalty is fully paid (remaining_amount = 0) will it automatically become inactive.

2. **Inactive Status**: Offenses become inactive when:
   - A monetary penalty is fully paid.
   - The offense is manually deactivated by an admin.
   - Year-end processes archive previous year offenses.

3. **Acknowledgment**: All offenses, whether active or inactive, can be acknowledged.
   - Acknowledgment is a separate flag from active status.
   - An offense can be active but not yet acknowledged.
   - Acknowledging an offense doesn't make it inactive.

## How to Use the Offense Management System

### Creating Offenses

1. Navigate to the employee's profile.
2. Click the "Offenses" tab.
3. Click "Add Offense".
4. Fill in the offense details:
   - Select the rule that was violated
   - Set the offense date
   - Choose the appropriate penalty
   - Add any relevant details
5. Click "Save".

### Acknowledging Offenses

1. From the employee's Offenses tab, find the offense to acknowledge.
2. Click the "View Details" button (eye icon).
3. In the offense details modal, click the "Acknowledge" button.
4. The offense status will change from "Pending" to "Acknowledged".
5. For record-keeping, the acknowledgment date will be recorded automatically.

### Managing Monetary Penalties

1. For monetary penalties, track the remaining amount.
2. Update the remaining amount as payments are made.
3. When the remaining amount reaches zero, the offense will be automatically marked as inactive.
4. The completion date will be set to the current date when the penalty is fully paid.

### Year-End Process

1. At the end of each year, previous year offenses can be deactivated automatically.
2. This is handled by a management command that can be scheduled to run annually.
3. Note that this doesn't delete offenses - they remain in the system but are marked inactive.

## Offense API Reference

The system provides the following endpoints for offense management:

- `GET /employees/{employee_id}/offenses/` - List employee offenses
- `POST /employees/{employee_id}/offenses/` - Create a new offense
- `GET /employees/{employee_id}/offenses/{offense_id}/` - Get offense details
- `POST /employees/{employee_id}/offenses/{offense_id}/acknowledge/` - Acknowledge an offense
- `POST /employees/{employee_id}/offenses/{offense_id}/deactivate/` - Deactivate an offense manually

## Troubleshooting

If offenses appear as inactive when they should be active:

1. Check the offense date is correct and not in a previous year.
2. Verify the offense was not manually deactivated.
3. For monetary penalties, ensure the remaining amount is greater than zero.
4. Run the provided fix_offenses.py script to correct the active status of existing offenses.
