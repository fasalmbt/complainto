// Global variables
let currentUser = null;
let authToken = null;
let allUserComplaints = [];

// Utility functions
function showNotification(message, type = 'success') {
  const notification = document.createElement('div');
  notification.className = `notification is-${type} fade-in`;
  notification.innerHTML = `
    <button class="delete" onclick="this.parentElement.remove()"></button>
    ${message}
  `;
  
  const container = document.querySelector('.notifications-container') || document.body;
  container.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 1) {
    return 'Yesterday at ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  } else if (diffDays < 7) {
    return diffDays + ' days ago';
  } else {
    return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  }
}

function getStatusClass(status) {
  const statusClasses = {
    'pending': 'status-pending',
    'in_progress': 'status-in_progress',
    'resolved': 'status-resolved',
    'rejected': 'status-rejected'
  };
  return statusClasses[status] || 'status-pending';
}

function getStatusText(status) {
  const statusTexts = {
    'pending': 'Pending',
    'in_progress': 'In Progress',
    'resolved': 'Resolved',
    'rejected': 'Rejected'
  };
  return statusTexts[status] || 'Unknown';
}

function getCategoryIcon(category) {
  const categoryIcons = {
    'technical': 'fas fa-cog',
    'billing': 'fas fa-dollar-sign',
    'service': 'fas fa-handshake',
    'product': 'fas fa-box',
    'other': 'fas fa-question-circle'
  };
  return categoryIcons[category] || 'fas fa-clipboard';
}

function getCategoryIconClass(category) {
  return `category-icon-${category}`;
}

function getStatusIcon(status) {
  const statusIcons = {
    'pending': 'fas fa-clock',
    'in_progress': 'fas fa-spinner fa-spin',
    'resolved': 'fas fa-check-circle',
    'rejected': 'fas fa-times-circle'
  };
  return statusIcons[status] || 'fas fa-clock';
}

function getPriorityColor(status) {
  const colors = {
    'pending': '#f59e0b',
    'in_progress': '#3b82f6',
    'resolved': '#10b981',
    'rejected': '#ef4444'
  };
  return colors[status] || '#6b7280';
}

// Authentication functions
function saveAuthData(token, user) {
  authToken = token;
  currentUser = user;
  localStorage.setItem('authToken', token);
  localStorage.setItem('currentUser', JSON.stringify(user));
}

function loadAuthData() {
  authToken = localStorage.getItem('authToken');
  const userData = localStorage.getItem('currentUser');
  if (userData) {
    currentUser = JSON.parse(userData);
  }
}

function clearAuthData() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem('authToken');
  localStorage.removeItem('currentUser');
}

function isAuthenticated() {
  return authToken && currentUser;
}

function getAuthHeaders() {
  return {
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json'
  };
}

// API functions
async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(errorData.detail || 'An error occurred');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}

// Authentication handlers
async function handleLogin(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  
  try {
    const response = await apiCall('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: formData.get('email'),
        password: formData.get('password')
      })
    });
    
    saveAuthData(response.access_token, response.user);
    showNotification('Login successful!');
    
    // Redirect based on user role
    if (response.user.is_admin) {
      window.location.href = '/admin';
    } else {
      window.location.href = '/dashboard';
    }
  } catch (error) {
    showNotification(error.message, 'danger');
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  
  const password = formData.get('password');
  const confirmPassword = formData.get('confirmPassword');
  
  if (password !== confirmPassword) {
    showNotification('Passwords do not match', 'danger');
    return;
  }
  
  try {
    const response = await apiCall('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: formData.get('email'),
        name: formData.get('name'),
        password: password,
        is_admin: formData.get('is_admin') === 'on'
      })
    });
    
    saveAuthData(response.access_token, response.user);
    showNotification('Registration successful!');
    
    // Redirect based on user role
    if (response.user.is_admin) {
      window.location.href = '/admin';
    } else {
      window.location.href = '/dashboard';
    }
  } catch (error) {
    showNotification(error.message, 'danger');
  }
}

async function handleForgotPassword(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  
  try {
    const response = await apiCall('/api/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: formData.get('email')
      })
    });
    
    showNotification('If the email exists, a reset link has been sent to your email address.', 'info');
    form.reset();
  } catch (error) {
    showNotification(error.message, 'danger');
  }
}

async function handleResetPassword(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  
  const newPassword = formData.get('new_password');
  const confirmPassword = formData.get('confirm_password');
  
  if (newPassword !== confirmPassword) {
    showNotification('Passwords do not match', 'danger');
    return;
  }
  
  if (newPassword.length < 6) {
    showNotification('Password must be at least 6 characters long', 'danger');
    return;
  }
  
  try {
    const response = await apiCall('/api/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: formData.get('token'),
        new_password: newPassword
      })
    });
    
    showNotification('Password reset successfully! You can now login with your new password.', 'success');
    
    // Redirect to login page after 2 seconds
    setTimeout(() => {
      window.location.href = '/login';
    }, 2000);
  } catch (error) {
    showNotification(error.message, 'danger');
  }
}

function handleLogout() {
  clearAuthData();
  showNotification('Logged out successfully');
  window.location.href = '/';
}

// Complaint functions
async function handleComplaintSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  
  // Add loading state to submit button
  const submitButton = form.querySelector('button[type="submit"]');
  const originalText = submitButton.innerHTML;
  submitButton.innerHTML = '<span class="icon"><i class="fas fa-spinner fa-spin"></i></span><span>Submitting...</span>';
  submitButton.disabled = true;
  
  try {
    const response = await fetch('/api/complaints', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      body: formData
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to submit complaint');
    }
    
    const result = await response.json();
    showNotification('Complaint submitted successfully!');
    form.reset();
    
    // Reset file upload area
    const uploadArea = document.querySelector('.file-upload-area');
    if (uploadArea) {
      uploadArea.innerHTML = `
        <div class="has-text-centered">
          <i class="fas fa-cloud-upload-alt fa-2x mb-2"></i>
          <p><strong>Click to upload</strong> or drag and drop</p>
          <p class="has-text-grey">PNG, JPG up to 10MB</p>
        </div>
      `;
    }
    
    // Refresh complaints list if on dashboard
    if (typeof loadUserComplaints === 'function') {
      loadUserComplaints();
    }
  } catch (error) {
    showNotification(error.message, 'danger');
  } finally {
    // Reset button state
    submitButton.innerHTML = originalText;
    submitButton.disabled = false;
  }
}

async function loadUserComplaints() {
  try {
    const complaints = await apiCall('/api/complaints');
    allUserComplaints = complaints;
    displayUserComplaints(complaints);
    updateUserStats(complaints);
  } catch (error) {
    showNotification('Failed to load complaints', 'danger');
  }
}

async function loadAllComplaints() {
  try {
    const complaints = await apiCall('/api/admin/complaints');
    displayAdminComplaints(complaints);
  } catch (error) {
    showNotification('Failed to load complaints', 'danger');
  }
}

function updateUserStats(complaints) {
  const stats = {
    pending: 0,
    in_progress: 0,
    resolved: 0,
    rejected: 0
  };
  
  complaints.forEach(complaint => {
    if (stats.hasOwnProperty(complaint.status)) {
      stats[complaint.status]++;
    }
  });
  
  // Show stats cards if there are complaints
  const statsContainer = document.getElementById('userStatsCards');
  if (statsContainer && complaints.length > 0) {
    statsContainer.style.display = 'flex';
    
    document.getElementById('userPendingCount').textContent = stats.pending;
    document.getElementById('userInProgressCount').textContent = stats.in_progress;
    document.getElementById('userResolvedCount').textContent = stats.resolved;
    document.getElementById('userRejectedCount').textContent = stats.rejected;
  }
}

function filterComplaints() {
  const filterValue = document.getElementById('statusFilter').value;
  let filteredComplaints = allUserComplaints;
  
  if (filterValue) {
    filteredComplaints = allUserComplaints.filter(complaint => complaint.status === filterValue);
  }
  
  displayUserComplaints(filteredComplaints);
}

function displayUserComplaints(complaints) {
  const container = document.getElementById('complaintsContainer');
  if (!container) return;
  
  if (complaints.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <i class="fas fa-inbox"></i>
        </div>
        <h3 class="title is-4 has-text-grey">No complaints found</h3>
        <p class="subtitle has-text-grey">
          ${document.getElementById('statusFilter')?.value ? 
            'No complaints match the selected filter.' : 
            'Submit your first complaint using the form above.'}
        </p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = complaints.map(complaint => `
    <div class="card complaint-card card-hover fade-in mb-4">
      <div class="card-content">
        <div class="media">
          <div class="media-left">
            <figure class="image is-48x48">
              <div class="has-text-white is-flex is-align-items-center is-justify-content-center ${getCategoryIconClass(complaint.category)}" 
                   style="width: 48px; height: 48px; border-radius: 12px;">
                <i class="${getCategoryIcon(complaint.category)} fa-lg"></i>
              </div>
            </figure>
          </div>
          <div class="media-content">
            <div class="level">
              <div class="level-left">
                <div class="level-item">
                  <div>
                    <p class="title is-5 mb-2">${complaint.title}</p>
                    <p class="subtitle is-6 has-text-grey">
                      <i class="${getCategoryIcon(complaint.category)} mr-1"></i>
                      ${complaint.category.charAt(0).toUpperCase() + complaint.category.slice(1)}
                    </p>
                  </div>
                </div>
              </div>
              <div class="level-right">
                <div class="level-item">
                  <span class="tag status-badge ${getStatusClass(complaint.status)} is-medium">
                    <i class="${getStatusIcon(complaint.status)} mr-1"></i>
                    ${getStatusText(complaint.status)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="content">
          <p class="mb-3">${complaint.description}</p>
          
          ${complaint.screenshot_path ? `
            <div class="mb-3">
              <figure class="image is-inline-block">
                <img src="/${complaint.screenshot_path}" alt="Screenshot" class="screenshot-preview" 
                     onclick="openImageModal('/${complaint.screenshot_path}')">
              </figure>
            </div>
          ` : ''}
          
          ${complaint.admin_notes ? `
            <div class="notification is-info is-light">
              <div class="media">
                <div class="media-left">
                  <i class="fas fa-user-shield has-text-info fa-lg"></i>
                </div>
                <div class="media-content">
                  <strong class="has-text-info">Admin Response:</strong><br>
                  ${complaint.admin_notes}
                </div>
              </div>
            </div>
          ` : ''}
        </div>
        
        <div class="level is-mobile">
          <div class="level-left">
            <div class="level-item">
              <div class="tags has-addons">
                <span class="tag is-light">
                  <i class="fas fa-calendar-plus mr-1"></i>
                  Created
                </span>
                <span class="tag is-primary is-light">
                  ${formatDate(complaint.created_at)}
                </span>
              </div>
            </div>
          </div>
          <div class="level-right">
            <div class="level-item">
              <div class="tags has-addons">
                <span class="tag is-light">
                  <i class="fas fa-clock mr-1"></i>
                  Updated
                </span>
                <span class="tag is-info is-light">
                  ${formatDate(complaint.updated_at)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

function openImageModal(imageSrc) {
  const modal = document.createElement('div');
  modal.className = 'modal is-active';
  modal.innerHTML = `
    <div class="modal-background" onclick="this.parentElement.remove()"></div>
    <div class="modal-content">
      <p class="image">
        <img src="${imageSrc}" alt="Screenshot">
      </p>
    </div>
    <button class="modal-close is-large" onclick="this.parentElement.remove()"></button>
  `;
  document.body.appendChild(modal);
}

function displayAdminComplaints(complaints) {
  const container = document.getElementById('adminComplaintsContainer');
  if (!container) return;
  
  if (complaints.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">
          <i class="fas fa-clipboard-list"></i>
        </div>
        <h3 class="title is-4 has-text-grey">No complaints found</h3>
        <p class="subtitle has-text-grey">All complaints will appear here when submitted.</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = complaints.map(complaint => `
    <div class="card complaint-card card-hover fade-in mb-4">
      <div class="card-content">
        <div class="level">
          <div class="level-left">
            <div class="level-item">
              <div>
                <p class="title is-5">${complaint.title}</p>
                <p class="subtitle is-6">${complaint.category} • ${complaint.user_name} (${complaint.user_email})</p>
              </div>
            </div>
          </div>
          <div class="level-right">
            <div class="level-item">
              <span class="tag status-badge ${getStatusClass(complaint.status)}">
                ${getStatusText(complaint.status)}
              </span>
            </div>
          </div>
        </div>
        
        <div class="content">
          <p>${complaint.description}</p>
          
          ${complaint.screenshot_path ? `
            <div class="mt-3">
              <img src="/${complaint.screenshot_path}" alt="Screenshot" class="screenshot-preview" 
                   onclick="openImageModal('/${complaint.screenshot_path}')">
            </div>
          ` : ''}
        </div>
        
        <div class="field">
          <label class="label">Status</label>
          <div class="control">
            <div class="select is-fullwidth">
              <select onchange="updateComplaintStatus(${complaint.id}, this.value)">
                <option value="pending" ${complaint.status === 'pending' ? 'selected' : ''}>Pending</option>
                <option value="in_progress" ${complaint.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                <option value="resolved" ${complaint.status === 'resolved' ? 'selected' : ''}>Resolved</option>
                <option value="rejected" ${complaint.status === 'rejected' ? 'selected' : ''}>Rejected</option>
              </select>
            </div>
          </div>
        </div>
        
        <div class="field">
          <label class="label">Admin Notes</label>
          <div class="control">
            <textarea class="textarea" id="notes-${complaint.id}" placeholder="Add notes...">${complaint.admin_notes || ''}</textarea>
          </div>
        </div>
        
        <div class="field">
          <div class="control">
            <button class="button is-primary" onclick="saveComplaintNotes(${complaint.id})">
              <span class="icon">
                <i class="fas fa-save"></i>
              </span>
              <span>Save Notes</span>
            </button>
          </div>
        </div>
        
        <div class="level is-mobile">
          <div class="level-left">
            <div class="level-item">
              <small class="has-text-grey">
                <i class="fas fa-calendar-plus mr-1"></i>
                Created: ${formatDate(complaint.created_at)}
              </small>
            </div>
          </div>
          <div class="level-right">
            <div class="level-item">
              <small class="has-text-grey">
                <i class="fas fa-clock mr-1"></i>
                Updated: ${formatDate(complaint.updated_at)}
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
  `).join('');
}

async function updateComplaintStatus(complaintId, status) {
  try {
    await apiCall(`/api/admin/complaints/${complaintId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    
    showNotification('Status updated successfully!');
  } catch (error) {
    showNotification(error.message, 'danger');
  }
}

async function saveComplaintNotes(complaintId) {
  const notesTextarea = document.getElementById(`notes-${complaintId}`);
  const notes = notesTextarea.value;
  
  try {
    const currentStatus = document.querySelector(`select[onchange*="${complaintId}"]`).value;
    
    await apiCall(`/api/admin/complaints/${complaintId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        status: currentStatus,
        admin_notes: notes 
      })
    });
    
    showNotification('Notes saved successfully!');
  } catch (error) {
    showNotification(error.message, 'danger');
  }
}

// File upload handling
function setupFileUpload() {
  const fileInput = document.getElementById('screenshot');
  const uploadArea = document.querySelector('.file-upload-area');
  
  if (!fileInput || !uploadArea) return;
  
  uploadArea.addEventListener('click', () => fileInput.click());
  
  uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
  });
  
  uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
  });
  
  uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files;
      updateFileUploadDisplay(files[0]);
    }
  });
  
  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      updateFileUploadDisplay(e.target.files[0]);
    }
  });
}

function updateFileUploadDisplay(file) {
  const uploadArea = document.querySelector('.file-upload-area');
  if (!uploadArea) return;
  
  uploadArea.innerHTML = `
    <div class="has-text-centered">
      <i class="fas fa-check-circle has-text-success fa-2x mb-2"></i>
      <p><strong>${file.name}</strong></p>
      <p class="has-text-grey">${(file.size / 1024 / 1024).toFixed(2)} MB</p>
      <p class="has-text-grey is-size-7">Click to change file</p>
    </div>
  `;
}

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  loadAuthData();
  
  // Check authentication for protected pages
  const protectedPages = ['/dashboard', '/admin'];
  const currentPath = window.location.pathname;
  
  if (protectedPages.includes(currentPath) && !isAuthenticated()) {
    window.location.href = '/login';
    return;
  }
  
  // Redirect authenticated users away from auth pages
  const authPages = ['/login', '/register', '/forgot-password'];
  if (authPages.includes(currentPath) && isAuthenticated()) {
    if (currentUser.is_admin) {
      window.location.href = '/admin';
    } else {
      window.location.href = '/dashboard';
    }
    return;
  }
  
  // Setup page-specific functionality
  setupFileUpload();
  
  // Load data based on current page
  if (currentPath === '/dashboard') {
    loadUserComplaints();
  } else if (currentPath === '/admin') {
    loadAllComplaints();
  }
  
  // Update UI with user info
  if (currentUser) {
    const userNameElements = document.querySelectorAll('.user-name');
    userNameElements.forEach(el => el.textContent = currentUser.name);
    
    const userEmailElements = document.querySelectorAll('.user-email');
    userEmailElements.forEach(el => el.textContent = currentUser.email);
  }
});
