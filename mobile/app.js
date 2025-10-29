// DOM Elements
const typeSelect = document.getElementById('type');
const amountInput = document.getElementById('amount');
const categoryInput = document.getElementById('category');
const dateInput = document.getElementById('date');
const descriptionInput = document.getElementById('description');
const addButton = document.getElementById('add-transaction');
const transactionsList = document.getElementById('transactions-list');
const filterType = document.getElementById('filter-type');
const filterMonth = document.getElementById('filter-month');
const totalIncomeEl = document.getElementById('total-income');
const totalExpenseEl = document.getElementById('total-expense');
const balanceEl = document.getElementById('balance');
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');
const installBtn = document.getElementById('install-btn');

// Set default date to today
const today = new Date();
dateInput.valueAsDate = today;

// Set default month filter to current month
const currentMonth = today.toISOString().slice(0, 7);
filterMonth.value = currentMonth;

// Initialize app
let transactions = JSON.parse(localStorage.getItem('transactions')) || [];

// Tab switching
tabButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Remove active class from all buttons and contents
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));
        
        // Add active class to clicked button and corresponding content
        button.classList.add('active');
        const tabId = button.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
        
        // If switching to transactions tab, refresh the list
        if (tabId === 'transactions') {
            renderTransactions();
        }
    });
});

// Add transaction
addButton.addEventListener('click', addTransaction);

// Add transaction on Enter key
[amountInput, categoryInput, descriptionInput].forEach(input => {
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addTransaction();
        }
    });
});

// Filter transactions
[filterType, filterMonth].forEach(filter => {
    filter.addEventListener('change', renderTransactions);
});

// Add transaction function
function addTransaction() {
    const amount = parseFloat(amountInput.value);
    const type = typeSelect.value;
    const category = categoryInput.value.trim();
    const date = dateInput.value;
    const description = descriptionInput.value.trim();
    
    // Validate inputs
    if (!amount || isNaN(amount) || amount <= 0) {
        showAlert('Please enter a valid amount', 'error');
        return;
    }
    
    if (!category) {
        showAlert('Please enter a category', 'error');
        return;
    }
    
    // Create transaction object
    const transaction = {
        id: Date.now().toString(),
        type,
        amount: parseFloat(amount.toFixed(2)),
        category,
        date,
        description,
        createdAt: new Date().toISOString()
    };
    
    // Add to transactions array
    transactions.unshift(transaction);
    
    // Save to localStorage
    saveTransactions();
    
    // Clear form
    amountInput.value = '';
    descriptionInput.value = '';
    categoryInput.focus();
    
    // Show success message
    showAlert('Transaction added successfully!', 'success');
    
    // If on transactions tab, refresh the list
    if (document.getElementById('transactions').classList.contains('active')) {
        renderTransactions();
    }
}

// Render transactions list
function renderTransactions() {
    const typeFilter = filterType.value;
    const monthFilter = filterMonth.value;
    
    // Filter transactions
    let filteredTransactions = transactions.filter(transaction => {
        // Filter by type
        if (typeFilter !== 'all' && transaction.type !== typeFilter) {
            return false;
        }
        
        // Filter by month
        if (monthFilter && !transaction.date.startsWith(monthFilter)) {
            return false;
        }
        
        return true;
    });
    
    // Clear current list
    transactionsList.innerHTML = '';
    
    if (filteredTransactions.length === 0) {
        transactionsList.innerHTML = '<div class="no-transactions">No transactions found</div>';
        updateSummary([]);
        return;
    }
    
    // Add transactions to the list
    filteredTransactions.forEach(transaction => {
        const transactionEl = document.createElement('div');
        transactionEl.className = 'transaction-item';
        
        const date = new Date(transaction.date);
        const formattedDate = date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
        
        transactionEl.innerHTML = `
            <div class="transaction-details">
                <div class="transaction-description">
                    ${transaction.description || transaction.category}
                </div>
                <div class="transaction-category">
                    ${transaction.category} • ${formattedDate}
                </div>
            </div>
            <div class="transaction-amount ${transaction.type}">
                ${transaction.type === 'expense' ? '-' : '+'}${transaction.amount.toFixed(2)}
            </div>
        `;
        
        // Add click handler to edit/delete
        transactionEl.addEventListener('click', () => {
            // For now, just show details in an alert
            showTransactionDetails(transaction);
        });
        
        transactionsList.appendChild(transactionEl);
    });
    
    // Update summary
    updateSummary(filteredTransactions);
}

// Update summary
function updateSummary(transactions) {
    const summary = transactions.reduce(
        (acc, transaction) => {
            if (transaction.type === 'income') {
                acc.income += transaction.amount;
            } else {
                acc.expense += transaction.amount;
            }
            return acc;
        },
        { income: 0, expense: 0 }
    );
    
    totalIncomeEl.textContent = `$${summary.income.toFixed(2)}`;
    totalExpenseEl.textContent = `$${summary.expense.toFixed(2)}`;
    balanceEl.textContent = `$${(summary.income - summary.expense).toFixed(2)}`;
    
    // Update balance color
    const balance = summary.income - summary.expense;
    balanceEl.style.color = balance >= 0 ? 'var(--primary-color)' : 'var(--danger-color)';
}

// Show transaction details
function showTransactionDetails(transaction) {
    const date = new Date(transaction.date);
    const formattedDate = date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
    
    const type = transaction.type === 'income' ? 'Income' : 'Expense';
    
    const details = `
        <strong>${transaction.description || transaction.category}</strong><br>
        <small>${type} • ${transaction.category}</small><br><br>
        <strong>Amount:</strong> $${transaction.amount.toFixed(2)}<br>
        <strong>Date:</strong> ${formattedDate}<br>
        ${transaction.description ? `<strong>Notes:</strong> ${transaction.description}<br>` : ''}
    `;
    
    // Simple alert for now, could be replaced with a modal
    if (confirm(`${details}\n\nDo you want to delete this transaction?`)) {
        deleteTransaction(transaction.id);
    }
}

// Delete transaction
function deleteTransaction(id) {
    transactions = transactions.filter(t => t.id !== id);
    saveTransactions();
    renderTransactions();
    showAlert('Transaction deleted', 'success');
}

// Save transactions to localStorage
function saveTransactions() {
    localStorage.setItem('transactions', JSON.stringify(transactions));
}

// Show alert message
function showAlert(message, type = 'info') {
    // Simple alert for now, could be replaced with a toast notification
    alert(message);
}

// PWA Installation
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    // Show the install button
    installBtn.style.display = 'block';
});

installBtn.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    
    // Show the install prompt
    deferredPrompt.prompt();
    
    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;
    
    // Optionally, send analytics event with outcome of user choice
    console.log(`User response to the install prompt: ${outcome}`);
    
    // We've used the prompt, and can't use it again, throw it away
    deferredPrompt = null;
    
    // Hide the install button
    installBtn.style.display = 'none';
});

// Check if the app is running as a PWA
window.addEventListener('appinstalled', () => {
    // Hide the install button
    installBtn.style.display = 'none';
    // Clear the deferredPrompt so it can be garbage collected
    deferredPrompt = null;
    // Optionally, send analytics that the app was installed
    console.log('PWA was installed');
});

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js')
            .then(registration => {
                console.log('ServiceWorker registration successful');
            })
            .catch(err => {
                console.log('ServiceWorker registration failed: ', err);
            });
    });
}

// Initial render
renderTransactions();
