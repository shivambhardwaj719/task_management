// Race AI Task Manager - Frontend Client

let currentUser = null;
let userProjects = [];
let allUsers = [];
let activeProjectId = 'all';
let isOverdueFilterActive = false;
let authModalMode = 'login';
let toastTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    initApp();
    setupEventListeners();
});

// Helper for CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// API Helper
async function apiFetch(url, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken') || ''
    };

    const config = { method, headers };
    if (body) {
        config.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(url, config);
        const data = await response.json().catch(() => ({}));
        return { ok: response.ok, status: response.status, data };
    } catch (err) {
        console.error("API Fetch Error:", err);
        return { ok: false, status: 500, data: { message: "Network or connection error" } };
    }
}

// Extract Error Message from Backend API Response
function extractErrorMessage(res) {
    if (!res) return "An unexpected error occurred.";
    if (res.data) {
        if (typeof res.data.message === 'string' && res.data.message) {
            return res.data.message;
        }
        if (typeof res.data.errors === 'string' && res.data.errors) {
            return res.data.errors;
        }
        if (typeof res.data.detail === 'string' && res.data.detail) {
            return res.data.detail;
        }
    }
    return `Server Error (${res.status || 500})`;
}

// Top Floating Toast Notification
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    const toastText = document.getElementById('toast-text');
    const toastIcon = document.getElementById('toast-icon');

    if (!toast || !toastText) return;

    toastText.textContent = message || (isError ? "An error occurred" : "Operation successful");
    toastIcon.textContent = isError ? "❌" : "✅";
    
    toast.style.borderColor = isError ? "rgba(239, 68, 68, 0.6)" : "rgba(16, 185, 129, 0.6)";
    toast.style.boxShadow = isError 
        ? "0 12px 40px rgba(239, 68, 68, 0.3)" 
        : "0 12px 40px rgba(16, 185, 129, 0.3)";

    toast.classList.remove('hidden');

    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.add('hidden');
    }, 4000);
}

// Custom Modal Confirmation Dialog
function showConfirm(title, message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    const titleEl = document.getElementById('confirm-modal-title');
    const msgEl = document.getElementById('confirm-modal-msg');
    const cancelBtn = document.getElementById('confirm-modal-cancel');
    const okBtn = document.getElementById('confirm-modal-ok');

    titleEl.textContent = title;
    msgEl.textContent = message;

    modal.classList.remove('hidden');

    const handleCancel = () => {
        modal.classList.add('hidden');
        cleanup();
    };

    const handleOk = () => {
        modal.classList.add('hidden');
        cleanup();
        onConfirm();
    };

    function cleanup() {
        cancelBtn.removeEventListener('click', handleCancel);
        okBtn.removeEventListener('click', handleOk);
    }

    cancelBtn.addEventListener('click', handleCancel);
    okBtn.addEventListener('click', handleOk);
}

// App Initialization
async function initApp() {
    const res = await apiFetch('/api/auth/me/');
    if (res.ok && res.data.success) {
        currentUser = res.data.data;
        renderAuthUI(true);
        await loadProjects();
        await loadUsers();
        await loadWorkspaceData();
    } else {
        currentUser = null;
        renderAuthUI(false);
    }
}

function renderAuthUI(isLoggedIn) {
    const userSection = document.getElementById('user-info-section');
    const authBtns = document.getElementById('auth-buttons-section');
    const unauthView = document.getElementById('unauth-view');
    const authWorkspace = document.getElementById('auth-workspace');

    if (isLoggedIn && currentUser) {
        userSection.classList.remove('hidden');
        authBtns.classList.add('hidden');
        unauthView.classList.add('hidden');
        authWorkspace.classList.remove('hidden');

        document.getElementById('username-display').textContent = currentUser.username;
        document.getElementById('user-avatar').textContent = currentUser.username.charAt(0).toUpperCase();
    } else {
        userSection.classList.add('hidden');
        authBtns.classList.remove('hidden');
        unauthView.classList.remove('hidden');
        authWorkspace.classList.add('hidden');
    }
}

// Data Loaders
async function loadProjects() {
    const res = await apiFetch('/api/projects/');
    if (res.ok && res.data.success) {
        userProjects = res.data.data;
        populateProjectDropdown();
    } else {
        showToast(extractErrorMessage(res), true);
    }
}

async function loadUsers() {
    const res = await apiFetch('/api/users/');
    if (res.ok && res.data.success) {
        allUsers = res.data.data;
        populateAssigneeDropdown();
    }
}

function populateProjectDropdown() {
    const select = document.getElementById('project-select');
    const taskProjSelect = document.getElementById('task-project-select');

    select.innerHTML = '<option value="all">⚡ My Assigned Tasks (Dashboard)</option>';
    taskProjSelect.innerHTML = '';

    userProjects.forEach(p => {
        const option = document.createElement('option');
        option.value = p.id;
        option.textContent = p.name + (p.is_owner ? ' (Owner)' : '');
        select.appendChild(option);

        const taskOpt = document.createElement('option');
        taskOpt.value = p.id;
        taskOpt.textContent = p.name;
        taskProjSelect.appendChild(taskOpt);
    });

    select.value = activeProjectId;
}

function populateAssigneeDropdown() {
    const select = document.getElementById('task-assignee-select');
    select.innerHTML = '<option value="">Unassigned</option>';

    allUsers.forEach(u => {
        const option = document.createElement('option');
        option.value = u.id;
        option.textContent = u.username + (u.first_name ? ` (${u.first_name})` : '');
        select.appendChild(option);
    });
}

// Workspace Loader (Dashboard vs Project Tasks vs Overdue)
async function loadWorkspaceData() {
    const editBtn = document.getElementById('btn-edit-project');
    const deleteBtn = document.getElementById('btn-delete-project');
    const metricsBar = document.getElementById('project-metrics-bar');

    if (isOverdueFilterActive) {
        await loadOverdueTasks();
        metricsBar.classList.add('hidden');
        editBtn.classList.add('hidden');
        deleteBtn.classList.add('hidden');
        return;
    }

    if (activeProjectId === 'all') {
        // Load Dashboard API
        editBtn.classList.add('hidden');
        deleteBtn.classList.add('hidden');
        metricsBar.classList.add('hidden');

        const res = await apiFetch('/api/dashboard/');
        if (res.ok && res.data.success) {
            const data = res.data.data;
            document.getElementById('overdue-badge-count').textContent = data.summary.overdue_count;
            renderKanbanColumns(data.columns);
        } else {
            showToast(extractErrorMessage(res), true);
        }
    } else {
        // Load Specific Project Tasks and Metrics
        const currentProject = userProjects.find(p => p.id == activeProjectId);
        if (currentProject && currentProject.is_owner) {
            editBtn.classList.remove('hidden');
            deleteBtn.classList.remove('hidden');
        } else {
            editBtn.classList.add('hidden');
            deleteBtn.classList.add('hidden');
        }

        // Fetch per-project status counts
        const countRes = await apiFetch(`/api/projects/${activeProjectId}/status-counts/`);
        if (countRes.ok && countRes.data.success) {
            const counts = countRes.data.data.counts;
            document.getElementById('metric-total').textContent = counts.TOTAL;
            document.getElementById('metric-todo').textContent = counts.TODO;
            document.getElementById('metric-inprogress').textContent = counts.IN_PROGRESS;
            document.getElementById('metric-done').textContent = counts.DONE;
            metricsBar.classList.remove('hidden');
        }

        // Fetch Tasks for Project
        const res = await apiFetch(`/api/tasks/?project_id=${activeProjectId}`);
        if (res.ok && res.data.success) {
            const tasks = res.data.data;
            const grouped = {
                TODO: { label: "To Do", tasks: tasks.filter(t => t.status === 'TODO') },
                IN_PROGRESS: { label: "In Progress", tasks: tasks.filter(t => t.status === 'IN_PROGRESS') },
                DONE: { label: "Done", tasks: tasks.filter(t => t.status === 'DONE') }
            };
            renderKanbanColumns(grouped);
        } else {
            showToast(extractErrorMessage(res), true);
        }
    }
}

async function loadOverdueTasks() {
    const res = await apiFetch('/api/tasks/overdue/');
    if (res.ok && res.data.success) {
        const tasks = res.data.data;
        document.getElementById('overdue-badge-count').textContent = tasks.length;
        const grouped = {
            TODO: { label: "To Do", tasks: tasks.filter(t => t.status === 'TODO') },
            IN_PROGRESS: { label: "In Progress", tasks: tasks.filter(t => t.status === 'IN_PROGRESS') },
            DONE: { label: "Done", tasks: tasks.filter(t => t.status === 'DONE') }
        };
        renderKanbanColumns(grouped);
    } else {
        showToast(extractErrorMessage(res), true);
    }
}

// Render Kanban Column Cards
function renderKanbanColumns(columnsData) {
    ['TODO', 'IN_PROGRESS', 'DONE'].forEach(status => {
        const colKey = status.toLowerCase().replace('_', '');
        const listEl = document.getElementById(`list-${colKey}`);
        const countEl = document.getElementById(`count-${colKey}`);

        listEl.innerHTML = '';
        const column = columnsData[status];
        const tasks = column ? column.tasks : [];

        countEl.textContent = tasks.length;

        if (tasks.length === 0) {
            listEl.innerHTML = `<div class="empty-column-msg" style="color:var(--text-muted); text-align:center; padding: 20px;">No tasks</div>`;
            return;
        }

        tasks.forEach(task => {
            const card = document.createElement('div');
            card.className = 'task-card';
            card.onclick = () => openCommentsDrawer(task);

            const isOwner = currentUser && task.project_owner_id === currentUser.id;

            card.innerHTML = `
                <div class="task-card-header">
                    <span class="task-title">${escapeHtml(task.title)}</span>
                    <div class="task-badges">
                        <span class="badge badge-priority-${task.priority}">${task.priority_display}</span>
                        ${task.is_overdue ? '<span class="badge badge-overdue">OVERDUE</span>' : ''}
                    </div>
                </div>
                <div class="task-card-meta">
                    <span>📁 ${escapeHtml(task.project_name)}</span>
                    <span>👤 ${escapeHtml(task.assigned_to_username)}</span>
                    <span>📅 ${task.due_date}</span>
                </div>
                ${isOwner ? `
                <div class="task-card-actions" onclick="event.stopPropagation()">
                    <select onchange="updateTaskStatus(${task.id}, this.value)" class="form-control" style="width: auto; padding: 4px 8px; font-size: 11px;">
                        <option value="TODO" ${task.status === 'TODO' ? 'selected' : ''}>To Do</option>
                        <option value="IN_PROGRESS" ${task.status === 'IN_PROGRESS' ? 'selected' : ''}>In Progress</option>
                        <option value="DONE" ${task.status === 'DONE' ? 'selected' : ''}>Done</option>
                    </select>
                    <button class="btn btn-sm btn-ghost" onclick="openEditTaskModal(${JSON.stringify(task).replace(/"/g, '&quot;')})">✏️</button>
                    <button class="btn btn-sm btn-danger-ghost" onclick="deleteTask(${task.id})">🗑️</button>
                </div>
                ` : ''}
            `;
            listEl.appendChild(card);
        });
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Actions & Event Setup
function setupEventListeners() {
    // Auth Modal Triggers
    document.getElementById('btn-show-login').onclick = () => openAuthModal('login');
    document.getElementById('btn-show-register').onclick = () => openAuthModal('register');
    document.getElementById('btn-logout').onclick = handleLogout;

    // Auth Form
    document.getElementById('auth-form').onsubmit = handleAuthSubmit;

    // Project Dropdown & Actions
    document.getElementById('project-select').onchange = (e) => {
        activeProjectId = e.target.value;
        isOverdueFilterActive = false;
        document.getElementById('btn-toggle-overdue').classList.remove('btn-warning');
        loadWorkspaceData();
    };

    document.getElementById('btn-new-project').onclick = () => openProjectModal();
    document.getElementById('btn-edit-project').onclick = () => openProjectModal(true);
    document.getElementById('btn-delete-project').onclick = handleDeleteProject;
    document.getElementById('project-form').onsubmit = handleProjectSubmit;

    // Task Actions
    document.getElementById('btn-new-task').onclick = () => openTaskModal();
    document.getElementById('task-form').onsubmit = handleTaskSubmit;

    // Overdue Filter Toggle
    document.getElementById('btn-toggle-overdue').onclick = () => {
        isOverdueFilterActive = !isOverdueFilterActive;
        const btn = document.getElementById('btn-toggle-overdue');
        if (isOverdueFilterActive) {
            btn.style.background = '#f59e0b';
            btn.style.color = '#fff';
        } else {
            btn.style.background = '';
            btn.style.color = '';
        }
        loadWorkspaceData();
    };

    // Comment Form
    document.getElementById('comment-form').onsubmit = handleCommentSubmit;
}

// Auth Handlers
function openAuthModal(mode) {
    authModalMode = mode;
    document.getElementById('auth-modal-title').textContent = mode === 'login' ? 'Log In' : 'Register Account';
    document.getElementById('auth-submit-btn').textContent = mode === 'login' ? 'Log In' : 'Register';

    const extraFields = document.getElementById('register-extra-fields');
    if (mode === 'register') {
        extraFields.classList.remove('hidden');
    } else {
        extraFields.classList.add('hidden');
    }

    document.getElementById('auth-error').classList.add('hidden');
    document.getElementById('auth-modal').classList.remove('hidden');
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    const username = document.getElementById('auth-username').value;
    const password = document.getElementById('auth-password').value;
    const email = document.getElementById('auth-email').value;

    const url = authModalMode === 'login' ? '/api/auth/login/' : '/api/auth/register/';
    const body = authModalMode === 'login' ? { username, password } : { username, password, email };

    const res = await apiFetch(url, 'POST', body);
    if (res.ok && res.data.success) {
        closeModal('auth-modal');
        showToast(res.data.message || "Authenticated successfully");
        await initApp();
    } else {
        const errorMsg = extractErrorMessage(res);
        const errorDiv = document.getElementById('auth-error');
        errorDiv.textContent = errorMsg;
        errorDiv.classList.remove('hidden');
        showToast(errorMsg, true);
    }
}

async function handleLogout() {
    const res = await apiFetch('/api/auth/logout/', 'POST');
    if (res.ok && res.data.success) {
        showToast("Logged out successfully");
        currentUser = null;
        renderAuthUI(false);
    } else {
        showToast(extractErrorMessage(res), true);
    }
}

// Project Modal Handlers
function openProjectModal(isEdit = false) {
    const title = document.getElementById('project-modal-title');
    const idInput = document.getElementById('project-id-input');
    const nameInput = document.getElementById('project-name-input');
    const descInput = document.getElementById('project-desc-input');

    if (isEdit && activeProjectId !== 'all') {
        const project = userProjects.find(p => p.id == activeProjectId);
        if (project) {
            title.textContent = 'Edit Project';
            idInput.value = project.id;
            nameInput.value = project.name;
            descInput.value = project.description || '';
        }
    } else {
        title.textContent = 'New Project';
        idInput.value = '';
        nameInput.value = '';
        descInput.value = '';
    }

    document.getElementById('project-error').classList.add('hidden');
    document.getElementById('project-modal').classList.remove('hidden');
}

async function handleProjectSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('project-id-input').value;
    const name = document.getElementById('project-name-input').value;
    const description = document.getElementById('project-desc-input').value;

    const url = id ? `/api/projects/${id}/` : '/api/projects/';
    const method = id ? 'PUT' : 'POST';

    const res = await apiFetch(url, method, { name, description });
    if (res.ok && res.data.success) {
        closeModal('project-modal');
        showToast(res.data.message || "Project saved successfully");
        await loadProjects();
        if (!id && res.data.data) {
            activeProjectId = res.data.data.id;
        }
        document.getElementById('project-select').value = activeProjectId;
        await loadWorkspaceData();
    } else {
        const errorMsg = extractErrorMessage(res);
        const err = document.getElementById('project-error');
        err.textContent = errorMsg;
        err.classList.remove('hidden');
        showToast(errorMsg, true);
    }
}

function handleDeleteProject() {
    if (activeProjectId === 'all') return;
    
    showConfirm(
        "Delete Project", 
        "Are you sure you want to delete this project and all of its tasks? This action cannot be undone.",
        async () => {
            const res = await apiFetch(`/api/projects/${activeProjectId}/`, 'DELETE');
            if (res.ok && res.data.success) {
                showToast(res.data.message || "Project deleted successfully");
                activeProjectId = 'all';
                await loadProjects();
                await loadWorkspaceData();
            } else {
                showToast(extractErrorMessage(res), true);
            }
        }
    );
}

// Task Handlers
function openTaskModal() {
    document.getElementById('task-modal-title').textContent = 'Create Task';
    document.getElementById('task-id-input').value = '';
    document.getElementById('task-title-input').value = '';
    document.getElementById('task-status-select').value = 'TODO';
    document.getElementById('task-priority-select').value = 'MEDIUM';

    const today = new Date().toISOString().split('T')[0];
    document.getElementById('task-duedate-input').value = today;

    if (activeProjectId !== 'all') {
        document.getElementById('task-project-select').value = activeProjectId;
    }

    document.getElementById('task-error').classList.add('hidden');
    document.getElementById('task-modal').classList.remove('hidden');
}

function openEditTaskModal(task) {
    document.getElementById('task-modal-title').textContent = 'Edit Task';
    document.getElementById('task-id-input').value = task.id;
    document.getElementById('task-project-select').value = task.project_id;
    document.getElementById('task-title-input').value = task.title;
    document.getElementById('task-status-select').value = task.status;
    document.getElementById('task-priority-select').value = task.priority;
    document.getElementById('task-duedate-input').value = task.due_date;
    document.getElementById('task-assignee-select').value = task.assigned_to_id || '';

    document.getElementById('task-error').classList.add('hidden');
    document.getElementById('task-modal').classList.remove('hidden');
}

async function handleTaskSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('task-id-input').value;
    const project_id = document.getElementById('task-project-select').value;
    const title = document.getElementById('task-title-input').value;
    const status = document.getElementById('task-status-select').value;
    const priority = document.getElementById('task-priority-select').value;
    const due_date = document.getElementById('task-duedate-input').value;
    const assigned_to_id = document.getElementById('task-assignee-select').value;

    const url = id ? `/api/tasks/${id}/` : '/api/tasks/';
    const method = id ? 'PUT' : 'POST';

    const body = { project_id, title, status, priority, due_date, assigned_to_id };

    const res = await apiFetch(url, method, body);
    if (res.ok && res.data.success) {
        closeModal('task-modal');
        showToast(res.data.message || "Task saved successfully");
        await loadWorkspaceData();
    } else {
        const errorMsg = extractErrorMessage(res);
        const err = document.getElementById('task-error');
        err.textContent = errorMsg;
        err.classList.remove('hidden');
        showToast(errorMsg, true);
    }
}

async function updateTaskStatus(taskId, newStatus) {
    const res = await apiFetch(`/api/tasks/${taskId}/`, 'PUT', { status: newStatus });
    if (res.ok && res.data.success) {
        showToast("Task status updated");
        await loadWorkspaceData();
    } else {
        showToast(extractErrorMessage(res), true);
    }
}

function deleteTask(taskId) {
    showConfirm(
        "Delete Task",
        "Are you sure you want to delete this task?",
        async () => {
            const res = await apiFetch(`/api/tasks/${taskId}/`, 'DELETE');
            if (res.ok && res.data.success) {
                showToast(res.data.message || "Task deleted successfully");
                await loadWorkspaceData();
            } else {
                showToast(extractErrorMessage(res), true);
            }
        }
    );
}

// Comments Drawer
async function openCommentsDrawer(task) {
    document.getElementById('comment-task-title').textContent = task.title;
    document.getElementById('comment-task-status').textContent = task.status_display;
    document.getElementById('comment-task-project').textContent = task.project_name;
    document.getElementById('comment-task-assignee').textContent = task.assigned_to_username;
    document.getElementById('comment-task-duedate').textContent = task.due_date;
    document.getElementById('comment-task-id').value = task.id;

    await loadTaskComments(task.id);
    document.getElementById('comments-drawer').classList.remove('hidden');
}

async function loadTaskComments(taskId) {
    const listEl = document.getElementById('comments-list');
    listEl.innerHTML = '<div style="color:var(--text-muted); text-align:center;">Loading comments...</div>';

    const res = await apiFetch(`/api/tasks/${taskId}/comments/`);
    if (res.ok && res.data.success) {
        const comments = res.data.data;
        if (comments.length === 0) {
            listEl.innerHTML = '<div style="color:var(--text-muted); text-align:center; padding:12px;">No comments yet. Be the first to comment!</div>';
            return;
        }

        listEl.innerHTML = '';
        comments.forEach(c => {
            const card = document.createElement('div');
            card.className = 'comment-card';
            const dateStr = new Date(c.created_at).toLocaleString();
            card.innerHTML = `
                <div class="comment-header">
                    <span class="comment-author">${escapeHtml(c.author_username)}</span>
                    <span>${dateStr}</span>
                </div>
                <div class="comment-body">${escapeHtml(c.body)}</div>
            `;
            listEl.appendChild(card);
        });
    } else {
        showToast(extractErrorMessage(res), true);
    }
}

async function handleCommentSubmit(e) {
    e.preventDefault();
    const taskId = document.getElementById('comment-task-id').value;
    const bodyInput = document.getElementById('comment-body-input');
    const body = bodyInput.value;

    if (!body || !body.trim()) return;

    const res = await apiFetch(`/api/tasks/${taskId}/comments/`, 'POST', { body });
    if (res.ok && res.data.success) {
        bodyInput.value = '';
        showToast("Comment posted");
        await loadTaskComments(taskId);
    } else {
        showToast(extractErrorMessage(res), true);
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}
