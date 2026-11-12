---
name: requirement-router
description: Capture, classify, deduplicate, and save software requirements to the correct registered project Markdown file. Use when a user requests a feature, UI change, business rule, database behavior, report, permission, integration, or bug fix.
---

# Requirement Router

Use this workflow before implementing a requested software change.

## 1. Resolve project
- Identify the current workspace/repository.
- Match it to `arr_list_projects`.
- If multiple registered projects match or no project matches, ask the user.
- Never guess a project.

## 2. Understand and classify
- Call `arr_list_modules(project_id)`.
- Read relevant existing requirements with `arr_search`.
- Select one primary module by business meaning, not just keyword.
- Identify related modules only when materially affected.
- Examples:
  - "Add birth-date column to student list" → primary `students`.
  - "Add teacher-in-charge column to student list" → primary `students`, related `teachers`.
  - "Create teacher profile form" → primary `teachers`.

## 3. Validate and save
- Call `arr_classify(project_id, request_text, ai_module, ai_type)`.
- `ai_module` must be one of the registered module IDs.
- If status is `needs_clarification`, do not save; ask one concise question.
- If classified, call `arr_save` with original request, title, faithful description,
  type, testable acceptance criteria, and related module IDs.
- Do not invent requirements or business rules.
- Treat `duplicate` and `possible_duplicate` as not saved.

## 4. Report
Return project, primary module, requirement ID, destination path, classification result,
and duplicate status.

## 5. Scope and safety
- Saving a requirement does not authorize implementation.
- Do not modify application source code unless separately requested.
- Do not commit, push, delete, or run destructive commands without explicit authorization.
- Never write outside the registered project and configured module destinations.
- If the request is an ordinary question, explanation, or conversation, do not capture it.
