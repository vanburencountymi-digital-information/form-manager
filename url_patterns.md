# django-forms-workflows URL patterns

Namespace `forms_workflows`, mounted at `/forms/` in `forms_manager/urls.py`
(`path('forms/', include('django_forms_workflows.urls'))`).

| URL name | Path | What it does |
|---|---|---|
| `forms_workflows:form_list` | `/forms/` | List all active form templates the current user has access to (staff/superusers see everything; other users are filtered by form- and category-level group restrictions). |
| `forms_workflows:form_submit` | `/forms/<slug>/submit/` | Fill out and submit a form. Supports both authenticated and anonymous (public) access depending on the form's `requires_login` setting. |
| `forms_workflows:form_embed` | `/forms/<slug>/embed/` | Render the form in a minimal layout for iframe embedding (only if `embed_enabled` on the form). |
| `forms_workflows:form_qr_code` | `/forms/<slug>/qr/` | Return a QR-code image (SVG or PNG) encoding the form's submit URL. Public, no login required. |
| `forms_workflows:form_auto_save` | `/forms/<slug>/auto-save/` | AJAX endpoint to auto-save a form draft (authenticated users only). |
| `forms_workflows:batch_template_download` | `/forms/<slug>/batch-template/` | Download a dynamic Excel template (with instructions and choice references) for bulk/batch submission of a form. |
| `forms_workflows:batch_import_upload` | `/forms/<slug>/batch-import/` | Upload a filled-in batch Excel file; validates each row and creates submissions, reporting any row-level errors. |
| `forms_workflows:my_submissions` | `/forms/my-submissions/` | View the current user's own submissions, optionally filtered by `?category=<slug>`. |
| `forms_workflows:submission_detail` | `/forms/submissions/<id>/` | View a single submission's details. Viewable by the submitter, approvers, reviewers, admins, or superusers. |
| `forms_workflows:withdraw_submission` | `/forms/submissions/<id>/withdraw/` | Let the submitter withdraw their own submission (if the form allows withdrawal). |
| `forms_workflows:discard_draft` | `/forms/submissions/<id>/discard/` | Permanently delete a draft submission owned by the current user. |
| `forms_workflows:resubmit_submission` | `/forms/submissions/<id>/resubmit/` | Create a new draft pre-filled from a rejected/withdrawn submission, so the user can correct and resubmit. |
| `forms_workflows:submission_pdf` | `/forms/submissions/<id>/pdf/` | Generate and serve a PDF of a submission (availability depends on the form's `pdf_generation` setting: none / anytime / post_approval). |
| `forms_workflows:bulk_export_submissions` | `/forms/submissions/bulk-export/` | Export a set of selected submissions to an Excel spreadsheet (POST list of submission IDs). |
| `forms_workflows:bulk_export_submissions_pdf` | `/forms/submissions/bulk-export-pdf/` | Export a set of selected submissions as one merged PDF. |
| `forms_workflows:sync_export` | `/forms/forms-sync/export/` | Export form definitions as JSON (token-authenticated sync API, not session-based). |
| `forms_workflows:sync_import` | `/forms/forms-sync/import/` | Import form definitions from a JSON payload (token-authenticated sync API). |
| `forms_workflows:sub_workflow_detail` | `/forms/sub-workflows/<instance_id>/` | View details of a single sub-workflow instance attached to a parent submission (e.g. a payment step). |
| `forms_workflows:approval_inbox` | `/forms/approvals/` | View pending approval tasks for the current user, optionally filtered by `?category=` and `?role=mine\|reviewing\|overseeing`. |
| `forms_workflows:completed_approvals` | `/forms/approvals/completed/` | View completed submissions (approved/rejected/withdrawn) the user was involved in approving — an approval history/audit view. |
| `forms_workflows:approve_submission` | `/forms/approvals/<task_id>/approve/` | Approve or reject a submission at the current workflow stage. |
| `forms_workflows:reassign_task` | `/forms/approvals/<task_id>/reassign/` | Reassign a pending approval task to another member of the stage's approval group (if the stage allows reassignment). |
| `forms_workflows:submission_success` | `/forms/submissions/<id>/success/` | Custom per-submission success/thank-you page, supporting answer-piped content from the form's `success_message`. |
| `forms_workflows:public_submission_confirmation` | `/forms/submitted/` | Generic thank-you page shown after an anonymous (public) form submission. |
| `forms_workflows:payment_initiate` | `/forms/payments/<submission_id>/initiate/` | Start payment for a submission — returns an inline payment page (Stripe) or redirects to an external portal (ECSI, PayPal). |
| `forms_workflows:payment_confirm` | `/forms/payments/<payment_record_id>/confirm/` | AJAX endpoint called after an inline payment succeeds; verifies with the provider and finalizes the submission. |
| `forms_workflows:payment_return` | `/forms/payments/<submission_id>/return/` | Return URL for redirect-flow payment providers; forwards provider query params to confirm the payment. |
| `forms_workflows:payment_cancel` | `/forms/payments/<submission_id>/cancel/` | User cancelled payment on the external portal. |
| `forms_workflows:payment_webhook` | `/forms/payments/webhook/<provider_name>/` | Generic payment provider webhook receiver. |
| `forms_workflows:analytics_dashboard` | `/forms/analytics/` | Render the analytics dashboard with submission and approval metrics (`?days=` and `?form=` filters). |
| `forms_workflows:analytics_export_csv` | `/forms/analytics/export/` | Export the analytics summary data as CSV. |
| `forms_workflows:notification_preferences` | `/forms/preferences/notifications/` | Let the signed-in user view and mute/unmute each notification rule they'd otherwise receive. |
| `forms_workflows:my_submissions_ajax` | `/forms/my-submissions/data/` | Server-side DataTables JSON endpoint backing the "My Submissions" table. |
| `forms_workflows:approval_inbox_ajax` | `/forms/approvals/data/` | Server-side DataTables JSON endpoint backing the pending approval inbox table. |
| `forms_workflows:completed_approvals_ajax` | `/forms/approvals/completed/data/` | Server-side DataTables JSON endpoint backing the completed-approvals history table. |

## REST API (namespace `forms_workflows_api`)

Mounted at `/api/` in `forms_manager/urls.py`
(`path("api/", include("django_forms_workflows.api_urls"))`). This one **is** wired up
in this project, unlike the SSO urls below.

| URL name | Path | What it does |
|---|---|---|
| `forms_workflows_api:docs` | `/api/docs/` | Swagger UI for the REST API (staff session auth). |
| `forms_workflows_api:schema` | `/api/schema/` | OpenAPI 3.0 JSON schema (staff session auth). |
| `forms_workflows_api:form_list` | `/api/forms/` | List `api_enabled` forms (Bearer token auth). |
| `forms_workflows_api:form_detail` | `/api/forms/<slug>/` | Get the field schema for one form (Bearer token auth). |
| `forms_workflows_api:form_submit` | `/api/forms/<slug>/submit/` | Submit a form via the API (Bearer token auth). |
| `forms_workflows_api:submission_status` | `/api/submissions/<id>/` | Poll a submission's status (Bearer token auth). |

## Admin-only builder URLs (namespace `admin`)

Not a separate include — `FormDefinitionAdmin.get_urls()` in `admin.py` registers these
directly onto the `admin:` namespace, under the `FormDefinition` changelist's base path:
`/admin/django_forms_workflows/formdefinition/`. (There's also an orphaned
`form_builder_urls.py` shipped in the package with an overlapping but incomplete set of
names under `app_name = "form_builder"` — it's never `include()`d anywhere, so it isn't
reachable; ignore it.)

| URL name | Path (relative to `/admin/django_forms_workflows/formdefinition/`) | What it does |
|---|---|---|
| `admin:form_diff` | `diff/` | Side-by-side JSON diff of two or more selected form definitions (`?pks=1,2`). |
| `admin:form_builder_new` | `builder/new/` | Visual form builder page for creating a new form. |
| `admin:form_builder_edit` | `builder/<form_id>/` | Visual form builder page for editing an existing form. |
| `admin:form_builder_api_load` | `builder/api/load/<form_id>/` | Load a form's data as JSON for the builder UI. |
| `admin:form_builder_api_save` | `builder/api/save/` | Save (create/update) a form's definition and fields from the builder UI. |
| `admin:form_builder_api_preview` | `builder/api/preview/` | Render a live preview of how the form will look to end users. |
| `admin:form_builder_api_templates` | `builder/api/templates/` | List available form templates, organized by category. |
| `admin:form_builder_api_load_template` | `builder/api/templates/<template_id>/` | Load a specific form template's data to populate the builder. |
| `admin:form_builder_api_clone` | `builder/api/clone/<form_id>/` | Clone an existing form (fields + settings), appending "(Copy)" and a new slug. |
| `admin:form_builder_api_shared_lists` | `builder/api/shared-lists/` | List all shared option lists (reusable choice sets for dropdowns/radios). |
| `admin:form_builder_api_shared_list_save` | `builder/api/shared-lists/save/` | Create or update a shared option list. |
| `admin:form_builder_api_shared_list_delete` | `builder/api/shared-lists/delete/<list_id>/` | Delete a shared option list. |
| `admin:form_builder_api_doc_templates` | `builder/api/doc-templates/<form_id>/` | List document templates (e.g. PDF layouts) attached to a form. |
| `admin:form_builder_api_doc_template_save` | `builder/api/doc-templates/<form_id>/save/` | Create or update a document template for a form. |
| `admin:form_builder_api_doc_template_delete` | `builder/api/doc-templates/<form_id>/delete/<template_id>/` | Delete a document template. |
| `admin:workflow_builder` | `<form_id>/workflow/` | Visual workflow builder page for a form's approval stages. |
| `admin:workflow_builder_load` | `workflow/api/load/<form_id>/` | Load a form's workflow data as JSON for the builder UI. |
| `admin:workflow_builder_save` | `workflow/api/save/` | Save (create/update) a form's workflow stages from the builder UI. |
| `admin:formdefinition_sync_import` | `sync-import/` | Admin page to import form definitions from an uploaded JSON file or pasted raw JSON. |
| `admin:formdefinition_sync_pull` | `sync-pull/` | Multi-step admin page to pull form definitions from a remote instance (picker → fetch/select → import). |
| `admin:formdefinition_sync_push` | `sync-push/` | Multi-step admin page to push local form definitions to a remote instance (picker → select/diff → push). |

## Conditional: SSO (namespace `forms_workflows_sso`)

Only registered if SSO dependencies are installed (`is_sso_available()`), and only mounted
if the project itself includes `django_forms_workflows.sso_urls` (not currently wired up in
this project's `urls.py`). Listed here for reference since it ships in the package:

| URL name | Path | What it does |
|---|---|---|
| `forms_workflows_sso:login` | `/sso/login/` | SSO provider selection page, or redirect straight to the single configured provider. |
| `forms_workflows_sso:saml_login` | `/sso/saml/login/` | Initiate SAML login. |
| `forms_workflows_sso:saml_acs` | `/sso/saml/acs/` | SAML Assertion Consumer Service (handles the IdP's SAML response). |
| `forms_workflows_sso:saml_metadata` | `/sso/saml/metadata/` | SP metadata document for IdP configuration. |
| `forms_workflows_sso:saml_sls` | `/sso/saml/sls/` | SAML Single Logout Service. |
