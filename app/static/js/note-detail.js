// 연구과제 상세 페이지 JavaScript

// Drag & Drop 업로드
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const folderSelect = document.getElementById('folderSelect');
    const modalFileInput = document.getElementById('uploadFiles');
    
    if (uploadArea && fileInput) {
        // Click to upload
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
        
        // Drag and drop
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
                handleFileUpload(files);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files);
            }
        });
    }

    // Modal 내 파일 선택 input 연동
    if (modalFileInput) {
        modalFileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                handleFileUpload(e.target.files);
            }
        });
    }
});

function handleFileUpload(files) {
    const folderId = document.getElementById('folderSelect')?.value;
    if (!folderId) {
        // 모달 내부에서 폴더를 먼저 선택하도록 안내만 하고 계속 진행 (목록 렌더링은 필요)
        console.warn('폴더가 선택되지 않았습니다. 업로드 전에 폴더를 선택해야 합니다.');
    }
    
    // Show upload modal
    const modal = new bootstrap.Modal(document.getElementById('uploadModal'));
    modal.show();
    
    // Populate file list
    const fileList = document.getElementById('uploadFileList');
    fileList.innerHTML = '';
    
    Array.from(files).forEach((file, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><i class="bi bi-file-earmark"></i> ${file.name}</td>
            <td>${(file.size / 1024 / 1024).toFixed(2)} MB</td>
            <td>
                <input type="date" class="form-control form-control-sm" name="created_date_${index}" 
                       value="${new Date().toISOString().split('T')[0]}" required>
            </td>
            <td>
                <input type="text" class="form-control form-control-sm" name="short_desc_${index}" 
                       placeholder="실험 목적">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm" name="tags_${index}" 
                       placeholder="태그1,태그2">
            </td>
        `;
        fileList.appendChild(row);
        
        // Store file data
        row.dataset.file = index;
    });
    
    // Store files globally
    window.uploadFiles = files;
}

document.getElementById('uploadForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    const folderId = document.getElementById('folderSelect')?.value;
    if (!folderId) {
        alert('폴더를 선택해주세요.');
        return;
    }
    
    // Add files
    if (!window.uploadFiles || window.uploadFiles.length === 0) {
        alert('업로드할 파일을 선택해주세요.');
        return;
    }
    Array.from(window.uploadFiles).forEach(file => {
        formData.append('files[]', file);
    });
    
    // Add metadata
    const rows = document.querySelectorAll('#uploadFileList tr');
    rows.forEach((row, index) => {
        const createdDate = row.querySelector(`input[name="created_date_${index}"]`).value;
        const shortDesc = row.querySelector(`input[name="short_desc_${index}"]`).value;
        const tags = row.querySelector(`input[name="tags_${index}"]`).value;
        
        formData.append('created_date', createdDate);
        formData.append('short_desc', shortDesc);
        formData.append('tags', tags);
    });
    
    // Upload
    try {
        const response = await fetch(`/folders/${folderId}/files`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            bootstrap.Modal.getInstance(document.getElementById('uploadModal')).hide();
            location.reload();
        } else {
            const data = await response.json();
            alert('업로드 실패: ' + (data.error || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('업로드 중 오류가 발생했습니다.');
    }
});

// 파일 버전 업로드
window.uploadNewVersion = function(fileId) {
    const input = document.createElement('input');
    input.type = 'file';
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reason = prompt('변경 사유를 입력하세요:', '');
        if (!reason) return;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('change_reason', reason);
        
        fetch(`/files/${fileId}/new-version`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('업로드 실패: ' + (data.error || '알 수 없는 오류'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('업로드 중 오류가 발생했습니다.');
        });
    };
    input.click();
};

// 파일 태그 편집
window.editFileTags = function(fileId, currentTags) {
    const newTags = prompt('태그를 입력하세요 (쉼표로 구분):', currentTags);
    if (newTags === null) return;
    
    fetch(`/files/${fileId}/tags`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tags: newTags})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('수정 실패: ' + (data.error || '알 수 없는 오류'));
        }
    });
};

// 파일명 변경
window.renameFile = function(fileId, currentName) {
    const newName = prompt('새 파일명을 입력하세요:', currentName);
    if (!newName || newName === currentName) return;
    
    fetch(`/files/${fileId}/rename`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({display_name: newName})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('수정 실패: ' + (data.error || '알 수 없는 오류'));
        }
    });
};

