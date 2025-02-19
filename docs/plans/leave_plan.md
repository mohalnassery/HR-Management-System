# Leave Management System - Project Documentation

## Overview
This document outlines the scope and context for implementing the Leave Management module in your Django-based HR system. The system will integrate with your existing `employees_employee` table (using `employee_number` as the primary identifier) and enforce business rules for 10+ leave types.

---

## Core Tasks

### 1. **Leave Type Configuration**
**Context**: Define rules for all leave categories to ensure compliance with company policies.  
**Scope**:  
- Create system-wide leave types:  
  - Emergency (15 paid days/year)  
  - Annual (accrued at 2.5 days/month)  
  - Half Day (deduct 0.5 days from Annual balance)  
  - Permission (track hours instead of days)  
  - Sick Leave (tiered: 15 paid → 20 half-paid → 20 unpaid)  
  - Injury (unlimited, requires medical report)  
  - Relative Death (3 days/event)  
  - Maternity (60 days, female-only)  
  - Paternity (1 day, male-only)  
  - Marriage (3 days/event)  
- Configure reset periods (annual/monthly) and eligibility rules.

---

### 2. **Employee Leave Balances**
**Context**: Track available/used leave days per employee while respecting reset schedules.  
**Scope**:  
- Automatically calculate balances for:  
  - Annual Leave accrual (monthly)  
  - Emergency Leave resets (yearly)  
  - Sick Leave tier transitions  
- Handle prorated balances for mid-year hires.  
- Prevent negative balances through validation rules.

---

### 3. **Leave Request Workflow**
**Context**: Streamline employee submissions and managerial approvals.  
**Scope**:  
- Employee-facing features:  
  - Submit requests with dates/documents  
  - View real-time balance updates  
  - Cancel pending requests  
- Manager-facing features:  
  - Approve/reject requests with comments  
  - View team leave calendars  
- System validations:  
  - Prevent overlapping requests  
  - Block inactive employees (`is_active=False`)  
  - Enforce document requirements (e.g., injury reports)

---

### 4. **Notifications & Alerts**
**Context**: Keep stakeholders informed throughout the leave lifecycle.  
**Scope**:  
- Automatic notifications for:  
  - New requests (to managers)  
  - Approval/rejection (to employees)  
  - Balance resets (to all employees)  
  - Upcoming leave start dates (to managers)  
- Delivery via in-app alerts and email.

---

### 5. **Reporting & Compliance**
**Context**: Meet legal requirements and enable HR oversight.  
**Scope**:  
- Injury Leave tracking:  
  - Medical document storage  
  - Follow-up date reminders  
- Audit logs for all balance changes.  
- Exportable reports:  
  - Leave utilization by team/employee  
  - Sick Leave tier usage  
  - Maternity/Paternity leave history

---

### 6. **Security & Access Control**
**Context**: Protect sensitive leave data.  
**Scope**:  
- Role-based permissions:  
  - Employees: View own balances/requests  
  - Managers: Approve team requests  
  - HR Admins: Override balances, edit leave types  
- Document encryption for medical files.  
- API rate limiting to prevent abuse.

---

### 7. **System Integration**
**Context**: Connect with existing HR data.  
**Scope**:  
- Map `employee_number` to leave records.  
- Sync with `is_active` status to block inactive users.  
- Future-proof for integration with:  
  - Payroll (leave deductions)  
  - Attendance tracking (half-day reconciliation)

---

## Non-Scope Items
1. Employee onboarding/offboarding workflows  
2. Leave payout calculations  
3. Mobile app development  

---

## Success Criteria
- Employees can submit/comply with all 10+ leave types within 3 clicks.  
- Managers approve/reject requests within 24hrs (on average).  
- System handles concurrent leave requests from 500+ employees.  
- 100% audit compliance for Injury/Maternity leaves.  

---

## Next Steps
1. Finalize leave type priority order  
2. Validate accrual/reset rules with legal team  
3. Design approval escalation path for absent managers  