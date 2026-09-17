# TaskFlow

## Project membership

A project member is defined as either the project owner or any user currently assigned to at least one task in that project. Membership is derived from existing relationships; no separate `ProjectMember` table is used.

Members can view the project and all of its tasks. Project and task write operations remain restricted to the project owner.
