# Planned Menu

Draft nav schema for the logged-in menu. Not finalized — see **Open
Questions** at the bottom.

**Legend:** *(existing)* = URL already wired up · *(NEW)* = view/URL not yet
built

---

## Left side (main nav)

### Forms — top-level nav item (dropdown only, no direct link)

- **Create New Form** *(NEW)* — routes through the new department-picker
  view first, then creates the form, then redirects to
  `admin:form_builder_edit` so every form is scoped to a department from
  creation. A department must be chosen before the form is created, so
  there's no path through this flow that skips it. The residual gap —
  someone creating a bare `FormDefinition` directly through Django admin,
  bypassing the wizard entirely — is covered by a `post_save` signal that
  auto-creates an empty `FormPermissions` row whenever a `FormDefinition` is
  created by *any* path, combined with treating an empty `editor_departments`
  as "administrators only," never as accidentally-open. See
  `IMPLEMENTATION_PLAN.md`.
- **Archived Forms** *(NEW)* — a separate list view, not a "show archived"
  toggle inside **Edit Form**. Deliberately kept as its own destination
  rather than a filter state on the main list, so there's no ambiguity about
  whether you're looking at the live working set or not — a toggle risks
  someone leaving it on and getting confused later about why an archived
  form is showing up where the active ones normally are. Supports
  un-archiving.
- **Edit Form** *(NEW — replaces the old `/forms/` catalog entirely; the
  catalog will no longer be available to anyone)* — opens the form list
  view:
  - Filter: "Public forms" / "All forms"
  - Per-row actions (shown conditionally, based on what the viewing user
    can do with that specific form — the list view itself filters out rows
    the user has no access to, and the destination pages independently
    enforce the same check server-side, so hiding the button is never the
    only protection):
    - Fill Out Form — *(existing, `forms_workflows:form_submit`)*
    - Edit Form (fields/schema) — *(existing, `admin:form_builder_edit`,
      gated by Phase 5's `enforce_edit_access` — guardian `change_formdefinition`,
      granted via `FormPermissions.editor_departments`/`editor_users`)*
      - **Edit Form Permissions** *(NEW)* — intercepts the edit flow the
        same way Create is intercepted: shows permissions first, then
        routes to the form. Kept as a separate action from **Edit Form**
        rather than an always-shown intermediary — permissions change far
        less often than form content, and forcing a permissions screen
        before every content edit (even a typo fix) adds friction with no
        real benefit for the common case.
    - Add Workflow (approval stages) — *(NEW)*
    - Edit Workflow (approval stages) — *(existing, `admin:workflow_builder`,
      gated by a new `enforce_workflow_edit_access` — see Phase 5.5 in
      `IMPLEMENTATION_PLAN.md`. This is a different axis than editing the
      form's schema: it checks Phase 1.5's `can_edit_workflows` department
      capability, scoped by the same `FormPermissions.editor_departments`/
      `editor_users` used for schema-edit access — department members need
      the capability, individually-granted users don't.)*
    - Share (link/QR) — *(existing, `forms_workflows:form_qr_code`)*

### Form Submissions — dropdown

- **Submissions by Department** — *(NEW)*
- **My Submissions** — *(existing, `forms_workflows:my_submissions`)*

### Approvals — dropdown

- **Approval Inbox** — *(existing, `forms_workflows:approval_inbox`)*
- **Approval History** — *(existing, `forms_workflows:completed_approvals`)*

### Departments — dropdown

- **Manage Departments** *(NEW)* — department hierarchy view, with per-row
  edit / archive-request / delete-request actions. A button for department
  managers links to the corresponding Personnel view.
- **Add Department** — *(NEW)*

### Personnel — dropdown

- **Users by Department** (list) — *(NEW)*
- **Invite User** — *(existing, `accounts:invite_user`)*. Renamed from "Add
  User" — the invitation flow is the only path for adding anyone, so the
  label should say what it does.
- **Edit User** (department membership, deactivation) — *(NEW)*.
  Administrator-status toggle stays invite-only, not editable here (per
  earlier decision).

### Analytics — top-level link

*(existing, `forms_workflows:analytics_dashboard`)*

---

## Right side (unchanged from today)

User avatar dropdown (`{{ user.get_full_name|default:user.username }}`):

- Header: `{{ user.email }}`
- **Notification Preferences** — *(existing, `forms_workflows:notification_preferences`)*
- **Logout** — *(existing, `logout`)*

If not authenticated: just a **Login** link, as today.

---

## Open questions

1. **Manage Forms gating** — who can edit/manage a given form is governed
   by `FormPermissions.editor_departments`, a department-scoped relation,
   not a flat boolean like `is_administrator`/`is_department_owner`. May
   need its own check helper (e.g. in `permissions/checks.py`) rather than
   reusing the existing two.
2. **Analytics gating** — currently gated on Django's `user.is_staff` in
   the existing nav. Decide whether it stays `is_staff` or switches to
   `is_administrator` now that the rest of the menu is organized around the
   new permission model.
3. **Django Admin link** (the gear icon in the current nav) — largely
   moot now: Django admin is planned to be off by default (env-var gated,
   enabled only temporarily for IT/superuser debugging — see Phase 0.5 in
   `IMPLEMENTATION_PLAN.md`), so there's little reason for a permanent nav
   entry pointing at something normally unreachable. Whoever turns it on
   can just navigate to `/admin/` directly.
