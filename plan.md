# Meal Planner
We are building a meal planning app for my wife and I so that we can collab on the week's plan.

## Technical requirements
- Simple. Concise.
- Built in python
- Needs to be built for the web and mobile web. UI needs to be responsive
- Needs a database backend
  
## Functional requirements
- User-friendly
- Contains a library of potential meals
- Ability to favorites meals
- Allows the user to plan out meals for every day
- Accommodate ability to say "Leftovers" or "Out to eat" or any other reasoning on a particular day
- Builds out a shopping list(s) of the items. We might go to Stop & shop and costco. Would be awesome if it allowed us to move items between lists.
- Recipes should include images
  
## Implementation plan

### Tech Stack
- **Backend**: Flask or FastAPI (Python web framework)
- **Database**: SQLite for simplicity (can migrate to PostgreSQL later if needed)
- **Frontend**: HTML/CSS/JavaScript with a responsive framework (Bootstrap or Tailwind CSS)
- **Image Storage**: Local file system or cloud storage (S3/Cloudinary) for recipe images
- **Authentication**: Flask-Login or similar for user sessions

### Database Schema

**Users Table**
- id (primary key)
- username
- email
- password_hash
- created_at

**Meals Table**
- id (primary key)
- name
- description
- image_url
- ingredients (JSON or separate table)
- instructions
- created_by (user_id)
- created_at

**Favorites Table**
- id (primary key)
- user_id (foreign key)
- meal_id (foreign key)
- created_at

**MealPlan Table**
- id (primary key)
- user_id (foreign key)
- date
- meal_type (breakfast/lunch/dinner)
- meal_id (foreign key, nullable)
- custom_entry (text for "Leftovers", "Out to eat", etc.)
- created_at

**ShoppingLists Table**
- id (primary key)
- user_id (foreign key)
- store_name (e.g., "Stop & Shop", "Costco")
- week_start_date
- created_at

**ShoppingListItems Table**
- id (primary key)
- shopping_list_id (foreign key)
- item_name
- quantity
- unit
- meal_id (foreign key, nullable - to track which meal it's for)
- is_checked (boolean)
- created_at

### Development Phases

**Phase 1: Project Setup & Authentication**
- Initialize Flask project with folder structure
- Set up SQLite database with SQLAlchemy ORM
- Implement user registration and login
- Create basic responsive layout template
- Set up image upload functionality

**Phase 2: Meal Library**
- Create meal CRUD operations (Create, Read, Update, Delete)
- Build meal library UI with grid/card layout
- Implement image upload for recipes
- Add search and filter functionality
- Create favorites toggle functionality

**Phase 3: Weekly Meal Planning**
- Design calendar/weekly view interface
- Implement meal assignment to specific days/meal types
- Add drag-and-drop or modal-based meal selection
- Allow custom entries (leftovers, eating out, etc.)
- Create edit and delete functionality for planned meals

**Phase 4: Shopping List Generation**
- Auto-generate shopping list from weekly meal plan
- Parse ingredients from selected meals
- Create multiple shopping lists (by store)
- Implement item drag-and-drop between lists
- Add checkbox functionality for completed items
- Allow manual item additions

**Phase 5: Collaboration & Polish**
- Ensure both users can view/edit shared meal plans
- Add real-time updates or refresh mechanism
- Implement responsive design testing (mobile/tablet/desktop)
- Add notifications or highlights for recent changes
- Error handling and validation

### Core Features Checklist
- [x] User authentication (registration/login) - Phase 1
- [x] Meal library with CRUD operations - Phase 2
- [x] Recipe image upload and display - Phase 2
- [x] Favorites system - Phase 2
- [x] Weekly meal planner interface - Phase 3
- [x] Custom meal entries (leftovers, eating out) - Phase 3
- [x] Automated shopping list generation - Phase 4
- [x] Multiple shopping lists (by store) - Phase 4
- [x] Item movement between shopping lists - Phase 4
- [x] Shopping list item checkboxes - Phase 4
- [x] Responsive mobile/web design - All phases
- [x] Collaborative editing for two users - Phase 5 (partial)