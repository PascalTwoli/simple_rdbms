# Task Manager - Web Demo Application

A simple task management web application demonstrating CRUD operations using the custom RDBMS backend.

---

## Overview

This web application serves as a practical demonstration of the Simple RDBMS project. It showcases how the custom database engine handles real-world operations through a clean, modern user interface.

### Purpose

The Task Manager demonstrates:
- **Create** - Adding new tasks to the database
- **Read** - Fetching and displaying all tasks
- **Update** - Modifying task details and completion status
- **Delete** - Removing tasks from the database

---

## Quick Start

```bash
# From the project root directory
python3 webapp.py

# Open in browser
# http://localhost:5050
```

---

## File Structure

```
static/
├── index.html    # Main HTML structure
├── style.css     # Styling and responsive design
├── app.js        # Frontend JavaScript (API calls, DOM manipulation)
└── README.md     # This file
```

---

## Features

### Task Management

| Feature | Description |
|---------|-------------|
| **Add Tasks** | Create tasks with title, description, and priority level |
| **View Tasks** | See all tasks in a responsive list layout |
| **Edit Tasks** | Modify task details via a modal dialog |
| **Delete Tasks** | Remove tasks with confirmation prompt |
| **Toggle Complete** | Mark tasks as done/undone with checkbox |
| **Priority Levels** | Low, Medium, High priority badges |

### User Interface

- **Modern Design** - Clean, minimal interface with smooth transitions
- **Responsive** - Works on desktop and mobile devices
- **Modal Dialogs** - Edit tasks without leaving the page
- **Visual Feedback** - Completed tasks show strikethrough styling
- **Empty State** - Friendly message when no tasks exist

---

## Technical Details

### Frontend Stack

| Technology | Purpose |
|------------|---------|
| **HTML5** | Semantic markup structure |
| **CSS3** | Modern styling with Flexbox, custom properties |
| **Vanilla JS** | No framework dependencies, pure JavaScript |
| **Fetch API** | HTTP requests to backend |
| **Google Fonts** | Inter font family |

### API Integration

The frontend communicates with the Flask backend via REST API:

```javascript
// Base URL for all API calls
const API_BASE = '/api/tasks';

// Available operations
GET    /api/tasks        // List all tasks
POST   /api/tasks        // Create new task
GET    /api/tasks/:id    // Get single task
PUT    /api/tasks/:id    // Update task
DELETE /api/tasks/:id    // Delete task
```

### Data Model

Each task has the following structure:

```javascript
{
  "id": 1,              // INTEGER PRIMARY KEY (auto-generated)
  "title": "...",       // TEXT NOT NULL
  "description": "...", // TEXT (optional)
  "priority": "medium", // TEXT: "low" | "medium" | "high"
  "completed": false    // BOOLEAN
}
```

This maps directly to the `tasks` table created in the RDBMS:

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT,
    completed BOOLEAN
);
```

---

## Code Organization

### index.html

- **Header** - App title and subtitle
- **Add Task Form** - Input fields for new tasks
- **Task List** - Container for dynamically rendered tasks
- **Empty State** - Shown when no tasks exist
- **Edit Modal** - Dialog for editing existing tasks
- **Footer** - CRUD operations description

### style.css

| Section | Purpose |
|---------|---------|
| CSS Variables | Color palette, spacing, typography |
| Base Styles | Reset, body, fonts |
| Layout | App container, header, main, footer |
| Form Styles | Input fields, buttons, selects |
| Task List | Task items, checkboxes, actions |
| Modal | Edit dialog styling |
| Animations | Transitions, hover effects |
| Responsive | Mobile breakpoints |

### app.js

| Function | Purpose |
|----------|---------|
| `fetchTasks()` | GET all tasks from API |
| `createTask(data)` | POST new task to API |
| `updateTask(id, data)` | PUT updated task to API |
| `deleteTask(id)` | DELETE task from API |
| `renderTasks(tasks)` | Update DOM with task list |
| `createTaskElement(task)` | Generate HTML for single task |
| `toggleComplete(id, status)` | Toggle completion status |
| `openEditModal(id)` | Show edit dialog with task data |
| `closeModal()` | Hide edit dialog |

---

## Database Integration

### How the Backend Works

1. **Flask Server** (`webapp.py`) serves the static files and API endpoints
2. **Custom RDBMS** stores tasks in an in-memory table with B-tree indexing
3. **JSON Persistence** - Database saved to `database.json` on every write
4. **Auto-Increment** - Task IDs managed by the application layer

### RDBMS Features Used

| Feature | Usage |
|---------|-------|
| PRIMARY KEY | Task `id` column for unique identification |
| NOT NULL | Task `title` must be provided |
| B-tree Index | Fast lookups when fetching single tasks |
| INSERT | Creating new tasks |
| SELECT (scan) | Listing all tasks |
| UPDATE | Modifying task properties |
| DELETE | Removing tasks |

---

## Styling Guide

### Color Palette

```css
:root {
    --primary: #6366f1;      /* Indigo - buttons, accents */
    --primary-hover: #4f46e5;
    --danger: #ef4444;       /* Red - delete actions */
    --success: #22c55e;      /* Green - completion */
    --bg-primary: #f8fafc;   /* Light gray background */
    --text-primary: #1e293b; /* Dark text */
    --text-secondary: #64748b;
}
```

### Priority Badges

| Priority | Color |
|----------|-------|
| Low | Green (`#22c55e`) |
| Medium | Yellow (`#eab308`) |
| High | Red (`#ef4444`) |

---

## Browser Compatibility

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Uses modern features:
- CSS Custom Properties
- Flexbox Layout
- Fetch API
- ES6+ JavaScript

---

## Customization

### Adding New Task Fields

1. Update `tasks` table schema in `webapp.py`
2. Add form field in `index.html`
3. Include field in API calls in `app.js`
4. Style the new field in `style.css`

### Changing Styles

All colors and spacing are defined as CSS custom properties in `style.css`:

```css
:root {
    --primary: #your-color;
    --spacing-md: 1rem;
    /* etc. */
}
```

---

## Known Limitations

- No user authentication (single-user demo)
- No sorting/filtering UI (backend supports it)
- No pagination (loads all tasks at once)
- No offline support
- No drag-and-drop reordering

These are intentional simplifications for a demo application focused on showcasing RDBMS CRUD operations.

---

## Credits

Part of the **Simple RDBMS** project for the Pesapal Junior Developer 2026 Challenge.

- **Backend**: Custom RDBMS with B-tree indexing
- **Framework**: Flask (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Font**: Inter (Google Fonts)
