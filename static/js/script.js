// Global variables
let currentUser = null;

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
});

// Initialize dashboard functionality
function initializeDashboard() {
    // Set up invite buttons
    const sendInviteButtons = document.querySelectorAll('.send-invite');
    sendInviteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const receiverId = this.dataset.receiverId;
            sendInvite(receiverId);
        });
    });
    
    // Set up invite response buttons
    const respondInviteButtons = document.querySelectorAll('.respond-invite');
    respondInviteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const inviteId = this.dataset.inviteId;
            const action = this.dataset.action;
            respondToInvite(inviteId, action);
        });
    });
    
    // Set up supervisor request response buttons
    const respondSupervisorRequestButtons = document.querySelectorAll('.respond-supervisor-request');
    respondSupervisorRequestButtons.forEach(button => {
        button.addEventListener('click', function() {
            const requestId = this.dataset.requestId;
            const action = this.dataset.action;
            respondToSupervisorRequest(requestId, action);
        });
    });
    
    // Initialize search functionality
    const searchInput = document.getElementById('search-student');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(searchStudent, 300));
    }
}

// Setup event listeners
function setupEventListeners() {
    // Form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
    
    // Real-time validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', validateEmail);
    });
    
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        input.addEventListener('input', validatePasswordStrength);
    });
}

// Form submission handler
function handleFormSubmit(event) {
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Add loading state
    if (submitButton) {
        const originalText = submitButton.textContent;
        submitButton.innerHTML = '<div class="loading"></div> Processing...';
        submitButton.disabled = true;
        
        // Revert after 3 seconds if still processing
        setTimeout(() => {
            submitButton.textContent = originalText;
            submitButton.disabled = false;
        }, 3000);
    }
}

// OTP sending functionality
function sendOTP(email, callback) {
    if (!validateEmailInput(email)) {
        if (callback) callback({ success: false, message: 'Please enter a valid email address' });
        return;
    }
    
    showLoading('Sending OTP...');
    
    fetch('/send_otp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (callback) callback(data);
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        if (callback) callback({ success: false, message: 'Network error occurred' });
    });
}

// Send invite to student
function sendInvite(receiverId) {
    showLoading('Sending invite...');
    
    fetch('/send_invite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ receiver_id: receiverId })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        showNotification(data.message, data.success ? 'success' : 'error');
        if (data.success) {
            setTimeout(() => location.reload(), 1000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showNotification('Network error occurred', 'error');
    });
}

// Respond to group invite
function respondToInvite(inviteId, action) {
    showLoading('Processing...');
    
    fetch('/respond_invite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            invite_id: inviteId,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        showNotification(data.message, data.success ? 'success' : 'error');
        if (data.success) {
            setTimeout(() => location.reload(), 1000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showNotification('Network error occurred', 'error');
    });
}

// Request supervisor
function requestSupervisor() {
    const supervisorSelect = document.getElementById('supervisor-select');
    const supervisorId = supervisorSelect.value;
    
    if (!supervisorId) {
        showNotification('Please select a supervisor', 'error');
        return;
    }
    
    showLoading('Sending request...');
    
    fetch('/request_supervisor', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ supervisor_id: supervisorId })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        showNotification(data.message, data.success ? 'success' : 'error');
        if (data.success) {
            setTimeout(() => location.reload(), 1000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showNotification('Network error occurred', 'error');
    });
}

// Respond to supervisor request
function respondToSupervisorRequest(requestId, action) {
    showLoading('Processing...');
    
    fetch('/respond_supervisor_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            request_id: requestId,
            action: action
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        showNotification(data.message, data.success ? 'success' : 'error');
        if (data.success) {
            setTimeout(() => location.reload(), 1000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showNotification('Network error occurred', 'error');
    });
}

// Update project title
function updateProjectTitle() {
    const titleInput = document.getElementById('project-title');
    const title = titleInput.value.trim();
    
    if (!title) {
        showNotification('Please enter a project title', 'error');
        return;
    }
    
    showLoading('Updating project title...');
    
    fetch('/update_project_title', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: title })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        showNotification(data.message, data.success ? 'success' : 'error');
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showNotification('Network error occurred', 'error');
    });
}

// Update document link
function updateDocumentLink() {
    const linkInput = document.getElementById('document-link');
    const link = linkInput.value.trim();
    
    if (!link) {
        showNotification('Please enter a document link', 'error');
        return;
    }
    
    // Basic URL validation
    if (!isValidUrl(link)) {
        showNotification('Please enter a valid URL', 'error');
        return;
    }
    
    showLoading('Updating document link...');
    
    fetch('/update_document_link', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ link: link })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        showNotification(data.message, data.success ? 'success' : 'error');
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showNotification('Network error occurred', 'error');
    });
}

// Assign marks to student
function assignMarks(studentId) {
    const presentation = parseFloat(document.getElementById(`presentation-${studentId}`).value) || 0;
    const documents = parseFloat(document.getElementById(`documents-${studentId}`).value) || 0;
    const collaboration = parseFloat(document.getElementById(`collaboration-${studentId}`).value) || 0;
    
    // Validate marks
    if (presentation < 0 || presentation > 10 || 
        documents < 0 || documents > 10 || 
        collaboration < 0 || collaboration > 10) {
        showNotification('Marks must be between 0 and 10', 'error');
        return;
    }
    
    showLoading('Assigning marks...');
    
    fetch('/assign_marks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            student_id: studentId,
            presentation: presentation,
            documents: documents,
            collaboration: collaboration
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        showNotification(data.message, data.success ? 'success' : 'error');
        if (data.success) {
            // Update total display
            const total = presentation + documents + collaboration;
            const totalElement = document.querySelector(`[data-student-total="${studentId}"]`);
            if (totalElement) {
                totalElement.textContent = `${total}/30`;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showNotification('Network error occurred', 'error');
    });
}

// Create panel for group
function createPanel(groupId) {
    const checkboxes = document.querySelectorAll(`.panel-checkbox-${groupId}:checked`);
    const supervisorIds = Array.from(checkboxes).map(checkbox => checkbox.value);
    
    if (supervisorIds.length !== 3) {
        showNotification('Please select exactly 3 panel members', 'error');
        return;
    }
    
    showLoading('Creating panel...');
    
    fetch('/create_panel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            group_id: groupId,
            supervisor_ids: supervisorIds
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        showNotification(data.message, data.success ? 'success' : 'error');
        if (data.success) {
            setTimeout(() => location.reload(), 1000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideLoading();
        showNotification('Network error occurred', 'error');
    });
}

// Search student functionality
function searchStudent() {
    const searchTerm = document.getElementById('search-student').value.trim();
    const availableStudents = document.querySelectorAll('.available-students tr');
    
    if (!searchTerm) {
        // Show all students if search is empty
        availableStudents.forEach(row => {
            row.style.display = '';
        });
        return;
    }
    
    availableStudents.forEach(row => {
        const rollNumber = row.cells[1].textContent.toLowerCase();
        if (rollNumber.includes(searchTerm.toLowerCase())) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Validation functions
function validateEmailInput(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateEmail(event) {
    const email = event.target.value.trim();
    const isValid = validateEmailInput(email);
    
    if (email && !isValid) {
        event.target.style.borderColor = '#e74c3c';
        showTooltip(event.target, 'Please enter a valid email address');
    } else {
        event.target.style.borderColor = isValid ? '#27ae60' : '#ddd';
        hideTooltip(event.target);
    }
}

function validatePasswordStrength(event) {
    const password = event.target.value;
    const strength = calculatePasswordStrength(password);
    
    // Visual feedback for password strength
    event.target.style.borderColor = 
        strength >= 80 ? '#27ae60' : 
        strength >= 60 ? '#f39c12' : 
        strength >= 40 ? '#e67e22' : '#e74c3c';
}

function calculatePasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (/[A-Z]/.test(password)) strength += 25;
    if (/[0-9]/.test(password)) strength += 25;
    if (/[^A-Za-z0-9]/.test(password)) strength += 25;
    return strength;
}

function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showLoading(message = 'Loading...') {
    // Create or show loading overlay
    let loadingOverlay = document.getElementById('loading-overlay');
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loading-overlay';
        loadingOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            color: white;
            font-size: 18px;
        `;
        document.body.appendChild(loadingOverlay);
    }
    
    loadingOverlay.innerHTML = `
        <div style="text-align: center;">
            <div class="loading" style="width: 40px; height: 40px; margin: 0 auto 1rem;"></div>
            <div>${message}</div>
        </div>
    `;
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification alert alert-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        min-width: 300px;
        max-width: 500px;
        animation: slideIn 0.3s ease;
    `;
    
    notification.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 18px; cursor: pointer;">×</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function showTooltip(element, message) {
    let tooltip = element.parentElement.querySelector('.tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.style.cssText = `
            position: absolute;
            background: #e74c3c;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            margin-top: 5px;
        `;
        element.parentElement.style.position = 'relative';
        element.parentElement.appendChild(tooltip);
    }
    tooltip.textContent = message;
    tooltip.style.display = 'block';
}

function hideTooltip(element) {
    const tooltip = element.parentElement.querySelector('.tooltip');
    if (tooltip) {
        tooltip.style.display = 'none';
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl + / for search focus
    if (event.ctrlKey && event.key === '/') {
        event.preventDefault();
        const searchInput = document.getElementById('search-student');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals/notifications
    if (event.key === 'Escape') {
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach(notification => notification.remove());
        
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }
});

// Export functions for global access
window.sendOTP = sendOTP;
window.sendInvite = sendInvite;
window.respondToInvite = respondToInvite;
window.requestSupervisor = requestSupervisor;
window.respondToSupervisorRequest = respondToSupervisorRequest;
window.updateProjectTitle = updateProjectTitle;
window.updateDocumentLink = updateDocumentLink;
window.assignMarks = assignMarks;
window.createPanel = createPanel;
window.searchStudent = searchStudent;
window.showNotification = showNotification;