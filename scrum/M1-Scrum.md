# Sprint Planning M1

## Sprint Information

- **Sprint / Milestone:** M1 – First Vertical Slice
- **Sprint dates:** 2026-10-05 to 2026-10-16
- **Planning meeting date:** 2026-10-05, During Lab 10-02, 10-09, 10-16
- **Facilitator:** Leo Cabral

### Team Members

- [x] Leo Cabral
- [x] Leyla Huseynova
- [x] Eleonora Ansella Kartono
- [x] Keenan Selbee

---

## 1. Sprint Goal

> What should the team have working by the end of this sprint?

**Sprint Goal:**

A customer can browse, search and filter restaurants, and view a restaurant's details and menu. 
Restaurants and menu items can be created and updated, with changes saved to JSON.

---

## 2. Sprint Backlog

Select the user stories that the team commits to working on during this sprint.

| User Story | Description | Priority | Primary Owner | Dependencies |
|---|---|---|---|---|
| #18 | List restaurants | High | Ansella | Restaurant data |
| #19 | Search restaurants by name | High | Ansella | #18 |
| #20 | Filter restaurants by cuisine | High | Ansella | #18 |
| #16 | View restaurant details | High | Keenan | Restaurant data |
| #24 | Create a restaurant | High | Keenan | #26 |
| #25 | Update restaurant information | High | Keenan | #26 |
| #26 | Add shared JSON storage (task) | High | Keenan | None |
| #33 | View restaurant's menu | High | Leyla | #16, restaurant IDs |
| #39 | View a menu item | Medium | Leyla | #33 |
| #40 | Add menu item | High | Leyla | #26, #33 |
| #41 | Update menu item | Medium | Leyla | #26, #33 |
| #37 | Frontend UI, CI and submission | High | Leo | Backend endpoints |


> **Important:** Primary ownership means that the student is responsible for coordinating the work. It does not mean that the student works alone or that other team members cannot contribute.

---

## 3. Task Decomposition

Break larger user stories into smaller tasks that can be implemented, reviewed, and tested.

### User Story #[NUMBER] — [TITLE]

### User Story #18 - List Restaurants

- [ ] Add/update the Pydantic response model
- [ ] Return each restaurant's ID, name, cuisine and address
- [ ] Return an empty list when there are no restaurants
- [ ] Tests
- [ ] Documentation / API updates

### User Story #19 - Search Restaurants by Name

- [ ] Implement restaurant name search
- [ ] Support partial matches
- [ ] Make search case insensitive
- [ ] Tests
- [ ] Documentation / API updates

### User Story #20 - Filter Restaurants by Cuisine

- [ ] Implement filtering by cuisine
- [ ] Make filtering case insensitive
- [ ] Support using search and cuisine filter together
- [ ] Tests
- [ ] Documentation / API updates

### User Story #16 - View Restaurant Details

- [ ] Add the lookup in the repository and handle missing restaurants in the service
- [ ] Add the endpoint with a Pydantic response model and ID validation
- [ ] Add addresses to the sample restaurants without changing their IDs
- [ ] Tests
- [ ] Documentation / API updates

### User Story #24 - Create a Restaurant

- [ ] Add the endpoint
- [ ] Add input validation
- [ ] Add saving logic with a server-assigned ID
- [ ] Tests
- [ ] Documentation / API updates

### User Story #25 - Update Restaurant Information

- [ ] Add the endpoint
- [ ] Add input validation (omitted fields and ID unchanged)
- [ ] Add saving logic
- [ ] Tests
- [ ] Documentation / API updates

### User Story #26 - Add Shared JSON Storage

- [ ] Configurable data folder using DATA_DIR
- [ ] Safe saves using temporary-file replacement
- [ ] One shared lock for read, change and save
- [ ] Tests
- [ ] Documentation / API updates

### User Story #33 - View Restaurant's Menu

- [ ] Add the menu item model, repository, service and endpoint
- [ ] Add menu data in a separate JSON file whose items belong to existing restaurants
- [ ] Return 404 for unknown restaurant IDs and 422 for invalid IDs
- [ ] Tests
- [ ] Documentation / API updates

### User Story #39 - View a Menu Item

- [ ] Add item lookup by ID
- [ ] Check that the item belongs to the restaurant
- [ ] Return 404 for unknown or mismatched IDs and 422 for invalid IDs
- [ ] Tests
- [ ] Documentation / API updates

### User Story #40 - Add Menu Item

- [ ] Add the request model and endpoint
- [ ] Add input validation (name, positive whole-number price, availability default)
- [ ] Add saving logic with a server-assigned ID
- [ ] Tests
- [ ] Documentation / API updates

### User Story #41 - Update Menu Item

- [ ] Add the MenuItemUpdate schema
- [ ] Add the repository update method using the shared JSON storage
- [ ] Add the PATCH endpoint (only supplied fields change)
- [ ] Tests
- [ ] Documentation / API updates

### User Story #37 - Frontend and Submission

- [ ] Restaurant list, details and menu UI
- [ ] Restaurant create/update forms
- [ ] CI setup and submission PDF
- [ ] Tests
- [ ] Documentation / API updates


---

## 4. Dependencies and Integration

Identify work that depends on another team member, subsystem, or component.

| Dependency | Related User Stories | Who is Responsible? | Planned Resolution |
|---|---|---|---|
| Shared JSON storage (#26) | #24, #25, #40, #41 | Keenan | Merge first so others can build on it |
| Restaurant IDs and sample data | #16, #18, #33 | Keenan | Agree on IDs before menu data is added |
| Backend endpoints | #37 | Ansella, Keenan, Leyla | Share endpoint paths with Leo early |


### Integration Plan

Each task is done on its own feature branch and merged into `main` through a pull request. Another teammate reviews each PR, and CI tests must pass before merging.

---

## 5. Risks and Potential Blockers

Identify anything that could prevent the team from achieving the sprint goal.

| Risk / Blocker                  | Impact                        | Planned Action                            | Owner |
|---|---|---|---|
| Persistence layer finished late | Create/update work is blocked | Build read-only endpoints first           | Keenan |
| PRs not reviewed in time        | Work not merged for M1        | Ask for reviews as soon as a PR is opened | Everyone |
| Short deadline                  | Features unfinished           | Focus on high-priority stories first      | Everyone |

---

## 6. Definition of Done

For work to be considered **DONE**, the team agrees that it must satisfy the following:

- [ ] Requirements/acceptance criteria are satisfied.
- [ ] Business logic is implemented in the appropriate service layer.
- [ ] Persistence is handled through the repository layer.
- [ ] Appropriate unit tests are included.
- [ ] Appropriate integration/API tests are included.
- [ ] Tests pass.
- [ ] Code has been reviewed by at least one teammate.
- [ ] Review feedback has been addressed.
- [ ] Documentation has been updated where necessary.
- [ ] The change is integrated into the team's working version.
- [ ] No known critical defects remain.

---

## 7. Sprint Commitment

Before ending the meeting, each team member should confirm their understanding of the sprint plan.

| Team Member              | Initial Responsibilities                                        | Confirmed |
|---|---|---|
| Eleonora Ansella Kartono | Restaurant discovery (list, search, filter), README              | Yes |
| Keenan Selbee            | Restaurant details, create, update, JSON persistence, PROVENANCE | Yes |
| Leyla Huseynova          | Menu management, scrum notes, project board                      | Yes |
| Leo Cabral               | Frontend, CI, submission PDF and release tag                     | Yes |

---

## Meeting Notes

- Meeting held on Oct 5 and discussion on the work and schedule arrangement during lab
- Each issue needs acceptance criteria, tests, and one main owner
- Every PR must be reviewed by another teammate before merging
- Sample data uses One Piece themed restaurants and should be adjusted in the later stages of project
