# Planned Menu

Draft nav schema for the logged-in menu. Not finalized — see open questions at the bottom.

## Left side (main nav)

### Forms
Top-level link → single list view (**NEW**, not yet built; replaces `forms_workflows:form_list`).

- Second level menu link **Create New Form** — this wires to the new department view first, then form is created, and then it reroutes to "admin:form_builder_edit" so that forms can be scoped to departments. 
- Second level menu link ***Edit Form*** - this will replace /forms/ so form catalog is not available to anybody.
- Per-row actions (shown conditionally, based on what the viewing user can do with that specific form):
  - **Fill out form** (Fill Out Form) — existing, `forms_workflows:form_submit`
  - **Edit Form** (fields/schema) — existing, `admin:form_builder_edit`
    - **Edit Form Permissions** — **NEW**, no view yet - this happens because we intercept the edit view, the same way we intercept the create view. Have them edit the permissions first, then route to the form.
  - **Add workflow** - approval stages.
  - **Edit Workflow** (approval stages) — existing, `admin:workflow_builder`
  - **Share** (link/QR) — existing, `forms_workflows:form_qr_code`

### Form Submissions
Dropdown.
- **Submissions by Department** — **NEW**, no view yet
- **My Submissions** — existing, `forms_workflows:my_submissions`

### Approvals
Dropdown.

- **Approval Inbox** — existing, `forms_workflows:approval_inbox`
- **Approval History** — existing, `forms_workflows:completed_approvals`

### Departments
Dropdown.
- **Manage Departments** (edit/archive) — Department heirarchy, with per row options to edit, archive_request, delete_request. Button for manager users goes to the corresponding personnel view. **NEW**, no view yet
- **Add Department** — **NEW**, no view yet


### Personnel
Dropdown.

- **Users by Department** (list) — **NEW**, no view yet
- **Add User** — existing, `accounts:invite_user`
- **Edit User** (department membership, deactivation) — **NEW**, no view yet.
  Administrator-status toggle stays invite-only (not editable here), per earlier decision.

### Analytics
Top-level link — existing, `forms_workflows:analytics_dashboard`

## Right side (unchanged from today)

User avatar dropdown (`{{ user.get_full_name|default:user.username }}`):

- Header: `{{ user.email }}`
- **Notification Preferences** — existing, `forms_workflows:notification_preferences`
- **Logout** — existing, `logout`

If not authenticated: just a **Login** link, as today.

## Open questions

- **Manage Forms gating** — who can edit/manage a given form is governed by `FormPermissions.editor_departments`, a department-scoped relation, not a flat boolean like `is_administrator`/`is_department_owner`. May need its own check helper (e.g. in `permissions/checks.py`) rather than reusing the existing two.
- **Analytics gating** — currently gated on Django's `user.is_staff` in the existing nav. Decide whether it stays `is_staff` or switches to `is_administrator` now that the rest of the menu is organized around the new permission model.
- **Django Admin link** (the gear icon in the current nav) — not placed anywhere in this schema. Decide where it goes, if anywhere.
