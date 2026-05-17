# CITS3403-Project-Repository

## Group Members
| UWA ID     | Name              | GitHub Username     |
|------------|-------------------|---------------------|
| 24223148   | Josh Counsel      | JoshCounselUWA      |
| 24281778   | Hok Yin Chan      | Tommy05-hk          |
| 24274237   | Gautham Sujit     | gau-sjt             |
| 23725853   | Leo Mills         | 23725853            |

## DICE - Digital Inventory Control Environment
DICE is a web-based inventory management software that allows organisations to lend equipment within internal departments. It helps manage the equipment and items available to borrow or be assigned to individuals. 
### Workflow
* Users are assigned to departments.
* Each department has its own inventory of items that can be borrowed.
* Users can request for specific items by submitting requests.
* Requests are tracked, accepted or declined by departmen admins.
* Ongoing loans can be checked using a calendar view. Overdue loans are flagged.

There are different roles:
* **Business admin**: manage the organisation and create/manage departments and oversee company-wide settings such as branding.
* **Department admins**: manage individual departments — they invite members, manage that department's inventory, and approve or decline its loan requests.
* **Users**: regular members who can view inventory and submit loan requests within the departments they belong to.

Users connect to departments through an invitation system. A department admin or business admin can invite a user by username. User cans accept or decline the invitation which appears on their dashboard after logging in. Each user can be a part of multiple departments and can have varying roles.

After registering an account and logging in, a user is redirected to their dashboard, where loans, requests, and any pending department invitations are visible. Business admins access the App Settings page to manage departments and company branding. Department admins use each department's management page to invite members, change member roles,and remove members. Only Business admins can access app settings.


