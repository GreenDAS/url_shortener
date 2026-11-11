# Spec Sheet: User Swapping

| | |
|---|---|
| **Author** | Daniel S. |
| **Date** | 11/11/2026 |
| **Version** | V1.0 |
| **Jira** | URL-12 (user swapping). Login itself is URL-13 |
| **Files** | `app/accounts.py` (uses `app/users.py`) |
| **Tests** | `tests/test_accounts.py` |

## 1. Purpose

Lets someone who has logged into more than one account on the same browser
jump between them from a "Switch user" menu without typing the password
again (decided by Dan 11/11/2026). Each account must have logged in on this
browser once, with its password, before it can be switched to.

## 2. Inputs

| Input | Where | Notes |
|---|---|---|
| `user_id` | login route (URL-13) after `verify_user()` passes | goes to `add_account()` |
| `user_id` | `POST /switch/<int:user_id>` from the header menu | must be an int, else 404 |
| Session cookie | the browser | signed with `SECRET_KEY` so it can't be edited |

## 3. Outputs and State

The session (Flask's signed cookie) holds:

| Key | Example | Meaning |
|---|---|---|
| `account_ids` (`ACCOUNTS_KEY`) | `[7, 3, 12]` | every account signed in here, most recently used first, at most 5 (`MAX_ACCOUNTS`) |
| `user_id` (`ACTIVE_KEY`) | `7` | the active account |

| Function / Route | Output |
|---|---|
| `POST /switch/<id>` | `302` to `/` if that id is signed in here, else `403 Forbidden` |
| `GET /switch/<id>` | `405 Method Not Allowed` |
| `switch_choices()` | list of `{id, username, active}` for the menu |

## 4. Behavior

* **add_account(id)** removes the id if it's already in the list, puts it
  first, trims the list to 5 (oldest falls off) and makes it active.
* **switch_to(id)** only works for ids already in the list, and reuses
  `add_account` so the account moves to the front.
* **remove_active_account()** takes the active id out. If anyone is left,
  the first one becomes active. Otherwise `user_id` is removed (logged out).
* **switch_choices()** looks up each id's username and skips ids whose
  account has been deleted since.
* **Safety:**
  * The cookie is signed, so a user can't add someone else's id.
  * `/switch` is POST only, so a link someone sends can't swap your account.
  * It always redirects to `/`, never to the Referer, so it can't be used to
    bounce people to another site.

## 5. Function Reference

| Function | Arg(s) | Returns |
|---|---|---|
| `signed_in_ids()` | | copy of the id list (empty if none) |
| `add_account(user_id)` | id that just logged in | Nothing |
| `switch_to(user_id)` | id to swap to | `True` if swapped, `False` if not signed in here |
| `remove_active_account()` | | new active id, or `None` |
| `current_user_id()` | | active id, or `None` |
| `switch_choices()` | | list of menu dicts |
| `switch_user(user_id)` | route `POST /switch/<int:user_id>` | redirect to `/`, or 403 |

## 6. Flow Chart: `POST /switch/<id>`

```mermaid
flowchart TD
    A(["Header menu: POST /switch/ID"]) --> B{"ID is an int?"}
    B -->|No| X0([404 Not Found])
    B -->|Yes| C["switch_user(ID) calls switch_to(ID)"]
    C --> D{"ID in session account_ids?"}
    D -->|No| X1(["abort(403)"])
    D -->|Yes| E["add_account(ID)"]
    E --> F([302 redirect to /])
```

## 7. Flow Chart: `add_account`

```mermaid
flowchart TD
    A(["add_account(user_id)"]) --> B["ids = signed_in_ids() without user_id"]
    B --> C["Insert user_id at the front"]
    C --> D["session account_ids = first 5 of ids"]
    D --> E["session user_id = user_id"]
    E --> F([Done])
```

## 8. Flow Chart: `remove_active_account` (log out one account)

```mermaid
flowchart TD
    A(["remove_active_account()"]) --> B["ids = signed_in_ids() without the active id"]
    B --> C["session account_ids = ids"]
    C --> D{ids empty?}
    D -->|No| E["session user_id = ids[0]"]
    E --> F(["Return ids[0]"])
    D -->|Yes| G["Remove user_id from the session"]
    G --> H([Return None])
```

## 9. Flow Chart: `switch_choices` (menu list)

```mermaid
flowchart TD
    A(["switch_choices()"]) --> B["choices = []"]
    B --> C{Next id in signed_in_ids?}
    C -->|No more| Z([Return choices])
    C -->|id| D["get_user_by_id(id)"]
    D --> E{Account still exists?}
    E -->|No| C
    E -->|Yes| F["Add id, username, active = (id == current_user_id())"]
    F --> C
```

## 10. Tests

* `tests/test_accounts.py` runs inside `app.test_request_context()` with
  `get_user_by_id` mocked. It checks first login, newest first ordering, no
  duplicates, the 5 account cap, switching to a signed in vs unknown
  account, logout handing over to the next account and logging fully out,
  the menu (active flag, deleted accounts skipped), and the route's 302,
  403 and 405.
* Run: `python -m unittest tests.test_accounts -v`

## 11. Known Limits and Notes

* Nothing calls `add_account()` yet because the login page (URL-13) isn't
  built. Until then the list is always empty and every switch is a 403.
* The header menu and logout route are not built yet either.
