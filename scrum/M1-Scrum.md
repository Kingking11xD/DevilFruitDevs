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
| #5 | Restaurant discovery: list, search by name (#19), filter by cuisine (#20) | High | Ansella | Restaurant data |
| #24, 25 | Restaurant details, create and update a restaurant | High | Keenan | JSON persistence (#26) |
| #6 | Menu management: view menu, view item, add item, update item | High | Leyla | JSON persistence (#26), restaurant IDs|
| # | Frontend UI, CI and submission | High | Leo | Backend endpoints |


> **Important:** Primary ownership means that the student is responsible for coordinating the work. It does not mean that the student works alone or that other team members cannot contribute.

---

## 3. Task Decomposition

Break larger user stories into smaller tasks that can be implemented, reviewed, and tested.

### User Story #[NUMBER] — [TITLE]

- [ ] Task
- [ ] Task
- [ ] Task
- [ ] Tests
- [ ] Documentation / API updates

---

## 4. Dependencies and Integration

Identify work that depends on another team member, subsystem, or component.

| Dependency                     | Related User Stories | Who is Responsible?    | Planned Resolution |
|---|---|---|---|
| Shared JSON persistence        | #24, #25, #6         | Keenan                 | Merge first so others can build on it |
| Restaurant IDs and sample data | #5, #6               | Keenan                 | Agree on IDs before menu data is added |
| Backend endpoints              | Frontend             | Ansella, Keenan, Leyla | Share endpoint paths with Leo early |


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
