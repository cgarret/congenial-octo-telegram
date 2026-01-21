// Task Manager Application
class TaskManager {
    constructor() {
        this.tasks = this.loadTasks();
        this.currentFilter = 'all';
        this.initializeElements();
        this.attachEventListeners();
        this.render();
    }

    // Initialize DOM elements
    initializeElements() {
        this.taskForm = document.getElementById('task-form');
        this.taskInput = document.getElementById('task-input');
        this.taskList = document.getElementById('task-list');
        this.emptyState = document.getElementById('empty-state');
        this.clearCompletedBtn = document.getElementById('clear-completed');
        this.filterButtons = document.querySelectorAll('.filter-btn');
        
        // Statistics elements
        this.totalTasksEl = document.getElementById('total-tasks');
        this.activeTasksEl = document.getElementById('active-tasks');
        this.completedTasksEl = document.getElementById('completed-tasks');
    }

    // Attach event listeners
    attachEventListeners() {
        // Form submission
        this.taskForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addTask();
        });

        // Clear completed tasks
        this.clearCompletedBtn.addEventListener('click', () => {
            this.clearCompleted();
        });

        // Filter buttons
        this.filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setFilter(e.target.dataset.filter);
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K to focus input
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.taskInput.focus();
            }
        });
    }

    // Generate unique ID
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    // Format timestamp
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffInMinutes = Math.floor((now - date) / (1000 * 60));
        
        if (diffInMinutes < 1) return 'Just now';
        if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
        
        const diffInHours = Math.floor(diffInMinutes / 60);
        if (diffInHours < 24) return `${diffInHours}h ago`;
        
        const diffInDays = Math.floor(diffInHours / 24);
        if (diffInDays < 7) return `${diffInDays}d ago`;
        
        return date.toLocaleDateString();
    }

    // Add new task
    addTask() {
        const text = this.taskInput.value.trim();
        
        if (!text) {
            this.taskInput.focus();
            return;
        }

        const task = {
            id: this.generateId(),
            text: text,
            completed: false,
            createdAt: Date.now()
        };

        this.tasks.unshift(task);
        this.saveTasks();
        this.taskInput.value = '';
        this.taskInput.focus();
        this.render();
        this.announceToScreenReader(`Task "${text}" added`);
    }

    // Toggle task completion
    toggleTask(id) {
        const task = this.tasks.find(t => t.id === id);
        if (task) {
            task.completed = !task.completed;
            task.completedAt = task.completed ? Date.now() : null;
            this.saveTasks();
            this.render();
            this.announceToScreenReader(
                `Task marked as ${task.completed ? 'completed' : 'active'}`
            );
        }
    }

    // Delete task
    deleteTask(id) {
        const task = this.tasks.find(t => t.id === id);
        if (task && confirm(`Delete task: "${task.text}"?`)) {
            this.tasks = this.tasks.filter(t => t.id !== id);
            this.saveTasks();
            this.render();
            this.announceToScreenReader(`Task "${task.text}" deleted`);
        }
    }

    // Clear completed tasks
    clearCompleted() {
        const completedCount = this.tasks.filter(t => t.completed).length;
        
        if (completedCount === 0) {
            return;
        }

        if (confirm(`Delete ${completedCount} completed task${completedCount !== 1 ? 's' : ''}?`)) {
            this.tasks = this.tasks.filter(t => !t.completed);
            this.saveTasks();
            this.render();
            this.announceToScreenReader(`${completedCount} completed tasks cleared`);
        }
    }

    // Set filter
    setFilter(filter) {
        this.currentFilter = filter;
        
        // Update active button
        this.filterButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        this.render();
        this.announceToScreenReader(`Showing ${filter} tasks`);
    }

    // Get filtered tasks
    getFilteredTasks() {
        switch (this.currentFilter) {
            case 'active':
                return this.tasks.filter(t => !t.completed);
            case 'completed':
                return this.tasks.filter(t => t.completed);
            default:
                return this.tasks;
        }
    }

    // Update statistics
    updateStatistics() {
        const total = this.tasks.length;
        const completed = this.tasks.filter(t => t.completed).length;
        const active = total - completed;

        this.totalTasksEl.textContent = total;
        this.activeTasksEl.textContent = active;
        this.completedTasksEl.textContent = completed;

        // Disable clear completed button if no completed tasks
        this.clearCompletedBtn.disabled = completed === 0;
    }

    // Create task element
    createTaskElement(task) {
        const li = document.createElement('li');
        li.className = `task-item ${task.completed ? 'completed' : ''}`;
        li.setAttribute('role', 'listitem');
        
        // Checkbox
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'task-checkbox';
        checkbox.checked = task.completed;
        checkbox.setAttribute('aria-label', `Mark task "${task.text}" as ${task.completed ? 'active' : 'completed'}`);
        checkbox.addEventListener('change', () => this.toggleTask(task.id));
        
        // Task text
        const taskText = document.createElement('span');
        taskText.className = 'task-text';
        taskText.textContent = task.text;
        
        // Timestamp
        const timestamp = document.createElement('span');
        timestamp.className = 'task-timestamp';
        timestamp.textContent = this.formatTimestamp(task.createdAt);
        timestamp.setAttribute('aria-label', `Created ${timestamp.textContent}`);
        
        // Delete button
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.innerHTML = '&times;';
        deleteBtn.setAttribute('aria-label', `Delete task "${task.text}"`);
        deleteBtn.addEventListener('click', () => this.deleteTask(task.id));
        
        li.appendChild(checkbox);
        li.appendChild(taskText);
        li.appendChild(timestamp);
        li.appendChild(deleteBtn);
        
        return li;
    }

    // Render task list
    render() {
        const filteredTasks = this.getFilteredTasks();
        
        // Clear existing tasks
        this.taskList.innerHTML = '';
        
        // Show/hide empty state
        if (filteredTasks.length === 0) {
            this.emptyState.classList.add('show');
            this.taskList.setAttribute('aria-label', 'No tasks to display');
        } else {
            this.emptyState.classList.remove('show');
            this.taskList.setAttribute('aria-label', `${filteredTasks.length} tasks`);
            
            // Create and append task elements
            filteredTasks.forEach(task => {
                const taskElement = this.createTaskElement(task);
                this.taskList.appendChild(taskElement);
            });
        }
        
        // Update statistics
        this.updateStatistics();
    }

    // Save tasks to localStorage
    saveTasks() {
        try {
            localStorage.setItem('taskManagerTasks', JSON.stringify(this.tasks));
        } catch (error) {
            console.error('Failed to save tasks:', error);
            this.announceToScreenReader('Failed to save tasks');
        }
    }

    // Load tasks from localStorage
    loadTasks() {
        try {
            const stored = localStorage.getItem('taskManagerTasks');
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('Failed to load tasks:', error);
            return [];
        }
    }

    // Announce to screen readers
    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', 'polite');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TaskManager();
});
