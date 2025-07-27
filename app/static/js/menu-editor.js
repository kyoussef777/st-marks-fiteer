document.addEventListener('DOMContentLoaded', function() {
    const editMenuBtn = document.getElementById('editMenuBtn');
    const editDrinksIcon = document.getElementById('editDrinksIcon');
    const editMilksIcon = document.getElementById('editMilksIcon');
    const editSyrupsIcon = document.getElementById('editSyrupsIcon');
    const editFoamsIcon = document.getElementById('editFoamsIcon');
    
    const drinkSelectContainer = document.getElementById('drinkSelectContainer');
    const drinkEditContainer = document.getElementById('drinkEditContainer');
    const milkSelectContainer = document.getElementById('milkSelectContainer');
    const milkEditContainer = document.getElementById('milkEditContainer');
    const syrupSelectContainer = document.getElementById('syrupSelectContainer');
    const syrupEditContainer = document.getElementById('syrupEditContainer');
    const foamSelectContainer = document.getElementById('foamSelectContainer');
    const foamEditContainer = document.getElementById('foamEditContainer');
    
    let editMode = false;

    // Toggle edit mode
    editMenuBtn.addEventListener('click', function() {
        editMode = !editMode;
        
        if (editMode) {
            // Enter edit mode
            editMenuBtn.textContent = '💾 Save Changes';
            editMenuBtn.className = 'btn btn-success btn-sm';
            
            editDrinksIcon.style.display = 'inline';
            editMilksIcon.style.display = 'inline';
            editSyrupsIcon.style.display = 'inline';
            editFoamsIcon.style.display = 'inline';
            
            drinkSelectContainer.style.display = 'none';
            drinkEditContainer.style.display = 'block';
            milkSelectContainer.style.display = 'none';
            milkEditContainer.style.display = 'block';
            syrupSelectContainer.style.display = 'none';
            syrupEditContainer.style.display = 'block';
            foamSelectContainer.style.display = 'none';
            foamEditContainer.style.display = 'block';
        } else {
            // Exit edit mode
            editMenuBtn.textContent = '✏️ Edit Menu';
            editMenuBtn.className = 'btn btn-outline-secondary btn-sm';
            
            editDrinksIcon.style.display = 'none';
            editMilksIcon.style.display = 'none';
            editSyrupsIcon.style.display = 'none';
            editFoamsIcon.style.display = 'none';
            
            drinkSelectContainer.style.display = 'block';
            drinkEditContainer.style.display = 'none';
            milkSelectContainer.style.display = 'block';
            milkEditContainer.style.display = 'none';
            syrupSelectContainer.style.display = 'block';
            syrupEditContainer.style.display = 'none';
            foamSelectContainer.style.display = 'block';
            foamEditContainer.style.display = 'none';
            
            // Refresh the page to show updated menu
            location.reload();
        }
    });

    // Save item changes
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('save-item')) {
            const editItem = e.target.closest('.edit-item');
            const itemId = editItem.dataset.id;
            const itemName = editItem.querySelector('.item-name').value;
            const itemPriceInput = editItem.querySelector('.item-price');
            const itemPrice = itemPriceInput ? itemPriceInput.value : null;
            
            if (!itemName.trim()) {
                alert('Item name is required');
                return;
            }
            
            const formData = new FormData();
            formData.append('csrf_token', getCsrfToken());
            formData.append('item_name', itemName);
            if (itemPrice) {
                formData.append('price', itemPrice);
            }
            
            fetch(`/update_menu_item/${itemId}`, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    e.target.textContent = '✅';
                    setTimeout(() => {
                        e.target.textContent = '💾';
                    }, 1000);
                } else {
                    alert('Error updating item');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error updating item');
            });
        }
    });

    // Delete item
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-item')) {
            if (confirm('Are you sure you want to delete this item?')) {
                const editItem = e.target.closest('.edit-item');
                const itemId = editItem.dataset.id;
                
                const formData = new FormData();
                formData.append('csrf_token', getCsrfToken());
                
                fetch(`/delete_menu_item/${itemId}`, {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.ok) {
                        editItem.remove();
                    } else {
                        alert('Error deleting item');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error deleting item');
                });
            }
        }
    });

    // Add new drink
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-drink')) {
            const addItem = e.target.closest('.add-item');
            const itemName = addItem.querySelector('.new-item-name').value;
            const itemPrice = addItem.querySelector('.new-item-price').value;
            
            if (!itemName.trim()) {
                alert('Drink name is required');
                return;
            }
            
            if (!itemPrice || parseFloat(itemPrice) <= 0) {
                alert('Valid price is required for drinks');
                return;
            }
            
            const formData = new FormData();
            formData.append('csrf_token', getCsrfToken());
            formData.append('item_type', 'drink');
            formData.append('item_name', itemName);
            formData.append('price', itemPrice);
            
            fetch('/add_menu_item', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    // Clear inputs
                    addItem.querySelector('.new-item-name').value = '';
                    addItem.querySelector('.new-item-price').value = '';
                    
                    // Show success message
                    e.target.textContent = '✅ Added';
                    setTimeout(() => {
                        e.target.textContent = '➕ Add Drink';
                    }, 1000);
                    
                    // Optionally refresh to show new item
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                } else {
                    alert('Error adding drink');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error adding drink');
            });
        }
    });

    // Add new milk
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-milk')) {
            const addItem = e.target.closest('.add-item');
            const itemName = addItem.querySelector('.new-item-name').value;
            
            if (!itemName.trim()) {
                alert('Milk type is required');
                return;
            }
            
            const formData = new FormData();
            formData.append('csrf_token', getCsrfToken());
            formData.append('item_type', 'milk');
            formData.append('item_name', itemName);
            
            fetch('/add_menu_item', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    // Clear input
                    addItem.querySelector('.new-item-name').value = '';
                    
                    // Show success message
                    e.target.textContent = '✅ Added';
                    setTimeout(() => {
                        e.target.textContent = '➕ Add Milk';
                    }, 1000);
                    
                    // Optionally refresh to show new item
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                } else {
                    alert('Error adding milk type');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error adding milk type');
            });
        }
    });

    // Add new syrup
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-syrup')) {
            const addItem = e.target.closest('.add-item');
            const itemName = addItem.querySelector('.new-item-name').value;
            
            if (!itemName.trim()) {
                alert('Syrup type is required');
                return;
            }
            
            const formData = new FormData();
            formData.append('csrf_token', getCsrfToken());
            formData.append('item_type', 'syrup');
            formData.append('item_name', itemName);
            
            fetch('/add_menu_item', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    // Clear input
                    addItem.querySelector('.new-item-name').value = '';
                    
                    // Show success message
                    e.target.textContent = '✅ Added';
                    setTimeout(() => {
                        e.target.textContent = '➕ Add Syrup';
                    }, 1000);
                    
                    // Optionally refresh to show new item
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                } else {
                    alert('Error adding syrup type');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error adding syrup type');
            });
        }
    });

    // Add new foam
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-foam')) {
            const addItem = e.target.closest('.add-item');
            const itemName = addItem.querySelector('.new-item-name').value;
            
            if (!itemName.trim()) {
                alert('Foam type is required');
                return;
            }
            
            const formData = new FormData();
            formData.append('csrf_token', getCsrfToken());
            formData.append('item_type', 'foam');
            formData.append('item_name', itemName);
            
            fetch('/add_menu_item', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    // Clear input
                    addItem.querySelector('.new-item-name').value = '';
                    
                    // Show success message
                    e.target.textContent = '✅ Added';
                    setTimeout(() => {
                        e.target.textContent = '➕ Add Foam';
                    }, 1000);
                    
                    // Optionally refresh to show new item
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                } else {
                    alert('Error adding foam type');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error adding foam type');
            });
        }
    });

    // Helper function to get CSRF token
    function getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrf_token') {
                return value;
            }
        }
        return '';
    }
});
