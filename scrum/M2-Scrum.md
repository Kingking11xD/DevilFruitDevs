# M2 Sprint Plan

## Sprint info

- Milestone: M2 Integrated Core System
- Due: November 20, 2026 at 11:59 pm
- Team: Leo Cabral, Leyla Huseynova, Eleonora Ansella Kartono, Keenan Selbee
- Based on the [M2 design](../docs/m2-design.md)

## 1 Sprint goal

Get the full flow working

Customer -> Restaurant -> Menu -> Cart -> Checkout -> Order

Customers can sign in, add an address, build a cart, check out and see their saved order

Keep the M1 browsing and restaurant/menu management working with the right permissions

Order status changes, deliveries and reports are for M3

## 2 Who does what

| Area | Main work | Owner | Needs |
| --- | --- | --- | --- |
| Accounts | Sign-up, login, profile, address, deactivation and permissions | Keenan | Shared JSON storage |
| Menus and carts | Availability, cart changes, prices and totals | Ansella | Accounts, restaurants, menus and shopping storage |
| Checkout and orders | Checkout checks, saving orders and order history | Leyla | Accounts, menus, carts and shopping storage |
| Frontend | Screens and API calls for the full flow | Leo | Backend endpoints and examples |

Each person leads their area but we can help each other with fixes and testing

Everyone updates their issues, tests, docs and provenance and helps review PRs

The design does not name an owner for scrum notes or the project board

## 3 Main tasks

### Keenan - accounts and permissions

- register customers and hash passwords
- add login and tokens to identify the signed-in account
- let customers change their name and address or deactivate their account
- add shared checks for roles, ownership and assigned restaurants
- set up demo admin and staff accounts
- test accounts with carts, checkout and orders

### Ansella - menus and carts

- support unavailable and deactivated menu items
- create or get the customer's active cart
- add items, change quantities, remove items and clear the cart
- show current item details, problems and totals from the backend
- reject invalid quantities, mixed restaurants and missing or unavailable items
- test carts with accounts, menus and checkout

### Leyla - checkout and orders

- recheck the customer, address, restaurant, cart and menu items
- recalculate the total and ask for confirmation if it changed
- save a copy of the customer, restaurant, item and price details with the order
- save the order and closed cart together in one file replacement
- return the same order if its owner retries checkout
- let customers view their own orders
- test failed saves and make sure later changes do not alter old orders

### Leo - frontend

- connect registration, login and profile screens
- connect restaurant/menu browsing and management for allowed users
- connect cart changes, totals, checkout and order history
- send auth headers and show useful errors
- keep tokens in memory so a page refresh needs another login
- update frontend setup instructions and help test the full flow

## 4 Connecting the work

| Shared work | Plan |
| --- | --- |
| Account and permission checks | Keenan provides the helpers and each owner uses and tests them |
| Menu data and cart contents | Ansella makes these available for checkout |
| Saving carts and orders | Leyla and Ansella make sure both are saved together |
| Frontend API calls | Backend owners share examples and help Leo fix connection problems |

Get registration and login ready first, then connect a simple order flow before adding the other cases

Use the shared storage helpers and lock for file changes
Accounts, restaurants and menus stay in list files
Carts and orders share `shopping.json`

Services use repositories and do not import routes

Use feature branches and reviewed PRs
Fix review comments and get CI passing before merging

## 5 Things to watch

| Problem | What to do | Who |
| --- | --- | --- |
| Frontend expects different API data | Share examples and test real requests early | Leo and backend owner |
| Missing permission checks | Test roles, ownership and inactive accounts | Feature owner |
| Only the order or cart gets saved | Check everything first and save both together | Leyla and Ansella |
| Two requests overwrite each other | Use the same storage lock and do not take it again inside a locked call | Backend owners |
| Reviews or fixes are late | Say what is blocked and split the remaining work | Everyone |
| Missing docs or evidence | Update docs and collect code, test and review links | Everyone |

## 6 When a task is done

Use this for each feature or fix

- [ ] meets the issue's acceptance criteria
- [ ] keeps route, service and repository work in the right place
- [ ] checks permissions and business rules in the backend
- [ ] passes the relevant tests using separate test data
- [ ] keeps saved data and links between records after restart
- [ ] has review feedback addressed and is merged
- [ ] works through the frontend and real API
- [ ] has docs and provenance updated

## Team communication

we discussed M2 during labs and kept in touch through Discord between labs

we used Discord to plan features, split work, share progress, request PR reviews, discuss fixes and coordinate merges

main discussions covered cart and checkout integration, permissions, frontend login and the remaining docs and submission tasks
