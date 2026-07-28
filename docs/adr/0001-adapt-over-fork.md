# ADR: Use adapter/wrapper strategy instead of forking django-forms-workflows

## Context and Problem Statement

The current django-forms-workflows package features a fairly limited/straightforward authorization architecture around viewing/editing FormDefinition (schema) objects and form submission data that is primarily oriented around
the usage of the `is_staff` decorator to determine who has access to materials.

As a local government department with the over-arching goal of eventual CJIS/HIPAA compliance, it is imperative we follow the principle of least access--especially with regards to form submission data, which may contain sensitive information. We need the ability to establish individual permissions on multiple levels, including domain-level, department-level, and object-level.

## Considered Options

* Forking django-forms-workflows: this would be an easier implementation lift, as we could essentially override the current authorization decorator with whatever custom decorators we wanted to use. However, it would also make long-term maintenance of the project much more difficult, and current staffing resources are very limited. Future maintainers of this project have no guaranteed level of engineering ability; presenting them with potentially very large / complex diffs when the upstream repo changes and the fork must be maintained may present an intense practical challenge in the future.
* Adapting around django-forms-workflows. This would include selectively wrapping or replacing upstream views so that we are able to gatekeep authorization with more fine-grained permissions that utilize a department-based architecture, while keeping the dependency boundary explicit. Although this is more difficult during initial implementation, the upstream package is also being actively maintained with several commits a week that introduce new functionality, and initial conversations with the package maintainer make it seem like he would be very open/welcome to merging upstream PRs that could significantly reduce the amount of code we need to duplicate/rewrite, such as splitting form-builder.js into a series of separate modules (vs a single 2000 line file). The diff burden with upstream changes, in this case, would be more obvious (and hopefully therefore easier to implement said changes.)

## Decision Outcome

Chosen option: adapting django-forms-workflows without forking. Complex ongoing maintenance could represent a real future potential burden to form-builder's current home (a somewhat experimental department inside of a local government office with very tight resources). 

Essentially, this project should serve as an adapter layer for django-forms-workflows specifically for questions of authorization and access to FormDefinitions and form submissions data.

## Consequences

### Positive
- Maintain easier compatibility with upstream releases
- Avoid long-term fork maintenance burden
- Keep project-specific authorization logic owned by Form Manager
- Allow reusable improvements to be contributed upstream

### Negative
- Initial implementation is more complex
- Some upstream functionality will need wrappers/replacements, particularly with form-builder.js and workflow-builder.js

### Mitigations
- Keep adapter code isolated
- Submit upstream fixes whenever possible to reduce the need to re-create logic not related to authorization rules
- Document deviations