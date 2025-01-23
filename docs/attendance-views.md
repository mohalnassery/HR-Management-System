# Attendance Management Views

## Template Views

### attendance_list
- URL: `/attendance/`
- Method: `GET`
- Description: Main attendance listing page
- Context: List of departments

### calendar_view
- URL: `/attendance/calendar/`
- Method: `GET`
- Description: Calendar view of attendance

### attendance_detail_view
- URL: `/attendance/detail/<attendance_id>/`
- Method: `GET`
- Description: Detailed view of attendance record
- Features:
  - Employee info
  - In/Out times
  - Total hours
  - Late status
  - Shift info

## API ViewSets

### AttendanceViewSet
- Base URL: `/api/attendance/`
- Actions:
  - List (`GET`)
  - Create (`POST`)
  - Update (`PUT/PATCH`)
  - Delete (`DELETE`)
- Features:
  - Date range filtering
  - Department filtering
  - Status filtering (late/present/absent)
  - Excel upload support

### ShiftViewSet
- Base URL: `/api/shifts/`
- Standard CRUD operations
- Filters active shifts only

### LeaveViewSet
- Base URL: `/api/leaves/`
- Standard CRUD operations
- Status filtering

### HolidayViewSet
- Base URL: `/api/holidays/`
- Standard CRUD operations
- Active holidays only

## API Endpoints

### get_calendar_events
- URL: `/api/calendar-events/`
- Method: `GET`
- Params: `start`, `end`
- Returns: Attendance events with status colors

### attendance_detail_api
- URL: `/api/attendance/<id>/details/`
- Method: `GET`
- Returns: Detailed attendance info including edits

### attendance_record_api
- URL: `/api/attendance/<id>/`
- Methods: `PATCH`, `DELETE`
- Features:
  - Time updates
  - Edit tracking
  - Soft deletes

### search_employees
- URL: `/api/search-employees/`
- Method: `GET`
- Param: `q`
- Features:
  - Search by ID or name
  - Limit 10 results

## Data Model Changes

The views now use a consolidated Attendance model instead of separate:
- AttendanceRecord
- AttendanceLog  
- AttendanceEdit

Key changes:
- Single attendance record per employee per day
- Built-in edit tracking
- Original and current times stored together
- Direct access to all attendance data
- Improved query performance
