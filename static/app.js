/**
 * Task Manager App - JavaScript
 * Handles all CRUD operations via REST API
 */

const API_BASE = '/api/tasks';

// DOM Elements
const taskForm = document.getElementById('task-form');
const taskList = document.getElementById('task-list');
const emptyState = document.getElementById('empty-state');
const taskCount = document.getElementById('task-count');
const editModal = document.getElementById('edit-modal');
const editForm = document.getElementById('edit-form');

// ============================================================
// API Functions
// ============================================================

async function fetchTasks() {
    try {
        const response = await fetch(API_BASE);
        const tasks = await response.json();
        renderTasks(tasks);
    } catch (error) {
        console.error('Failed to fetch tasks:', error);
    }
}

async function createTask(taskData) {
    try {
        const response = await fetch(API_BASE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error);
        }
        
        await fetchTasks();
        return true;
    } catch (error) {
        console.error('Failed to create task:', error);
        alert('Failed to create task: ' + error.message);
        return false;
    }
}

async function updateTask(taskId, updates) {
    try {
        const response = await fetch(`${API_BASE}/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error);
        }
        
        await fetchTasks();
        return true;
    } catch (error) {
        console.error('Failed to update task:', error);
        alert('Failed to update task: ' + error.message);
        return false;
    }
}

async function deleteTask(taskId) {
    try {
        const response = await fetch(`${API_BASE}/${taskId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error);
        }
        
        await fetchTasks();
        return true;
    } catch (error) {
        console.error('Failed to delete task:', error);
        alert('Failed to delete task: ' + error.message);
        return false;
    }
}

// ============================================================
// Render Functions
// ============================================================

function renderTasks(tasks) {
    taskList.innerHTML = '';
    
    if (tasks.length === 0) {
        emptyState.classList.add('visible');
        taskCount.textContent = '0 tasks';
        return;
    }
    
    emptyState.classList.remove('visible');
    taskCount.textContent = `${tasks.length} task${tasks.length !== 1 ? 's' : ''}`;
    
    tasks.forEach(task => {
        const taskElement = createTaskElement(task);
        taskList.appendChild(taskElement);
    });
}

function createTaskElement(task) {
    const div = document.createElement('div');
    div.className = `task-item ${task.completed ? 'completed' : ''}`;
    div.dataset.id = task.id;
    
    div.innerHTML = `
        <div class="task-checkbox">
            <input type="checkbox" id="check-${task.id}" ${task.completed ? 'checked' : ''}>
            <label for="check-${task.id}"></label>
        </div>
        <div class="task-content">
            <div class="task-title">${escapeHtml(task.title)}</div>
            ${task.description ? `<div class="task-description">${escapeHtml(task.description)}</div>` : ''}
            <div class="task-meta">
                <span class="priority-badge priority-${task.priority}">${task.priority}</span>
            </div>
        </div>
        <div class="task-actions">
            <button class="btn-icon edit" title="Edit" onclick="openEditModal(${task.id})">
                ✏️
            </button>
            <button class="btn-icon delete" title="Delete" onclick="confirmDelete(${task.id})">
                🗑️
            </button>
        </div>
    `;
    
    // Add checkbox event listener
    const checkbox = div.querySelector(`#check-${task.id}`);
    checkbox.addEventListener('change', () => toggleComplete(task.id, checkbox.checked));
    
    return div;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
// Event Handlers
// ============================================================

// Create task form submission
taskForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const title = document.getElementById('task-title').value.trim();
    const description = document.getElementById('task-description').value.trim();
    const priority = document.getElementById('task-priority').value;
    
    if (!title) return;
    
    const success = await createTask({ title, description, priority });
    
    if (success) {
        taskForm.reset();
        document.getElementById('task-priority').value = 'medium';
    }
});

// Toggle task completion
async function toggleComplete(taskId, completed) {
    await updateTask(taskId, { completed });
}

// Delete task with confirmation
function confirmDelete(taskId) {
    if (confirm('Are you sure you want to delete this task?')) {
        deleteTask(taskId);
    }
}

// ============================================================
// Edit Modal
// ============================================================

async function openEditModal(taskId) {
    try {
        const response = await fetch(`${API_BASE}/${taskId}`);
        const task = await response.json();
        
        document.getElementById('edit-id').value = task.id;
        document.getElementById('edit-title').value = task.title;
        document.getElementById('edit-description').value = task.description || '';
        document.getElementById('edit-priority').value = task.priority;
        
        editModal.classList.add('active');
    } catch (error) {
        console.error('Failed to load task:', error);
    }
}

function closeModal() {
    editModal.classList.remove('active');
}

// Close modal on backdrop click
editModal.addEventListener('click', (e) => {
    if (e.target === editModal) {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && editModal.classList.contains('active')) {
        closeModal();
    }
});

// Edit form submission
editForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const taskId = document.getElementById('edit-id').value;
    const title = document.getElementById('edit-title').value.trim();
    const description = document.getElementById('edit-description').value.trim();
    const priority = document.getElementById('edit-priority').value;
    
    if (!title) return;
    
    const success = await updateTask(taskId, { title, description, priority });
    
    if (success) {
        closeModal();
    }
});

// ============================================================
// Initial Load
// ============================================================

fetchTasks();
