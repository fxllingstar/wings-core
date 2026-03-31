// wings-core Server Manager JavaScript
 
/*
# wings-core
# Copyright (C) 2026 fxllingstar on GitHub
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
 * 
 */
// State
let startTime = null;
let projects = [];
 
// DOM Elements
const statsSection = document.getElementById('stats-section');
const projectsSection = document.getElementById('projects-section');
const filesSection = document.getElementById('files-section');
 
// Navigation
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Remove active from all links and sections
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
        
        // Add active to clicked link
        link.classList.add('active');
        
        // Show corresponding section
        const section = link.dataset.section;
        document.getElementById(`${section}-section`).classList.add('active');
        
        // Load data for the section
        if (section === 'stats') {
            loadStats();
        } else if (section === 'projects') {
            loadProjects();
        } else if (section === 'files') {
            loadProjectDropdown();
        }
    });
});
 
// Load Server Stats
async function loadStats() {
    const statusElement = document.getElementById('server-status');
    
    try {
        const response = await fetch('/api/stats');
        
        if (!response.ok) throw new Error("Server error");

        const data = await response.json();
        
        // --- 1. Update Status to Online ---
        statusElement.textContent = "Online";
        statusElement.className = "status-online"; // We'll add CSS for this

        // --- 2. Update existing data ---
        startTime = data.start_time * 1000;
        document.getElementById('total-projects').textContent = data.total_projects;
        document.getElementById('total-versions').textContent = data.total_versions;
        document.getElementById('total-size').textContent = data.total_size_mb;
        document.getElementById('active-users').textContent = data.active_users;
        
        updateUptime();
        

        
    } catch (error) {
        // --- 3. Handle Offline State ---
       statusElement.innerHTML = '<span class="status-dot offline"></span> Offline';
    statusElement.className = "status-value status-indicator offline-text";
    
    // Show a warning in the Uptime area
    document.getElementById('uptime').textContent = "Server Connection Lost";
    console.error('The server might have crashed. Check crash.log on the host.');
    }
}
 
// Update Uptime
function updateUptime() {

    if (!startTime) {
        document.getElementById('uptime').textContent = "Calculating...";
        return;
    }
    
    const elapsed = Date.now() - startTime;
    const seconds = Math.floor(elapsed / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    let uptimeStr = '';
    if (days > 0) {
        uptimeStr += `${days}d `;
    }
    if (hours % 24 > 0) {
        uptimeStr += `${hours % 24}h `;
    }
    if (minutes % 60 > 0) {
        uptimeStr += `${minutes % 60}m `;
    }
    uptimeStr += `${seconds % 60}s`;
    
    document.getElementById('uptime').textContent = uptimeStr;
}
 
// Load Projects
async function loadProjects() {
    const projectsList = document.getElementById('projects-list');
    projectsList.innerHTML = '<div class="loading">Loading projects...</div>';
    
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        projects = data.projects;
        
        if (projects.length === 0) {
            projectsList.innerHTML = '<div class="empty-state"><p>No projects found</p></div>';
            return;
        }
        
        projectsList.innerHTML = '';
        projects.forEach(project => {
            const card = createProjectCard(project);
            projectsList.appendChild(card);
        });
        
    } catch (error) {
        console.error('Failed to load projects:', error);
        projectsList.innerHTML = '<div class="error-message">Failed to load projects</div>';
    }
}
 
// Create Project Card
function createProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'project-card';
    
    const timestamp = project.timestamp !== 'N/A' 
        ? new Date(project.timestamp).toLocaleString() 
        : 'N/A';
    
    card.innerHTML = `
        <div class="project-header">
            <div class="project-name">${escapeHtml(project.id)}</div>
            <div class="project-version">v${escapeHtml(project.latest_version)}</div>
        </div>
        <div class="project-meta">
            <div class="meta-item">
                <span class="meta-label">Versions</span>
                <span class="meta-value">${project.version_count}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Last Author</span>
                <span class="meta-value">${escapeHtml(project.last_author)}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Last Updated</span>
                <span class="meta-value">${escapeHtml(timestamp)}</span>
            </div>
        </div>
    `;
    
    return card;
}
 
// Load Project Dropdown for File Browser
async function loadProjectDropdown() {
    const select = document.getElementById('project-select');
    select.innerHTML = '<option value="">Select a project...</option>';
    
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        
        data.projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = `${project.id} (v${project.latest_version})`;
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('Failed to load projects for dropdown:', error);
    }
}
 
// Browse Files
document.getElementById('browse-files').addEventListener('click', async () => {
    const projectId = document.getElementById('project-select').value;
    const fileList = document.getElementById('file-list');
    
    if (!projectId) {
        fileList.innerHTML = '<div class="empty-state"><p>Please select a project first</p></div>';
        return;
    }
    
    fileList.innerHTML = '<div class="loading">Loading files...</div>';
    
    try {
        // Since we don't have a direct API endpoint for listing files,
        // we'll show the versions as downloadable items
        const response = await fetch(`/list?project_id=${encodeURIComponent(projectId)}`);
        const data = await response.json();
        
        if (!data.versions || data.versions.length === 0) {
            fileList.innerHTML = '<div class="empty-state"><p>No versions found for this project</p></div>';
            return;
        }
        
        fileList.innerHTML = '';
        data.versions.forEach(version => {
            const fileItem = createFileItem(projectId, version);
            fileList.appendChild(fileItem);
        });
        
    } catch (error) {
        console.error('Failed to load files:', error);
        fileList.innerHTML = '<div class="error-message">Failed to load files. Authentication may be required.</div>';
    }
});
 
// Create File Item
function createFileItem(projectId, version) {
    const item = document.createElement('div');
    item.className = 'file-item';
    
    const zipFile = `${version}.zip`;
    const logFile = `${version}.log`;
    
    item.innerHTML = `
        <div class="file-info">
            <div class="file-icon">📦</div>
            <div class="file-details">
                <div class="file-name">Version ${escapeHtml(version)}</div>
                <div class="file-size">ZIP + Log files</div>
            </div>
        </div>
        <div style="display: flex; gap: 0.5rem;">
            <a href="/download/${encodeURIComponent(projectId)}/${encodeURIComponent(zipFile)}" 
               class="btn-download" target="_blank">
                📦 ZIP
            </a>
            <a href="/download/${encodeURIComponent(projectId)}/${encodeURIComponent(logFile)}" 
               class="btn-download" target="_blank">
                📄 Log
            </a>
        </div>
    `;
    
    return item;
}
 
// Refresh Projects Button
document.getElementById('refresh-projects').addEventListener('click', () => {
    loadProjects();
});
 
// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
 
// Utility: Show Error
function showError(message) {
    console.error(message);
    // You could add a toast notification system here
}
 
// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Load initial stats
    loadStats();
    
    // Update uptime every second
    setInterval(updateUptime, 1000);
    updateUptime();
    
    // Refresh stats every 30 seconds
    setInterval(loadStats, 30000);
});
 