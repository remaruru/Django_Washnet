import sys
import re

with open('c:/Users/Admin/Downloads/DjangoGroupProjectNew/templates/core/employee/pos.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Product addItem onclick to openProductModal
content = content.replace(
    '''onclick="addItem(\'Product\', \'{{ product.id }}\', \'{{ product.name|escapejs }}\', parseFloat(\'{{ product.price }}\'))"''',
    '''onclick="openProductModal(\'{{ product.id }}\', \'{{ product.name|escapejs }}\', parseFloat(\'{{ product.price }}\'))"'''
)

# Insert Product Modal HTML
product_modal_html = """
<!-- Product Modal -->
<div id="productModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center;">
    <div class="glass-card" style="background: white; padding: 2rem; border-radius: 12px; width: 90%; max-width: 400px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem;">
            <h2 id="productModalTitle" style="font-size: 1.5rem; color: var(--primary); margin: 0;">Add Product</h2>
            <button type="button" onclick="closeProductModal()" style="background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--secondary);">×</button>
        </div>
        
        <div class="form-group mb-4">
            <label class="form-label" style="font-weight: 600;">Quantity (pieces)</label>
            <input type="number" id="productModalQty" class="form-control" placeholder="1" value="1" style="padding: 0.8rem; font-size: 1.1rem; width: 100%; box-sizing: border-box;" min="1" step="1">
        </div>

        <div style="margin-top: 2rem; padding-top: 1.5rem; display: flex; justify-content: flex-end; gap: 1rem;">
            <button type="button" class="btn btn-outline" onclick="closeProductModal()">Cancel</button>
            <button type="button" class="btn btn-primary" onclick="confirmProductAddition()">Add</button>
        </div>
    </div>
</div>

<!-- Toast Error Notification -->
<div id="toastNotification" style="display: none; position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: var(--error); color: white; padding: 1rem 2rem; border-radius: 8px; z-index: 2000; font-weight: 600; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
    <span id="toastMessage">Error</span>
</div>

<script>
"""

content = content.replace('<!-- Extra Products Data Injection -->\n<script>', '<!-- Extra Products Data Injection -->\n' + product_modal_html)

# Rewrite script content to remove alerts and fix duplicated tails
script_replacement = """
    const availableProducts = [
        {% for product in products %}
        { id: '{{ product.id }}', name: '{{ product.name|escapejs }}', price: parseFloat('{{ product.price }}') }{% if not forloop.last %},{% endif %}
        {% endfor %}
    ];

    let cart = [];
    let currentService = null;
    let currentProduct = null;
    
    function showError(msg) {
        const toast = document.getElementById('toastNotification');
        document.getElementById('toastMessage').innerText = msg;
        toast.style.display = 'block';
        setTimeout(() => toast.style.display = 'none', 3000);
    }

    function openServiceModal(id, name, price) {
        currentService = { id, name, price };
        document.getElementById('modalTitle').innerText = name + ' (₱' + price + '/kg)';
        document.getElementById('modalWeight').value = '';
        document.getElementById('loadsContainer').innerHTML = '';
        
        const modal = document.getElementById('serviceModal');
        modal.style.display = 'flex';
    }

    function closeServiceModal() {
        document.getElementById('serviceModal').style.display = 'none';
        currentService = null;
    }

    function openProductModal(id, name, price) {
        currentProduct = { id, name, price };
        document.getElementById('productModalTitle').innerText = name + ' (₱' + price + ')';
        document.getElementById('productModalQty').value = '1';
        
        const modal = document.getElementById('productModal');
        modal.style.display = 'flex';
    }

    function closeProductModal() {
        document.getElementById('productModal').style.display = 'none';
        currentProduct = null;
    }

    function calculateLoads() {
        const weight = parseFloat(document.getElementById('modalWeight').value);
        const loadsContainer = document.getElementById('loadsContainer');
        
        if (isNaN(weight) || weight <= 0) {
            loadsContainer.innerHTML = '';
            return;
        }

        const numLoads = Math.ceil(weight / 7);
        let html = '<h3 style="font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem;">Configure Add-ons (' + numLoads + ' Loads Found)</h3>';
        
        for (let i = 1; i <= numLoads; i++) {
            html += `
                <div style="background: #F9FAFB; border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                    <h4 style="font-weight: 600; margin-bottom: 0.8rem; color: var(--secondary);">Load ${i}</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
            `;
            
            availableProducts.forEach(prod => {
                html += `
                    <label style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; background: white; padding: 0.5rem; border-radius: 4px; border: 1px solid #E5E7EB;">
                        <input type="checkbox" id="load_${i}_prod_${prod.id}" value="${prod.id}" style="width: 16px; height: 16px;">
                        <span style="font-size: 0.9rem;">${prod.name} (₱${prod.price})</span>
                    </label>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        loadsContainer.innerHTML = html;
    }

    function confirmServiceAddition() {
        if (!currentService) return;
        
        const weight = parseFloat(document.getElementById('modalWeight').value);
        if (isNaN(weight) || weight <= 0) {
            showError('Please enter a valid weight.');
            return;
        }

        // Add the primary service
        cart.push({
            type: 'Service',
            id: currentService.id,
            name: currentService.name,
            price: currentService.price,
            qty: weight,
            total: currentService.price * weight
        });

        // Add the selected products per load
        const numLoads = Math.ceil(weight / 7);
        for (let i = 1; i <= numLoads; i++) {
            availableProducts.forEach(prod => {
                const checkbox = document.getElementById(`load_${i}_prod_${prod.id}`);
                if (checkbox && checkbox.checked) {
                    cart.push({
                        type: 'Product',
                        id: prod.id,
                        name: `${prod.name} (Load ${i})`,
                        price: prod.price,
                        qty: 1,
                        total: prod.price
                    });
                }
            });
        }

        closeServiceModal();
        renderCart();
    }

    function confirmProductAddition() {
        if (!currentProduct) return;
        
        const qty = parseFloat(document.getElementById('productModalQty').value);
        if (isNaN(qty) || qty <= 0) {
            showError('Invalid quantity');
            return;
        }

        cart.push({
            type: 'Product',
            id: currentProduct.id,
            name: `${currentProduct.name} (Extra)`,
            price: currentProduct.price,
            qty: qty,
            total: currentProduct.price * qty
        });

        closeProductModal();
        renderCart();
    }

    function removeItem(index) {
        cart.splice(index, 1);
        renderCart();
    }

    function renderCart() {
        const orderItemsDiv = document.getElementById('orderItems');
        const listHTML = [];

        let grandTotal = 0;

        if (cart.length === 0) {
            orderItemsDiv.innerHTML = '<p id="emptyCart" class="text-muted text-center" style="margin-top: 50%;">Cart is empty</p>';
            updateTotals(0);
            return;
        }

        cart.forEach((item, index) => {
            grandTotal += item.total;
            listHTML.push(`
                <div style="display: flex; justify-content: space-between; align-items: center; background: white; padding: 0.5rem; border-radius: 4px; border: 1px solid #E5E7EB; margin-bottom: 0.5rem;">
                    <div>
                        <p style="font-size: 0.9rem; font-weight: 600;">${item.name}</p>
                        <p style="font-size: 0.8rem; color: #6B7280;">${item.qty} ${item.type === 'Service' ? 'kg' : 'x'} @ ₱${item.price}</p>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-weight: 600;">₱${item.total.toFixed(2)}</span>
                        <button type="button" onclick="removeItem(${index})" style="background: none; border: none; color: #EF4444; cursor: pointer; padding: 0.2rem;">×</button>
                    </div>
                </div>
            `);
        });

        orderItemsDiv.innerHTML = listHTML.join('');
        updateTotals(grandTotal);
    }

    function updateTotals(total) {
        document.getElementById('subtotalAmount').innerText = '₱' + total.toFixed(2);
        document.getElementById('totalAmount').innerText = '₱' + total.toFixed(2);
        document.getElementById('orderDataPayload').value = JSON.stringify(cart);
    }

    function submitOrder() {
        if (cart.length === 0) {
            showError('Cannot create an empty order!');
            return;
        }
        document.getElementById('posForm').submit();
    }
</script>
"""

# Completely replace the script blocks at the end of the file with the clean, non-duplicated block
content = re.sub(r'const availableProducts = \[.*?</script>', script_replacement, content, flags=re.DOTALL)

# Fix the trailing duplicate script tags if they still exist
content = re.sub(r'\s*document\.getElementById\(\'posForm\'\)\.submit\(\);\s*\}\s*</script>\s*$', '\n', content)

with open('c:/Users/Admin/Downloads/DjangoGroupProjectNew/templates/core/employee/pos.html', 'w', encoding='utf-8') as f:
    f.write(content)
