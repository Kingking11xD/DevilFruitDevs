# M1 Design

Version: V1  
Last updated: October 5, 2026

> **Draft for team review:** This document proposes our M1 design and can be updated as needed. It is separate from the course-required Decision Receipt.

Build restaurant browsing, menus, and create/update features using a basic frontend and API. Leave accounts, authentication, carts, orders, deliveries, and distance features for later.

## Who does what

| Person | Work |
| --- | --- |
| Ansella | Restaurant list, search, cuisine filter, README. |
| Keenan | Restaurant details/create/update, shared JSON storage, provenance coordination. |
| Leyla | Menu/item browsing and create/update, scrum notes and board coordination. |
| Leo | Frontend, API integration, CI, submission PDF and tag. |

Everyone writes tests, maintains their issues and provenance, and reviews teammates' PRs.

## Data and validation

| Record | Fields |
| --- | --- |
| Restaurant | `id`, `name`, `cuisine`, `address` |
| Menu item | `id`, `restaurant_id`, `name`, `price`, `available` |

- IDs are positive integers assigned by the backend. Keep existing IDs; start at 1 for an empty list, otherwise use the next number above the highest saved ID. IDs cannot be edited. No deletion in M1.
- Every menu item belongs to an existing restaurant. Item IDs are unique across all menus; items cannot move between restaurants.
- Restaurant creation requires name, cuisine, and address. Remove surrounding spaces from text and reject blanks. Restaurant/menu-item names and cuisine: up to 100 characters; address: up to 250. Allow free-text cuisines and duplicate restaurant names.
- Menu creation takes `restaurant_id` from the URL, not the request body. The body requires `name` and a positive whole-number `price` in Berries; `available` is optional, true or false, and defaults to true.
- Use Pydantic create/update/response models. Reject unknown fields and client-supplied IDs.
- PATCH changes only supplied fields. Reject null values and empty updates. Return the complete saved record.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/restaurants` | List, search, and filter restaurants. |
| GET | `/restaurants/{id}` | Restaurant details. |
| POST | `/restaurants` | Create restaurant. |
| PATCH | `/restaurants/{id}` | Update restaurant. |
| GET | `/restaurants/{restaurant_id}/menu-items` | List menu items. |
| GET | `/restaurants/{restaurant_id}/menu-items/{item_id}` | Item details. |
| POST | `/restaurants/{restaurant_id}/menu-items` | Create item. |
| PATCH | `/restaurants/{restaurant_id}/menu-items/{item_id}` | Update item. |

Keep `/health` and `/docs`.

For restaurant lists, `search` matches part of a name and `cuisine` matches a complete cuisine value. Ignore capitalization and surrounding spaces. Blank filters do nothing; when both filters are supplied, both must match.

List endpoints return arrays ordered by ID. Details, create, and update endpoints return one complete record. No matches or an existing restaurant with no items returns `[]`. Include unavailable menu items with their availability flag.

**Responses:** 200 for reads/updates; 201 for creates; 404 for missing records or an item belonging to another restaurant; 422 for invalid input; 500 for storage failures. Errors use `{"detail": "message"}`, except 422 uses FastAPI's standard validation-error list. Never expose file paths or contents in errors.

## Saving data

Follow **Routes -> Services -> Repositories -> JSON**: routes handle HTTP, schemas check input, services enforce business rules, and repositories read/write files.

- Use `data/restaurants.json` and `data/menu_items.json`, each containing a list of records. Make the data folder configurable and independent of the launch directory.
- Keenan provides shared JSON reading/saving. Keep restaurant listing compatible; add lookup/create/update methods.
- Use one shared storage lock for all JSON reads and updates. Hold it for the complete read-change-save operation. Restaurant and menu operations take turns, keeping the implementation simple. Write a temporary file beside the original, then replace the original only after writing succeeds. Preserve old data if saving fails. Use UTF-8 and two-space indentation.
- Run one backend process. The lock does not protect against other processes, external edits, or cloud-sync conflicts; avoid those while running. Saves across both files are not one transaction. Change functions only modify the supplied records; they must not call storage functions again while holding the lock.
- Missing or corrupt required files must produce an error. Never silently reset data or overwrite it at startup. An intentionally empty menu file contains `[]`.
- Add sample addresses to existing restaurant records without changing their IDs.

## Testing

Use isolated test data and test successful requests, invalid input, missing records, restart persistence, and failed writes.
